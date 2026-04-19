#!/usr/bin/env python3

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "bin" / "check_wrapper_contents.py"
CLASSIFIER = ROOT / "bin" / "classify_failure.py"
HANDLER = ROOT / "bin" / "handle_failure.py"
REPAIRER = ROOT / "bin" / "repair_failure.py"
RUNS_DIR = ROOT / "runs"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def run_python_json(script: Path, stdin_text=None, args=None):
    cmd = ["python3", str(script)]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    parsed = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    return result.returncode, result.stdout, result.stderr, parsed


def write_run_artifact(payload: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"{utc_timestamp()}.outcome.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def extract_counts(check_parsed: dict | None, handler_parsed: dict | None) -> dict:
    violations = check_parsed.get("violations", []) if isinstance(check_parsed, dict) else []
    return {
        "violation_count": len(violations),
        "blocking_count": handler_parsed.get("blocking_count", 0) if isinstance(handler_parsed, dict) else 0,
        "nonblocking_count": handler_parsed.get("nonblocking_count", 0) if isinstance(handler_parsed, dict) else 0,
        "unknown_count": handler_parsed.get("unknown_count", 0) if isinstance(handler_parsed, dict) else 0,
        "repair_action_count": handler_parsed.get("repair_action_count", 0) if isinstance(handler_parsed, dict) else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts_dir")
    args = parser.parse_args()

    artifacts_dir = str(Path(args.artifacts_dir).resolve())

    run_record = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_dir": artifacts_dir,
        "check_output": None,
        "classification_output": None,
        "handler_output": None,
        "repair_output": None,
        "recheck_output": None,
        "final_status": None,
        "final_decision": None,
        "repaired_any": False,
        "violation_count": 0,
        "blocking_count": 0,
        "nonblocking_count": 0,
        "unknown_count": 0,
        "repair_action_count": 0,
    }

    # --- 1. CHECK ---
    rc, out, err, parsed = run_python_json(
        CHECKER,
        args=["--artifacts", artifacts_dir],
    )

    run_record["check_output"] = {
        "returncode": rc,
        "stdout": out,
        "stderr": err,
        "parsed": parsed,
    }

    if parsed is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "checker_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "final_decision": "checker_unparseable",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    run_record["violation_count"] = len(parsed.get("violations", []))

    if parsed.get("status") == "pass":
        run_record["final_status"] = "complete"
        run_record["final_decision"] = "already_valid"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "complete",
            "final_decision": "already_valid",
            "violation_count": run_record["violation_count"],
            "blocking_count": run_record["blocking_count"],
            "nonblocking_count": run_record["nonblocking_count"],
            "unknown_count": run_record["unknown_count"],
            "repair_action_count": run_record["repair_action_count"],
            "run_artifact": str(artifact),
        }, indent=2))
        return 0

    # --- 2. CLASSIFY ---
    rc, out, err, parsed = run_python_json(
        CLASSIFIER,
        stdin_text=json.dumps(parsed),
    )

    run_record["classification_output"] = {
        "returncode": rc,
        "stdout": out,
        "stderr": err,
        "parsed": parsed,
    }

    if parsed is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "classifier_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "final_decision": "classifier_unparseable",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # --- 3. HANDLE (DECISION ONLY) ---
    rc, out, err, parsed = run_python_json(
        HANDLER,
        stdin_text=json.dumps(parsed),
    )

    run_record["handler_output"] = {
        "returncode": rc,
        "stdout": out,
        "stderr": err,
        "parsed": parsed,
    }

    if parsed is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "handler_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "final_decision": "handler_unparseable",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    counts = extract_counts(
        run_record["check_output"]["parsed"],
        run_record["handler_output"]["parsed"],
    )
    run_record.update(counts)

    decision = parsed.get("final_decision")
    run_record["final_decision"] = decision

    # --- HALT / ESCALATE ---
    if decision in {"halt", "escalate"}:
        run_record["final_status"] = "complete"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "complete",
            "final_decision": decision,
            "violation_count": run_record["violation_count"],
            "blocking_count": run_record["blocking_count"],
            "nonblocking_count": run_record["nonblocking_count"],
            "unknown_count": run_record["unknown_count"],
            "repair_action_count": run_record["repair_action_count"],
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # --- REPAIR REQUIRED ---
    if decision == "repair_required":
        repair_payload = {
            "status": "fail",
            "classifications": run_record["classification_output"]["parsed"]["classifications"],
        }

        rc, out, err, parsed = run_python_json(
            REPAIRER,
            stdin_text=json.dumps(repair_payload),
        )

        run_record["repair_output"] = {
            "returncode": rc,
            "stdout": out,
            "stderr": err,
            "parsed": parsed,
        }

        if parsed:
            run_record["repaired_any"] = parsed.get("repaired_any", False)

        # --- RE-CHECK ---
        rc, out, err, parsed = run_python_json(
            CHECKER,
            args=["--artifacts", artifacts_dir],
        )

        run_record["recheck_output"] = {
            "returncode": rc,
            "stdout": out,
            "stderr": err,
            "parsed": parsed,
        }

        if parsed is not None:
            run_record["violation_count"] = len(parsed.get("violations", []))

        if parsed and parsed.get("status") == "pass":
            run_record["final_status"] = "complete"
            run_record["final_decision"] = "recovered"
            artifact = write_run_artifact(run_record)
            print(json.dumps({
                "status": "complete",
                "final_decision": "recovered",
                "repaired_any": run_record["repaired_any"],
                "violation_count": run_record["violation_count"],
                "blocking_count": run_record["blocking_count"],
                "nonblocking_count": run_record["nonblocking_count"],
                "unknown_count": run_record["unknown_count"],
                "repair_action_count": run_record["repair_action_count"],
                "run_artifact": str(artifact),
            }, indent=2))
            return 0

        run_record["final_status"] = "complete"
        run_record["final_decision"] = "repair_failed"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "complete",
            "final_decision": "repair_failed",
            "repaired_any": run_record["repaired_any"],
            "violation_count": run_record["violation_count"],
            "blocking_count": run_record["blocking_count"],
            "nonblocking_count": run_record["nonblocking_count"],
            "unknown_count": run_record["unknown_count"],
            "repair_action_count": run_record["repair_action_count"],
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # --- FALLBACK ---
    run_record["final_status"] = "complete"
    run_record["final_decision"] = "no_repair_path"
    artifact = write_run_artifact(run_record)
    print(json.dumps({
        "status": "complete",
        "final_decision": "no_repair_path",
        "repaired_any": run_record["repaired_any"],
        "violation_count": run_record["violation_count"],
        "blocking_count": run_record["blocking_count"],
        "nonblocking_count": run_record["nonblocking_count"],
        "unknown_count": run_record["unknown_count"],
        "repair_action_count": run_record["repair_action_count"],
        "run_artifact": str(artifact),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
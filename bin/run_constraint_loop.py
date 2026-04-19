#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
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


def run_python_json(script: Path, stdin_text: str | None = None, args: list[str] | None = None) -> tuple[int, str, str, dict | None]:
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
    stdout_text = result.stdout.strip()

    if stdout_text:
        try:
            parsed = json.loads(stdout_text)
        except json.JSONDecodeError:
            parsed = None

    return result.returncode, result.stdout, result.stderr, parsed


def write_run_artifact(payload: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"{utc_timestamp()}.outcome.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts_dir", help="Path to artifacts directory to validate")
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
    }

    # 1. Check
    check_rc, check_stdout, check_stderr, check_json = run_python_json(
        CHECKER,
        args=["--artifacts", artifacts_dir],
    )

    run_record["check_output"] = {
        "returncode": check_rc,
        "stdout": check_stdout,
        "stderr": check_stderr,
        "parsed": check_json,
    }

    if check_json is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "checker_output_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "reason": "Checker output was not valid JSON",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    if check_json.get("status") == "pass":
        run_record["final_status"] = "complete"
        run_record["final_decision"] = "already_valid"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "complete",
            "final_decision": "already_valid",
            "repaired_any": False,
            "run_artifact": str(artifact),
        }, indent=2))
        return 0

    # 2. Classify
    classify_rc, classify_stdout, classify_stderr, classify_json = run_python_json(
        CLASSIFIER,
        stdin_text=json.dumps(check_json),
    )

    run_record["classification_output"] = {
        "returncode": classify_rc,
        "stdout": classify_stdout,
        "stderr": classify_stderr,
        "parsed": classify_json,
    }

    if classify_json is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "classifier_output_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "reason": "Classifier output was not valid JSON",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # 3. Handle
    handle_rc, handle_stdout, handle_stderr, handle_json = run_python_json(
        HANDLER,
        stdin_text=json.dumps(classify_json),
    )

    run_record["handler_output"] = {
        "returncode": handle_rc,
        "stdout": handle_stdout,
        "stderr": handle_stderr,
        "parsed": handle_json,
    }

    if handle_json is None:
        run_record["final_status"] = "error"
        run_record["final_decision"] = "handler_output_unparseable"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "error",
            "reason": "Handler output was not valid JSON",
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    final_decision = handle_json.get("final_decision")
    run_record["final_decision"] = final_decision

    # 4. Stop on halt/escalate
    if final_decision in {"halt", "escalate"}:
        run_record["final_status"] = "complete"
        artifact = write_run_artifact(run_record)
        print(json.dumps({
            "status": "complete",
            "final_decision": final_decision,
            "repaired_any": False,
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # 5. Optional repair path:
    # If the classifier found known deterministic failures, run repair_failure.py directly.
    classifications = classify_json.get("classifications", [])
    deterministic = [
        item for item in classifications
        if item.get("classification") == "known_deterministic"
    ]

    if deterministic:
        repair_payload = {
            "status": classify_json.get("status"),
            "classifications": deterministic,
        }

        repair_rc, repair_stdout, repair_stderr, repair_json = run_python_json(
            REPAIRER,
            stdin_text=json.dumps(repair_payload),
        )

        run_record["repair_output"] = {
            "returncode": repair_rc,
            "stdout": repair_stdout,
            "stderr": repair_stderr,
            "parsed": repair_json,
        }

        if repair_json is not None:
            run_record["repaired_any"] = repair_json.get("repaired_any", False)

        # 6. Re-check after repair attempt
        recheck_rc, recheck_stdout, recheck_stderr, recheck_json = run_python_json(
            CHECKER,
            args=["--artifacts", artifacts_dir],
        )

        run_record["recheck_output"] = {
            "returncode": recheck_rc,
            "stdout": recheck_stdout,
            "stderr": recheck_stderr,
            "parsed": recheck_json,
        }

        if recheck_json is not None and recheck_json.get("status") == "pass":
            run_record["final_status"] = "complete"
            run_record["final_decision"] = "recovered"
            artifact = write_run_artifact(run_record)
            print(json.dumps({
                "status": "complete",
                "final_decision": "recovered",
                "repaired_any": run_record["repaired_any"],
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
            "run_artifact": str(artifact),
        }, indent=2))
        return 1

    # 7. No deterministic repair path
    run_record["final_status"] = "complete"
    run_record["final_decision"] = "no_repair_path"
    artifact = write_run_artifact(run_record)
    print(json.dumps({
        "status": "complete",
        "final_decision": "no_repair_path",
        "repaired_any": False,
        "run_artifact": str(artifact),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from failure_codes import FailureCode


def repair_missing_player(wrapper: Path) -> bool:
    text = wrapper.read_text(encoding="utf-8", errors="ignore")

    if "<asciinema-player" in text:
        return False

    if "<broken-player" in text:
        updated = text.replace("<broken-player", "<asciinema-player", 1)
        wrapper.write_text(updated, encoding="utf-8")
        return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--wrapper", required=True)
    args = parser.parse_args()

    if not args.code.strip():
        print("missing failure code", file=sys.stderr)
        return 1

    try:
        code = FailureCode(args.code)
    except ValueError:
        print(f"invalid failure code: {args.code}", file=sys.stderr)
        return 1

    wrapper = Path(args.wrapper)

    if not wrapper.exists():
        print(f"wrapper does not exist: {wrapper}", file=sys.stderr)
        return 1

    match code:
        case FailureCode.WRAPPER_MISSING_PLAYER:
            changed = repair_missing_player(wrapper)
            if not changed:
                print("no repair performed", file=sys.stderr)
                return 1
            print(f"repaired {wrapper}")
            return 0

        case _:
            print(f"unhandled failure code: {code.value}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
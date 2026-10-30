"""CLI entry point for the dependency-aware job scheduler."""
from __future__ import annotations

import json
import re
import sys
from typing import Sequence

from scheduler_engine import build_schedule
from validator import SchedulerError, load_tasks


def parse_arguments(argv: Sequence[str]) -> tuple[str, int]:
    """Parse exactly --input PATH --workers W and report JSON on failures."""
    values: dict[str, str] = {}
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag not in ("--input", "--workers"):
            raise SchedulerError("INVALID_ARGUMENT", f"Unexpected argument {flag!r}.")
        if flag in values:
            raise SchedulerError("INVALID_ARGUMENT", f"Argument {flag!r} was supplied more than once.")
        if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
            raise SchedulerError("INVALID_ARGUMENT", f"Argument {flag!r} requires a value.")
        values[flag] = argv[index + 1]
        index += 2

    missing = [flag for flag in ("--input", "--workers") if flag not in values]
    if missing:
        raise SchedulerError(
            "INVALID_ARGUMENT",
            "Missing required argument(s): " + ", ".join(missing) + ".",
        )

    workers_text = values["--workers"]
    if re.fullmatch(r"[0-9]+", workers_text) is None:
        raise SchedulerError("INVALID_ARGUMENT", "Worker count must be an integer from 1 to 32.")
    workers = int(workers_text)
    if not 1 <= workers <= 32:
        raise SchedulerError("INVALID_ARGUMENT", "Worker count must be between 1 and 32.")

    return values["--input"], workers


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        input_path, workers = parse_arguments(argv)
        tasks = load_tasks(input_path)
        result = build_schedule(tasks, workers)
        exit_code = 0
    except SchedulerError as exc:
        result = exc.as_json()
        exit_code = 2
    except Exception as exc:  # defensive: keep stdout a single JSON document
        result = {
            "status": "error",
            "errors": [{
                "code": "INVALID_TASK",
                "message": f"Unable to build schedule: {exc}",
            }],
        }
        exit_code = 2

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

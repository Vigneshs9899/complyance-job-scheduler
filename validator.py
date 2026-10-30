"""CSV loading and validation for the dependency-aware job scheduler."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

ASCII_WS = " \t\n\r\v\f"
HEADER = ["task_id", "duration", "priority", "dependencies"]
TASK_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}\Z")
UNSIGNED_RE = re.compile(r"[0-9]+\Z")


class SchedulerError(Exception):
    """An expected input/validation error with a machine-readable code."""

    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra

    def as_json(self) -> dict[str, Any]:
        return {
            "status": "error",
            "errors": [{"code": self.code, "message": self.message, **self.extra}],
        }


def _trim(value: str) -> str:
    return value.strip(ASCII_WS)


def _valid_task_id(value: str) -> bool:
    return TASK_ID_RE.fullmatch(value) is not None


def _parse_unsigned(value: str, field: str, minimum: int, maximum: int,
                    task_id: str) -> int:
    if not UNSIGNED_RE.fullmatch(value):
        raise SchedulerError(
            "INVALID_TASK",
            f"Task {task_id!r} has an invalid {field}; expected an unsigned decimal integer.",
        )
    number = int(value)
    if not minimum <= number <= maximum:
        raise SchedulerError(
            "INVALID_TASK",
            f"Task {task_id!r} {field} must be between {minimum} and {maximum}.",
        )
    return number


def _find_cycle(tasks: dict[str, dict[str, Any]]) -> list[str] | None:
    """Return a real closed cycle path using iterative DFS (no recursion limit risk)."""
    color: dict[str, int] = {task_id: 0 for task_id in tasks}  # 0 white, 1 gray, 2 black
    path: list[str] = []
    path_index: dict[str, int] = {}

    for root in sorted(tasks):
        if color[root] != 0:
            continue
        color[root] = 1
        path_index[root] = 0
        path.append(root)
        stack: list[tuple[str, Any]] = [(root, iter(sorted(tasks[root]["dependencies"])))]

        while stack:
            node, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                stack.pop()
                color[node] = 2
                path.pop()
                path_index.pop(node, None)
                continue

            if color[neighbor] == 0:
                color[neighbor] = 1
                path_index[neighbor] = len(path)
                path.append(neighbor)
                stack.append((neighbor, iter(sorted(tasks[neighbor]["dependencies"]))))
            elif color[neighbor] == 1:
                return path[path_index[neighbor]:] + [neighbor]

    return None


def load_tasks(path: str | Path) -> dict[str, dict[str, Any]]:
    """Read and fully validate a scheduler CSV file."""
    try:
        handle = open(path, "r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise SchedulerError("READ_ERROR", f"Cannot read input file: {exc.strerror or exc}.") from exc

    with handle:
        try:
            reader = csv.reader(handle, strict=True)
            records = []
            for row in reader:
                if not row:  # physically blank line
                    continue
                trimmed = [_trim(field) for field in row]
                if len(trimmed) == 1 and trimmed[0] == "":
                    continue
                records.append((reader.line_num, trimmed))
        except (csv.Error, UnicodeDecodeError) as exc:
            raise SchedulerError("INVALID_CSV", f"Malformed CSV or invalid UTF-8 input: {exc}.") from exc
        except OSError as exc:
            raise SchedulerError("READ_ERROR", f"Cannot read input file: {exc.strerror or exc}.") from exc

    if not records:
        raise SchedulerError("INVALID_CSV", "The CSV file is missing the required header.")

    header_line, header = records[0]
    if header != HEADER:
        raise SchedulerError(
            "INVALID_CSV",
            "Header must contain exactly: task_id,duration,priority,dependencies in that order.",
        )

    data_records = records[1:]
    if len(data_records) > 2000:
        raise SchedulerError("INVALID_TASK", "The input cannot contain more than 2,000 tasks.")

    tasks: dict[str, dict[str, Any]] = {}
    for line_number, row in data_records:
        if len(row) != 4:
            raise SchedulerError(
                "INVALID_CSV",
                f"CSV record ending at line {line_number} has {len(row)} columns; expected 4.",
            )

        task_id, duration_text, priority_text, dependency_text = row
        if not _valid_task_id(task_id):
            raise SchedulerError(
                "INVALID_TASK",
                f"Invalid task ID {task_id!r} on CSV record ending at line {line_number}.",
            )
        if task_id in tasks:
            raise SchedulerError("DUPLICATE_TASK", f"Task ID {task_id!r} occurs more than once.")

        duration = _parse_unsigned(duration_text, "duration", 1, 1_000_000, task_id)
        priority = _parse_unsigned(priority_text, "priority", 0, 1_000, task_id)

        dependencies: list[str] = []
        if dependency_text != "":
            tokens = dependency_text.split(",")
            for raw_token in tokens:
                dependency = _trim(raw_token)
                if dependency == "":
                    raise SchedulerError(
                        "INVALID_DEPENDENCY",
                        f"Task {task_id!r} contains an empty dependency token.",
                    )
                if not _valid_task_id(dependency):
                    raise SchedulerError(
                        "INVALID_DEPENDENCY",
                        f"Task {task_id!r} has malformed dependency ID {dependency!r}.",
                    )
                if dependency == task_id:
                    raise SchedulerError(
                        "INVALID_DEPENDENCY",
                        f"Task {task_id!r} cannot depend on itself.",
                    )
                if dependency in dependencies:
                    raise SchedulerError(
                        "INVALID_DEPENDENCY",
                        f"Task {task_id!r} repeats dependency {dependency!r}.",
                    )
                dependencies.append(dependency)

        tasks[task_id] = {
            "task_id": task_id,
            "duration": duration,
            "priority": priority,
            "dependencies": dependencies,
        }

    # Validate references only after every task has been read, allowing forward references.
    for task_id, task in tasks.items():
        for dependency in task["dependencies"]:
            if dependency not in tasks:
                raise SchedulerError(
                    "INVALID_DEPENDENCY",
                    f"Task {task_id!r} depends on unknown task {dependency!r}.",
                )

    cycle = _find_cycle(tasks)
    if cycle:
        path_text = " -> ".join(cycle)
        raise SchedulerError(
            "CYCLE_DETECTED",
            f"Dependency cycle detected: {path_text}.",
            cycle=cycle,
        )

    return tasks

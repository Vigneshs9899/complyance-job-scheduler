"""Deterministic virtual-time scheduling engine."""
from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Any


def build_schedule(tasks: dict[str, dict[str, Any]], worker_count: int) -> dict[str, Any]:
    """Build a schedule using the exact priority and worker-allocation policy."""
    dependents: dict[str, list[str]] = defaultdict(list)
    remaining_dependencies: dict[str, int] = {}

    for task_id, task in tasks.items():
        remaining_dependencies[task_id] = len(task["dependencies"])
        for dependency in task["dependencies"]:
            dependents[dependency].append(task_id)

    # Ready queue: priority first, then ASCII task ID.
    ready: list[tuple[int, str]] = []
    for task_id, task in tasks.items():
        if remaining_dependencies[task_id] == 0:
            heapq.heappush(ready, (task["priority"], task_id))

    # Min-heap guarantees lowest-numbered idle worker is allocated first.
    idle_workers = list(range(1, worker_count + 1))
    heapq.heapify(idle_workers)

    # Running queue entries: (end_time, worker_id, task_id).
    running: list[tuple[int, int, str]] = []
    schedule: list[dict[str, int | str]] = []
    completed: set[str] = set()
    current_time = 0

    while len(completed) < len(tasks):
        # Start all work possible at this instant before advancing virtual time.
        while ready and idle_workers:
            _, task_id = heapq.heappop(ready)
            worker_id = heapq.heappop(idle_workers)
            start = current_time
            end = start + tasks[task_id]["duration"]
            schedule.append({
                "task_id": task_id,
                "worker_id": worker_id,
                "start": start,
                "end": end,
            })
            heapq.heappush(running, (end, worker_id, task_id))

        if not running:
            # A valid acyclic graph always has progress available or running.
            # Keep a defensive guard in case this function is called independently.
            raise ValueError("No schedulable tasks remain; dependency graph may contain a cycle.")

        current_time = running[0][0]

        # Finish EVERY task at this instant before releasing/starting any new work.
        finished_now: list[tuple[int, int, str]] = []
        while running and running[0][0] == current_time:
            finished_now.append(heapq.heappop(running))

        for _, worker_id, task_id in finished_now:
            completed.add(task_id)
            heapq.heappush(idle_workers, worker_id)

        # Release dependents only after all simultaneous completions have been processed.
        for _, _, finished_task_id in finished_now:
            for dependent_id in dependents[finished_task_id]:
                remaining_dependencies[dependent_id] -= 1
                if remaining_dependencies[dependent_id] == 0:
                    heapq.heappush(
                        ready,
                        (tasks[dependent_id]["priority"], dependent_id),
                    )

    schedule.sort(key=lambda entry: (entry["start"], entry["worker_id"]))
    makespan = max((entry["end"] for entry in schedule), default=0)

    return {
        "status": "ok",
        "workers": worker_count,
        "makespan": makespan,
        "schedule": schedule,
    }

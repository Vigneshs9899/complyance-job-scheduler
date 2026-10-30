import tempfile
import unittest
from pathlib import Path

from scheduler_engine import build_schedule
from validator import load_tasks


def tasks_from_csv(content):
    temp = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
    try:
        temp.write(content)
        temp.close()
        return load_tasks(temp.name)
    finally:
        Path(temp.name).unlink(missing_ok=True)


class SchedulerTests(unittest.TestCase):
    def test_brief_example(self):
        tasks = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "A,3,2,\nB,2,1,A\nC,4,1,\nD,1,2,\"B,C\"\n"
        )
        result = build_schedule(tasks, 2)
        self.assertEqual(result["makespan"], 6)
        self.assertEqual(result["schedule"], [
            {"task_id": "C", "worker_id": 1, "start": 0, "end": 4},
            {"task_id": "A", "worker_id": 2, "start": 0, "end": 3},
            {"task_id": "B", "worker_id": 2, "start": 3, "end": 5},
            {"task_id": "D", "worker_id": 1, "start": 5, "end": 6},
        ])

    def test_priority_then_ascii_id_and_input_order_independent(self):
        first = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "J2,1,1,\nJ10,1,1,\na,1,1,\nZ,1,0,\n"
        )
        second = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "Z,1,0,\na,1,1,\nJ10,1,1,\nJ2,1,1,\n"
        )
        expected = ["Z", "J10", "J2", "a"]
        self.assertEqual(
            [x["task_id"] for x in build_schedule(first, 1)["schedule"]], expected
        )
        self.assertEqual(
            [x["task_id"] for x in build_schedule(second, 1)["schedule"]], expected
        )

    def test_multiple_dependencies_and_simultaneous_completions(self):
        tasks = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "A,2,1,\nB,2,1,\nC,1,0,\"A,B\"\nD,1,0,A\n"
        )
        result = build_schedule(tasks, 2)
        by_id = {x["task_id"]: x for x in result["schedule"]}
        self.assertEqual((by_id["A"]["end"], by_id["B"]["end"]), (2, 2))
        self.assertEqual(by_id["C"]["start"], 2)
        self.assertEqual(by_id["D"]["start"], 2)
        self.assertEqual(result["makespan"], 3)

    def test_lowest_idle_worker_including_earlier_idle_worker(self):
        tasks = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "A,2,1,\nB,5,1,\nC,1,1,A\n"
        )
        result = build_schedule(tasks, 2)
        by_id = {x["task_id"]: x for x in result["schedule"]}
        # Worker 1 finishes A at t=2 while worker 2 is still busy with B.
        self.assertEqual(by_id["C"]["worker_id"], 1)
        self.assertEqual(by_id["C"]["start"], 2)

    def test_idle_jump_without_time_stepping(self):
        tasks = tasks_from_csv(
            "task_id,duration,priority,dependencies\n"
            "A,3,1,\nB,2,1,A\n"
        )
        result = build_schedule(tasks, 1)
        self.assertEqual(result["schedule"][1]["start"], 3)
        self.assertEqual(result["makespan"], 5)

    def test_empty_task_set(self):
        tasks = tasks_from_csv("task_id,duration,priority,dependencies\n")
        self.assertEqual(build_schedule(tasks, 2), {
            "status": "ok", "workers": 2, "makespan": 0, "schedule": []
        })

    def test_large_dependency_chain(self):
        rows = ["task_id,duration,priority,dependencies"]
        for index in range(250):
            dependency = "" if index == 0 else f"T{index - 1}"
            rows.append(f"T{index},1,1,{dependency}")
        result = build_schedule(tasks_from_csv("\n".join(rows) + "\n"), 8)
        self.assertEqual(len(result["schedule"]), 250)
        self.assertEqual(result["makespan"], 250)
        self.assertEqual(result["schedule"][-1]["end"], 250)


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validator import SchedulerError, load_tasks
from scheduler import parse_arguments


def load_content(content):
    temp = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
    try:
        temp.write(content)
        temp.close()
        return load_tasks(temp.name)
    finally:
        Path(temp.name).unlink(missing_ok=True)


class ValidatorTests(unittest.TestCase):
    def assert_code(self, code, content):
        with self.assertRaises(SchedulerError) as caught:
            load_content(content)
        self.assertEqual(caught.exception.code, code)
        self.assertTrue(caught.exception.message)

    def test_unknown_dependency(self):
        self.assert_code(
            "INVALID_DEPENDENCY",
            "task_id,duration,priority,dependencies\nA,1,1,MISSING\n",
        )

    def test_self_dependency(self):
        self.assert_code(
            "INVALID_DEPENDENCY",
            "task_id,duration,priority,dependencies\nA,1,1,A\n",
        )

    def test_repeated_dependency(self):
        self.assert_code(
            "INVALID_DEPENDENCY",
            'task_id,duration,priority,dependencies\nA,1,1,"B,B"\nB,1,1,\n',
        )

    def test_cycle_witness_is_closed_and_real_with_unrelated_task(self):
        with self.assertRaises(SchedulerError) as caught:
            load_content(
                "task_id,duration,priority,dependencies\n"
                "A,1,1,B\nB,1,1,C\nC,1,1,A\nFREE,1,1,\n"
            )
        error = caught.exception
        self.assertEqual(error.code, "CYCLE_DETECTED")
        cycle = error.extra["cycle"]
        self.assertEqual(cycle[0], cycle[-1])
        edges = {"A": {"B"}, "B": {"C"}, "C": {"A"}, "FREE": set()}
        for source, target in zip(cycle, cycle[1:]):
            self.assertIn(target, edges[source])

    def test_duplicate_id(self):
        self.assert_code(
            "DUPLICATE_TASK",
            "task_id,duration,priority,dependencies\nA,1,1,\nA,2,1,\n",
        )

    def test_bad_header_and_wrong_column_count(self):
        self.assert_code("INVALID_CSV", "task_id,priority,duration,dependencies\n")
        self.assert_code(
            "INVALID_CSV",
            "task_id,duration,priority,dependencies\nA,1,1\n",
        )

    def test_invalid_task_values(self):
        for row in ("1A,1,1,", "A,0,1,", "A,1000001,1,", "A,1,-1,", "A,1,1001,"):
            self.assert_code(
                "INVALID_TASK",
                "task_id,duration,priority,dependencies\n" + row + "\n",
            )

    def test_dependency_empty_token_and_bad_id(self):
        self.assert_code(
            "INVALID_DEPENDENCY",
            'task_id,duration,priority,dependencies\nA,1,1,"B,"\nB,1,1,\n',
        )
        self.assert_code(
            "INVALID_DEPENDENCY",
            "task_id,duration,priority,dependencies\nA,1,1,not.valid\n",
        )

    def test_bom_whitespace_blank_lines_and_forward_reference(self):
        tasks = load_content(
            '\ufeff task_id , duration , priority , dependencies \r\n'
            '\r\n B , 2 , 1 , A \r\n A , 1 , 2 , \r\n'
        )
        self.assertEqual(tasks["B"]["dependencies"], ["A"])


    def test_cli_emits_json_and_nonzero_for_invalid_input(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "bad.csv"
            csv_path.write_text(
                "task_id,duration,priority,dependencies\nA,0,1,\n",
                encoding="utf-8",
            )
            process = subprocess.run(
                [sys.executable, str(project_root / "scheduler.py"),
                 "--input", str(csv_path), "--workers", "2"],
                cwd=project_root, capture_output=True, text=True,
            )
        payload = json.loads(process.stdout)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(payload["status"], "error")
        self.assertNotIn("schedule", payload)
        self.assertEqual(payload["errors"][0]["code"], "INVALID_TASK")

    def test_cli_success_exit_and_json_output(self):
        project_root = Path(__file__).resolve().parents[1]
        process = subprocess.run(
            [sys.executable, str(project_root / "scheduler.py"),
             "--input", str(project_root / "inputs" / "basic.csv"), "--workers", "2"],
            cwd=project_root, capture_output=True, text=True,
        )
        payload = json.loads(process.stdout)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["makespan"], 6)

    def test_worker_count_arguments(self):
        self.assertEqual(parse_arguments(["--input", "x.csv", "--workers", "32"]),
                         ("x.csv", 32))
        for args in (
            [], ["--input", "x.csv"], ["--input", "x.csv", "--workers", "0"],
            ["--input", "x.csv", "--workers", "33"],
            ["--input", "x.csv", "--workers", "2.5"],
            ["--input", "x.csv", "--workers", "-1"],
        ):
            with self.assertRaises(SchedulerError) as caught:
                parse_arguments(args)
            self.assertEqual(caught.exception.code, "INVALID_ARGUMENT")


if __name__ == "__main__":
    unittest.main()

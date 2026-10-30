import json
import unittest
from pathlib import Path

from scheduler_engine import build_schedule
from validator import SchedulerError, load_tasks


ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "basic": 2,
    "simultaneous": 2,
    "idle-and-ties": 3,
    "empty": 2,
    "unknown-dependency": 2,
    "cycle": 2,
    "duplicate-id": 2,
}


class OfficialPublicCaseTests(unittest.TestCase):
    def test_all_official_public_cases(self):
        for case_name, worker_count in CASES.items():
            with self.subTest(case=case_name):
                expected = json.loads(
                    (ROOT / "expected" / f"{case_name}.json").read_text(encoding="utf-8")
                )
                try:
                    tasks = load_tasks(ROOT / "inputs" / f"{case_name}.csv")
                    actual = build_schedule(tasks, worker_count)
                except SchedulerError as exc:
                    actual = exc.as_json()

                self.assertEqual(actual["status"], expected["status"])
                if expected["status"] == "ok":
                    # Successful public outputs must match all required values and ordering.
                    self.assertEqual(actual, expected)
                else:
                    self.assertNotIn("schedule", actual)
                    self.assertEqual(
                        actual["errors"][0]["code"],
                        expected["errors"][0]["code"],
                    )
                    self.assertTrue(actual["errors"][0]["message"].strip())
                    if expected["errors"][0]["code"] == "CYCLE_DETECTED":
                        cycle = actual["errors"][0]["cycle"]
                        self.assertGreaterEqual(len(cycle), 2)
                        self.assertEqual(cycle[0], cycle[-1])


if __name__ == "__main__":
    unittest.main()

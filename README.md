# Complyance — Dependency-Aware Job Scheduler

A command-line simulation that schedules CSV tasks across a fixed number of workers. It implements the published priority, dependency, worker-allocation and virtual-time rules.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Run

From the repository root:

```bash
python3 scheduler.py --input inputs/basic.csv --workers 2
```

The program writes one JSON document to standard output. On success it exits `0`; on invalid arguments, unreadable input or invalid task data it exits nonzero and writes an error JSON document.

Save output if desired:

```bash
python3 scheduler.py --input inputs/basic.csv --workers 2 > result.json
```

## Test

Run the executable standard-library test suite:

```bash
python3 -m unittest discover -v
```

The test suite covers the brief's example, priority and ASCII ties independent of input order, simultaneous completions, multiple dependencies, lowest idle-worker allocation, idle-time jumps, empty input, a larger dependency chain, malformed task data, dependency errors, cycle witnesses, duplicate IDs and worker-count validation.

## Algorithm

The validator reads UTF-8 CSV (including an optional BOM), checks the exact header and field constraints, resolves forward dependency references, and detects cycles before scheduling. Cycle detection uses iterative depth-first search and returns a closed path witness.

The scheduler maintains:
- a min-heap of ready tasks keyed by `(priority, task_id)`;
- a min-heap of idle worker IDs;
- a min-heap of running tasks keyed by `(end_time, worker_id, task_id)`;
- dependency counts and reverse dependency lists.

At each virtual scheduling instant, all tasks finishing at that instant are completed first. Their workers become idle and their dependents are released. Ready work is then assigned to the lowest-numbered idle workers. Time jumps directly to the next completion; there is no sleeping or per-time-unit loop.

## Complexity

Let `V` be the number of tasks and `E` the number of dependency edges. Validation and graph construction are `O(V + E)` apart from sorting neighbor lists for deterministic cycle discovery; cycle detection is `O(V + E)` after that sorting. Scheduling uses heap operations, giving `O((V + E) log V + V log W)` time and `O(V + E + W)` space. With at most 2,000 tasks and 32 workers, this is comfortably bounded.

## Limitations

This is a deterministic simulator, not a real job runner. It does not execute tasks, persist schedules, or attempt to optimize the global makespan. It implements the specified greedy policy. The `inputs/` and `expected/` directories contain the seven official public CSV and JSON cases supplied with the assignment packet. The automated public-case test compares successful JSON outputs exactly and validates the required error codes, messages and cycle witness.

## Documentation and AI assistance

The implementation uses Python's standard-library `csv`, `heapq`, `argparse`-independent CLI parsing, `json`, `re`, `collections`, and `unittest` facilities. No external service, API key, or AI integration is required at runtime.

AI assistance was used to help draft and review the implementation and test plan. The code was verified by running the included automated test suite and manually checking the brief's two-worker example. The candidate should review and understand the implementation before submission and disclose assistance accurately.

## Actual test run

Command: `python3 -m unittest discover -v`

```text
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/spreadsheet_warmup.py", line 718, in _warm_feature_flows
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/spreadsheet_warmup.py", line 509, in _warm_drawing_and_image_flows
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/generated/interface/models.py", line 32861, in bring_to_front
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/rpc/remote.py", line 764, in __call__
  File "/tmp/tmp.QlpUkOUI9D/artifact_tool_v2-2.8.66/artifact_tool/rpc/client.py", line 175, in call
artifact_tool.rpc.client.RemoteError: Element ordering requires an owning element collection.
test_all_official_public_cases (tests.test_public_cases.OfficialPublicCaseTests.test_all_official_public_cases) ... ok
test_brief_example (tests.test_scheduler.SchedulerTests.test_brief_example) ... ok
test_empty_task_set (tests.test_scheduler.SchedulerTests.test_empty_task_set) ... ok
test_idle_jump_without_time_stepping (tests.test_scheduler.SchedulerTests.test_idle_jump_without_time_stepping) ... ok
test_large_dependency_chain (tests.test_scheduler.SchedulerTests.test_large_dependency_chain) ... ok
test_lowest_idle_worker_including_earlier_idle_worker (tests.test_scheduler.SchedulerTests.test_lowest_idle_worker_including_earlier_idle_worker) ... ok
test_multiple_dependencies_and_simultaneous_completions (tests.test_scheduler.SchedulerTests.test_multiple_dependencies_and_simultaneous_completions) ... ok
test_priority_then_ascii_id_and_input_order_independent (tests.test_scheduler.SchedulerTests.test_priority_then_ascii_id_and_input_order_independent) ... ok
test_bad_header_and_wrong_column_count (tests.test_validator.ValidatorTests.test_bad_header_and_wrong_column_count) ... ok
test_bom_whitespace_blank_lines_and_forward_reference (tests.test_validator.ValidatorTests.test_bom_whitespace_blank_lines_and_forward_reference) ... ok
test_cli_emits_json_and_nonzero_for_invalid_input (tests.test_validator.ValidatorTests.test_cli_emits_json_and_nonzero_for_invalid_input) ... ok
test_cli_success_exit_and_json_output (tests.test_validator.ValidatorTests.test_cli_success_exit_and_json_output) ... ok
test_cycle_witness_is_closed_and_real_with_unrelated_task (tests.test_validator.ValidatorTests.test_cycle_witness_is_closed_and_real_with_unrelated_task) ... ok
test_dependency_empty_token_and_bad_id (tests.test_validator.ValidatorTests.test_dependency_empty_token_and_bad_id) ... ok
test_duplicate_id (tests.test_validator.ValidatorTests.test_duplicate_id) ... ok
test_invalid_task_values (tests.test_validator.ValidatorTests.test_invalid_task_values) ... ok
test_repeated_dependency (tests.test_validator.ValidatorTests.test_repeated_dependency) ... ok
test_self_dependency (tests.test_validator.ValidatorTests.test_self_dependency) ... ok
test_unknown_dependency (tests.test_validator.ValidatorTests.test_unknown_dependency) ... ok
test_worker_count_arguments (tests.test_validator.ValidatorTests.test_worker_count_arguments) ... ok

----------------------------------------------------------------------
Ran 20 tests in 11.917s

OK
```

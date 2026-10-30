# Assignment 1 — Full Technical Specification

Contract version: 1.0. This reference records the requirements used for this implementation.

## 1. CLI
Accept `--input PATH --workers W`. Worker count is an integer from 1 to 32.
Write exactly one JSON document to stdout. Success exits 0; errors exit nonzero.
Diagnostics, if any, belong on stderr.

## 2. CSV
The exact header is `task_id,duration,priority,dependencies` in that order.
Input is UTF-8 with optional BOM; LF and CRLF are supported. Parse quoted CSV correctly.
Trim outer ASCII whitespace from headers and fields. Ignore blank lines and single-field
whitespace-only records. A row such as `,,,` is invalid, not blank.
Task IDs match `[A-Za-z][A-Za-z0-9_-]{0,31}` and are unique and case-sensitive.
Duration is an unsigned decimal integer from 1 to 1,000,000.
Priority is an unsigned decimal integer from 0 to 1,000; smaller is higher priority.
Leading zeroes are allowed; signs and fractions are not.
Dependencies are empty or comma-separated IDs. Trim tokens; forward references are valid.
Empty, malformed, repeated, self and unknown dependencies are invalid.
Reject cycles. Support at most 2,000 tasks. A header-only file is valid.

## 3. Scheduling
A task starts only when all dependencies have finished. Workers run one task at a time;
tasks are non-preemptive. At each instant:
1. Finish all tasks ending at that instant.
2. Release tasks whose dependencies are now all complete.
3. Sort the entire ready set by priority ascending, then ASCII task ID ascending.
4. Assign in that order to all idle workers in worker-ID ascending order.
5. If work remains, jump directly to the next running completion.
Do not idle while ready work exists. Do not let blocked high-priority tasks reserve workers.
This is the specified greedy policy, not global makespan optimization.

## 4. Success JSON
Return `status: "ok"`, `workers`, `makespan`, and `schedule`.
Each task appears exactly once with `task_id`, `worker_id`, `start`, and `end`.
Sort schedule by start ascending, then worker ID ascending. Makespan is maximum end,
or zero for an empty task set. Empty tasks return an empty schedule.

## 5. Error JSON
Return `status: "error"` and a nonempty `errors` array. Each error has `code` and `message`.
Codes: `INVALID_ARGUMENT`, `READ_ERROR`, `INVALID_CSV`, `INVALID_TASK`,
`DUPLICATE_TASK`, `INVALID_DEPENDENCY`, `CYCLE_DETECTED`.
Cycle errors include a real closed dependency path in `cycle`. Never include a partial
schedule in an error response.

## 6. Tests
Cover priority/ASCII ties independent of input order; multiple dependencies and simultaneous
completions; lowest idle-worker selection including earlier-idle workers; idle jumps;
unknown/self/repeated dependencies; cycles with unrelated tasks; invalid CSV/task values;
duplicate IDs and worker counts; empty tasks; and a meaningful larger dependency chain.

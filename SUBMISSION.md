# Assignment 1 — submission checklist

## Running the work

- Language/runtime and version: Python 3.10+ (verified with the local Python runtime used for the test run).
- Dependency installation command, if needed: None; standard library only.
- Exact scheduler command with `--input` and `--workers`: `python3 scheduler.py --input inputs/basic.csv --workers 2`
- Exact test command: `python3 -m unittest discover -v`
- Actual test results: 20 tests passed in the final local run; see `README.md` for the captured output.
- Data structures and approximate time/space complexity: Ready-task min-heap, idle-worker min-heap, running-task min-heap, dependency counts, reverse adjacency lists and completed set. Approximately `O((V + E) log V + V log W)` time and `O(V + E + W)` space.

## Scope and assistance

- Known limitations or unfinished work: Simulator only; it does not execute jobs or optimize globally. None known after running all seven official public CSV cases against their expected JSON files.
- Documentation or libraries used: Assignment brief and Specification v1.0; Python standard library.
- AI assistance used: AI helped draft and review the implementation and test plan. The candidate should personally review, understand, execute and verify all code before submission.

## Before submitting

- [ ] The repository includes implementation, executable tests and reproducible instructions.
- [ ] Standard output is one JSON document; errors exit nonzero without a partial schedule.
- [ ] The program runs locally without AI/LLM services, API keys or paid accounts.
- [ ] No credentials, customer data, dependency folders or build output are included.
- [ ] The repository is public and final work is on the default branch.
- [ ] I will leave submitted work unchanged; no corrections or resubmissions are accepted.

Submit this repository URL together with the separate public Assignment 2 repository URL through the form supplied in the recruiter email.

# AI Open SDLC Kit -- Agent Instructions

## Project Overview

This project uses Python with a manual build system (manual).

## Verified Commands

- **Build:** `python -m py_compile run.py src/osdlc/*.py`
- **Test:** `python -m pytest --cov=src/osdlc --cov-report=xml --cov-report=term-missing -v`
- **Lint:** `python -m py_compile run.py src/osdlc/*.py`

## Environment

Python 3.x. Install dependencies with `pip install pytest pytest-cov`.

## OpenCode Protocol

The agent MUST handle slash-commands found in issue or PR comments.

### Parsing

When opencode is triggered by a comment:
1. Read the comment body from the triggering event.
2. If the comment starts with `/oc` or `/opencode`, extract the first whitespace-delimited token immediately following the prefix.
3. The remainder of the comment (after the command token) is the **instruction payload**.
4. Route to the appropriate behaviour based on the command token.

### Commands

- **`/oc fix`** (Issue) - Apply a quick corrective change. Analyse the issue, create a throwaway fix branch from `main`, apply the fix, commit with `fix:`, and push. Do NOT create a PR. The payload may describe the fix intent.
- **`/oc analyze`** (Issue) - Read the issue body and all comments. Perform a critical analysis, then post a detailed functional requirement as a new issue comment. Include: problem statement, affected areas, acceptance criteria, and open questions. DO NOT create any branch, commit, or Pull Request.
- **`/oc plan`** (Issue) - Requires prior analyze. Read the analysed requirement, produce a technical implementation plan with file-level breakdown, and post it as a new issue comment. DO NOT create any branch, commit, or Pull Request.
- **`/oc implement`** (Issue) - Requires prior plan. Create branch `issue-{{number}}` from `main`. Implement file-by-file, commit each unit conventionally. Open a PR targeting `main` with `Closes #{{number}}`.
- **`/oc fixCheck`** (PR) - Read automated check results. For each failure, apply a fix, amend the PR branch, and re-trigger checks. Repeat up to 3 retries. Post a status comment when done.

### Instruction Payload

Any text after the command token is the instruction payload. The agent MAY use it for additional context:
- `/oc fix add null guard` -> command `fix`, payload `add null guard`
- `/oc analyze` -> command `analyze`, payload empty

### Model Overrides

The workflow sets the model based on keywords anywhere in the comment (case-insensitive):

- `GEMINI` -> `google/gemini-2.5-flash`
- `BIGPICKLE` -> `opencode/big-pickle`
- `NEMOTRON` -> `opencode/nemotron-3-super-free`
- (default) -> `opencode/deepseek-v4-flash-free`

## Commit Convention

Every commit MUST follow the Conventional Commits specification:
- `feat: ...` -- a new feature
- `fix: ...` -- a bug fix
- `chore: ...` -- maintenance, dependencies, tooling
- `BREAKING CHANGE: ...` or `feat!: ...` -- incompatible API changes

## Branch Naming

Feature branches MUST follow the pattern: `issue-{{number}}`
Always branch from `main`.

## Version Configuration

Version is stored in: `pyproject.toml`

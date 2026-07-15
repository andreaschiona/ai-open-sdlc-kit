OPENCODE_JSON = """\
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "AGENTS.md"
  ],
  "skills": {
    "paths": [".opencode/skills"]
  },
  "permission": {
    "bash": "allow"
  },
  "compaction": {
    "auto": true,
    "tail_turns": 10
  },
  "tool_output": {
    "max_lines": 150,
    "max_bytes": 6144
  },
  "provider": {
    "opencode": {
      "options": {
        "timeout": 300000,
        "chunkTimeout": 60000
      }
    }{provider_google}
  },
  "model": "{model}"
}
"""

AGENTS_MD = """\
# {project_name} -- Agent Instructions

## STOP -- Read This First

You are handling a `/oc` slash command. You MUST:
1. Parse the command from the triggering comment (analyze, plan, fix, implement, fixCheck).
2. Execute ONLY that command's behavior as defined below.
3. For `analyze` and `plan`: POST A COMMENT ONLY. Do NOT edit files, create branches, or PRs.
4. For `fix`: push a branch only. Do NOT create a PR.
5. For `implement`: this is the ONLY command that creates a PR.

If the command is `analyze` or `plan`, your job is DONE after posting one comment via `gh issue comment`.
DO NOT touch any source code files for analyze or plan commands.

## Project Overview

{language_description}

## Verified Commands

| Action | Command |
|--------|---------|
| Build  | `{build_cmd}` |
| Test   | `{test_cmd}` |
| Lint   | `{lint_cmd}` |

## Environment

{env_notes}

## OpenCode Protocol

The agent MUST handle slash-commands found in issue or PR comments.

### Parsing

When opencode is triggered by a comment:
1. Read the comment body from the triggering event.
2. If the comment starts with `/oc` or `/opencode`, extract the first whitespace-delimited token immediately following the prefix.
3. The remainder of the comment (after the command token) is the **instruction payload**.
4. Route to the appropriate behaviour based on the command token.

### Dispatch Table

| Command | Scope | Behaviour |
|---------|-------|-----------|
| `/oc fix` | Issue | Apply a quick corrective change. Analyse the issue, create a throwaway fix branch from `{default_branch}`, apply the fix, commit with `fix:` prefix, and push. Do NOT create a PR. The instruction payload may describe the fix intent. |
| `/oc analyze` | Issue | Read the issue body and all comments. Perform a critical analysis, then post a detailed functional requirement as a new issue comment. Include: problem statement, affected areas, acceptance criteria, and open questions. DO NOT create any branch, commit, or Pull Request. The instruction payload may scope the analysis. |
| `/oc plan` | Issue | (Requires prior analyze comment) Read the analysed functional requirement from the issue. Produce a technical implementation plan with file-level breakdown, and post it as a new issue comment. List each file to create or modify, the approach, and any dependencies. DO NOT create any branch, commit, or Pull Request. |
| `/oc implement` | Issue | (Requires prior plan comment) Create a feature branch named `issue-{{number}}` from `{default_branch}`. Implement the plan file-by-file, committing each logical unit with a conventional commit message. Open a Pull Request targeting `{default_branch}` that includes `Closes #{{number}}` in the description. |
| `/oc fixCheck` | PR | Read the PR's automated check results (lint errors, test failures). For each failure, apply a fix, amend the PR branch, and re-trigger checks. Repeat up to 3 retries. When done (all passing or retries exhausted), post a status comment on the PR. |

### CRITICAL RULES -- READ BEFORE ACTING

- **`/oc analyze` MUST ONLY post a comment.** NEVER create branches, commits, or PRs for analyze.
- **`/oc plan` MUST ONLY post a comment.** NEVER create branches, commits, or PRs for plan.
- **`/oc fix` MUST NOT create a PR.** Only push the fix branch.
- **`/oc implement` is the ONLY command that creates a PR.**
- If the command is `analyze`, your ENTIRE output is a GitHub issue comment. Nothing else.
- Execute EXACTLY ONE command per invocation. Do not chain or anticipate next steps.

### Instruction Payload

Any text after the command token is the instruction payload. The agent MAY use it for additional context:
- `/oc fix add null guard` → command `fix`, payload `add null guard`
- `/oc analyze` → command `analyze`, payload empty

### Model Overrides

The workflow sets the model based on keywords anywhere in the comment (case-insensitive):

| Keyword | Model |
|---------|-------|
| `GEMINI` | `google/gemini-2.5-flash` |
| `BIGPICKLE` | `opencode/big-pickle` |
| `NEMOTRON` | `opencode/nemotron-3-super-free` |
| (default) | `opencode/deepseek-v4-flash-free` |

## Commit Convention

Every commit MUST follow the Conventional Commits specification:
- `feat: ...` -- a new feature
- `fix: ...` -- a bug fix
- `chore: ...` -- maintenance, dependencies, tooling
- `BREAKING CHANGE: ...` or `feat!: ...` -- incompatible API changes

## Branch Naming

Feature branches MUST follow the pattern: `issue-{{number}}`
Always branch from `{default_branch}`.

## Version Configuration

Version is stored in: `{version_file}`
{architectural_notes}
"""

PACKAGE_JSON = """\
{
  "name": "opencode-skills",
  "private": true,
  "version": "0.0.0"
}
"""

DOT_GITIGNORE = """\
node_modules/
dist/
build/
.opencode/skills/*/node_modules/
"""

VERSION_MANAGEMENT_SKILL = """\
# Version Management Skill

## Workflow

Issue -> Branch -> Commit -> PR -> Merge -> Release

## Branching

- All feature branches MUST be created from `{default_branch}`.
- Branch name pattern: `issue-{{number}}`

## Commits

Every commit MUST be formatted according to the Conventional Commits specification:

| Type | Description |
|------|-------------|
| `feat` | A new feature (MINOR bump) |
| `fix` | A bug fix (PATCH bump) |
| `chore` | Maintenance, dependencies, tooling |
| `BREAKING CHANGE` | Incompatible API changes (MAJOR bump) |
| `!:` | Alternative syntax for breaking changes |

Examples:
- `feat: add user authentication endpoint`
- `fix: correct null pointer in login handler`
- `chore: update dependencies`
- `feat!: redesign API response format`

## Pull Requests

- PR title MUST start with a conventional commit type (e.g., `feat:`, `fix:`).
- PR description MUST include `Closes #{{number}}`.

## Version Properties

Version is tracked in: `{version_file}`
The version field MUST be updated by the release workflow according to the semver
bump determined from commit history since the last tag.
"""

ERROR_HANDLING_SKILL = """\
# Error Handling Skill

## Error Reporting

Every runtime error MUST be reported via the GitHubIssueReporter.

- Use `GitHubIssueReporter.reportError()` for all unhandled exceptions.
- No silent errors -- at minimum use `Log.e()` before reporting.
- The reporter MUST be initialised with a `GITHUB_TOKEN` that has `issues: write` scope.

## Issue Format

Every auto-reported issue MUST include:

- **Context**: environment, user action, relevant state
- **Error**: exception type, message, stack trace
- **Version**: current version of the application
- **Timestamp**: UTC timestamp of occurrence
- **Labels**: `bug`, `auto-reported`

## Labels

All auto-reported issues MUST include the labels: `bug`, `auto-reported`.

## Configuration

The `GITHUB_TOKEN` environment variable must be available at runtime with
`issues: write` permission for the repository.
"""

PLAN_SKILL = """\
# Plan Skill

## Purpose

This skill is activated when the `/oc plan` command is detected.

## RULES -- ABSOLUTE CONSTRAINTS

1. You MUST NOT create any branch.
2. You MUST NOT create any commit.
3. You MUST NOT create any Pull Request.
4. You MUST NOT modify any file in the repository.
5. Your ONLY action is to post a single comment on the current issue.

## Procedure

1. Read the issue title and body.
2. Read all existing comments on the issue, especially the functional requirement analysis.
3. Examine the codebase to understand affected areas.
4. Compose a detailed technical implementation plan with file-level breakdown.
5. Post it as a comment on the issue using `gh issue comment`.

## Output Format

Your comment MUST follow this structure:

```
## Technical Implementation Plan

### Overview
[Brief summary of the implementation approach]

### Files to Modify
- `path/to/file1`: [What changes are needed]
- `path/to/file2`: [What changes are needed]
- ...

### Implementation Steps
1. [Step 1 description]
2. [Step 2 description]
...

### Dependencies
[Any prerequisites or dependencies]

### Risk Assessment
[Potential risks and mitigation strategies]
```

## Verification

Before finishing, confirm:
- Did I create any branch? If yes, ABORT -- you violated the rules.
- Did I create any PR? If yes, ABORT -- you violated the rules.
- Did I post exactly one comment? If no, something went wrong.
"""

ANALYZE_SKILL = """\
# Analyze Skill

## Purpose

This skill is activated when the `/oc analyze` command is detected.

## RULES -- ABSOLUTE CONSTRAINTS

1. You MUST NOT create any branch.
2. You MUST NOT create any commit.
3. You MUST NOT create any Pull Request.
4. You MUST NOT modify any file in the repository.
5. Your ONLY action is to post a single comment on the current issue.

## Procedure

1. Read the issue title and body.
2. Read all existing comments on the issue.
3. Examine the codebase to understand affected areas.
4. Compose a detailed functional requirement analysis.
5. Post it as a comment on the issue using `gh issue comment`.

## Output Format

Your comment MUST follow this structure:

```
## Functional Requirement Analysis

### Problem Statement
[Clear description of what needs to be solved]

### Affected Areas
[List of files, modules, or components impacted]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- ...

### Open Questions
- [Any ambiguities or decisions needed]
```

## Verification

Before finishing, confirm:
- Did I create any branch? If yes, ABORT -- you violated the rules.
- Did I create any PR? If yes, ABORT -- you violated the rules.
- Did I post exactly one comment? If no, something went wrong.
"""

OPENCODE_WORKFLOW = """\
name: opencode

on:
  issue_comment:
    types: [created]
  pull_request_review:
    types: [submitted]
  workflow_run:
    workflows: ["PR Check"]
    types: [completed]

concurrency:
  group: opencode-${{ github.event_name }}-${{
    github.event.issue.number ||
    github.event.pull_request.number ||
    github.event.workflow_run.pull_requests[0].number ||
    github.event.reply_to_id }}-${{
    github.event_name == 'workflow_run' && 'auto' ||
    contains(github.event.comment.body, '/oc') && 'cmd' ||
    'other' }}
  cancel-in-progress: true

jobs:
  opencode:
    if: |
      github.event_name != 'workflow_run' &&
      github.event.comment != null &&
      github.event.comment.author_association == 'OWNER' &&
      (
        contains(github.event.comment.body, ' /oc') ||
        startsWith(github.event.comment.body, '/oc') ||
        contains(github.event.comment.body, ' /opencode') ||
        startsWith(github.event.comment.body, '/opencode')
      )
    runs-on: ubuntu-latest
    timeout-minutes: 180
    permissions:
      id-token: write
      contents: write
      pull-requests: write
      issues: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7
        with:
          persist-credentials: false
          fetch-depth: 0

      - name: Configure git for push
        shell: bash
        env:
          TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"
          git remote set-url origin "https://x-access-token:${TOKEN}@github.com/${{ github.repository }}"

      - name: Install jq
        shell: bash
        run: sudo apt-get update -qq && sudo apt-get install -y -qq jq

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.x'

      - name: Get opencode version
        id: version
        shell: bash
        run: |
          VERSION=$(curl -sf https://api.github.com/repos/anomalyco/opencode/releases/latest |
            grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4 || true)
          echo "version=${VERSION:-v1.15.10}" >> "$GITHUB_OUTPUT"

      - name: Cache opencode
        id: cache
        uses: actions/cache@v6
        with:
          path: ~/.opencode/bin
          key: opencode-${{ runner.os }}-${{ runner.arch }}-${{ steps.version.outputs.version }}

      - name: Install opencode
        if: steps.cache.outputs.cache-hit != 'true'
        shell: bash
        run: curl -fsSL https://opencode.ai/install | bash -s -- ${{ steps.version.outputs.version }}

      - name: Add opencode to PATH
        shell: bash
        run: echo "$HOME/.opencode/bin" >> "$GITHUB_PATH"

      - name: Determine model from comment
        id: model_select
        shell: bash
        env:
          COMMENT: ${{ github.event.comment.body }}
        run: |
          if echo "$COMMENT" | grep -qi "GEMINI"; then
            echo "model=google/gemini-2.5-flash" >> "$GITHUB_OUTPUT"
          elif echo "$COMMENT" | grep -qi "BIGPICKLE"; then
            echo "model=opencode/big-pickle" >> "$GITHUB_OUTPUT"
          elif echo "$COMMENT" | grep -qi "NEMOTRON"; then
            echo "model=opencode/nemotron-3-super-free" >> "$GITHUB_OUTPUT"
          else
            echo "model={model}" >> "$GITHUB_OUTPUT"
          fi

      - name: Run opencode (with retry)
        shell: bash
        id: run_opencode
        env:
          MODEL: ${{ steps.model_select.outputs.model }}
          OPENCODE_TELEMETRY: false
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          USE_GITHUB_TOKEN: "true"
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          echo "Selected model: $MODEL"

          jq --arg model "$MODEL" '.model = $model' opencode.json > opencode.tmp.json && mv opencode.tmp.json opencode.json
          echo "Injected model '$MODEL' into opencode.json"

          MAX_RETRIES=3
          RETRY_DELAY=15
          for i in $(seq 1 "$MAX_RETRIES"); do
            echo "opencode run attempt $i of $MAX_RETRIES"
            if opencode github run; then
              echo "opencode completed successfully"
              exit 0
            fi
            exit_code=$?
            echo "opencode exit code: $exit_code"
            if [ "$i" -eq "$MAX_RETRIES" ]; then
              echo "All $MAX_RETRIES attempts failed, last exit code: $exit_code"
              exit 1
            fi
            echo "Attempt $i failed (exit code: $exit_code), retrying in ${RETRY_DELAY}s..."
            sleep "$RETRY_DELAY"
          done

  auto-analyze-failure:
    if: |
      github.event_name == 'workflow_run' &&
      github.event.workflow_run.conclusion == 'failure' &&
      github.event.workflow_run.pull_requests[0] != null &&
      github.event.workflow_run.head_repository.fork == false
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
      pull-requests: write
      checks: read
    steps:
      - name: Checkout PR head
        uses: actions/checkout@v7
        with:
          ref: ${{ github.event.workflow_run.head_sha }}
          fetch-depth: 0
          persist-credentials: false

      - name: Get PR number
        id: pr
        shell: bash
        run: |
          {
            echo "number=${{ github.event.workflow_run.pull_requests[0].number }}"
            echo "head_branch=${{ github.event.workflow_run.head_branch }}"
            echo "head_sha=${{ github.event.workflow_run.head_sha }}"
          } >> "$GITHUB_OUTPUT"

      - name: Collect failure context
        shell: bash
        run: |
          mkdir -p /tmp/ci-context
          URL="/repos/${{ github.repository }}/commits/${{ github.event.workflow_run.head_sha }}/check-runs"
          gh api "$URL" --jq '
            .check_runs[] | select(.conclusion == "failure") |
            "## \(.name)\\n\\n**Title:** \(.output.title // "failed")\\n\\n**Summary:**\\n\(.output.summary // "N/A")\\n\\n**Text:**\\n\(.output.text // "N/A")\\n"
          ' > /tmp/ci-context/check-failures.md
          gh pr diff ${{ steps.pr.outputs.number }} > /tmp/ci-context/pr-diff.diff
          echo "Failure context collected ($(wc -l < /tmp/ci-context/check-failures.md) lines)"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Get opencode version
        id: version
        shell: bash
        run: |
          VERSION=$(curl -sf https://api.github.com/repos/anomalyco/opencode/releases/latest |
            grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4 || true)
          echo "version=${VERSION:-v1.15.10}" >> "$GITHUB_OUTPUT"

      - name: Cache opencode
        id: cache
        uses: actions/cache@v6
        with:
          path: ~/.opencode/bin
          key: opencode-auto-${{ runner.os }}-${{ runner.arch }}-${{ steps.version.outputs.version }}

      - name: Install opencode
        if: steps.cache.outputs.cache-hit != 'true'
        shell: bash
        run: curl -fsSL https://opencode.ai/install | bash -s -- ${{ steps.version.outputs.version }}

      - name: Add opencode to PATH
        shell: bash
        run: echo "$HOME/.opencode/bin" >> "$GITHUB_PATH"

      - name: Analyze failures with opencode
        shell: bash
        continue-on-error: true
        env:
          OPENCODE_TELEMETRY: false
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          opencode run --model {model} \
            --file /tmp/ci-context/check-failures.md \
            --file /tmp/ci-context/pr-diff.diff \
            "CI checks on this PR (#${{ steps.pr.outputs.number }}) have failed. \
            The attached files contain the failing check details and the PR diff. \
            Analyze the failures and propose specific fixes." \
            > /tmp/ci-context/analysis.md 2>&1

      - name: Post analysis to PR
        if: always() && steps.pr.outputs.number != ''
        shell: bash
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          {
            echo '## CI Failure Analysis'
            echo ''
            if [ -s /tmp/ci-context/analysis.md ]; then
              echo 'OpenCode has analyzed the check failures on this PR.'
              echo ''
              cat /tmp/ci-context/analysis.md
            else
              echo "The automatic analysis did not produce results."
              echo "To analyze manually, comment with /oc fixCheck on this PR."
            fi
          } > /tmp/ci-context/body.md
          gh pr comment ${{ steps.pr.outputs.number }} --body-file /tmp/ci-context/body.md
"""

PR_CHECK_WORKFLOW = """\
name: PR Check

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [{default_branch}]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

{language_setup}

      - name: Lint
        run: {lint_cmd}

      - name: Test
        run: {test_cmd}

      - name: Build
        run: {build_cmd}

      - name: Upload coverage artifact
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: coverage-report
          path: coverage.xml
          retention-days: 7

      - name: PR comment with results
        if: always() && github.event_name == 'pull_request'
        uses: actions/github-script@v9
        with:
          script: |
            const { data: checks } = await github.rest.checks.listForRef({
              ...context.repo,
              ref: context.sha,
            });
            const summary = checks.check_runs.map(c =>
              `- **${c.name}**: ${c.conclusion || 'in_progress'}`
            ).join('\\n');
            github.rest.issues.createComment({
              ...context.repo,
              issue_number: context.issue.number,
              body: `## PR Check Results\\n\\n${summary}\\n\\n_Updated at ${new Date().toISOString()}_`,
            });
"""

RELEASE_WORKFLOW = """\
name: Release

on:
  workflow_dispatch:
  push:
    branches: [{default_branch}]
    paths-ignore:
      - '**.md'
      - '.gitignore'

permissions:
  contents: write
  issues: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    outputs:
      new_version: ${{ steps.resolve.outputs.new_version }}
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

{language_setup}

      - name: Determine bump
        id: bump
        run: |
          LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
          if [ -z "$LAST_TAG" ]; then
            COMMITS=$(git log --format="%s")
          else
            COMMITS=$(git log "$LAST_TAG..HEAD" --format="%s")
          fi
          if echo "$COMMITS" | grep -q "BREAKING CHANGE"; then
            echo "BUMP_TYPE=major" >> "$GITHUB_ENV"
          elif echo "$COMMITS" | grep -q "^feat"; then
            echo "BUMP_TYPE=minor" >> "$GITHUB_ENV"
          else
            echo "BUMP_TYPE=patch" >> "$GITHUB_ENV"
          fi

      - name: Bump version
        id: version
        shell: bash
        run: |
          OUTPUT=$(python -m osdlc.version update --root . 2>&1)
          echo "update_output=$OUTPUT" >> "$GITHUB_OUTPUT"
          NEW_VERSION=$(echo "$OUTPUT" | sed -n 's/.*-> \\([0-9]\\+\\.[0-9]\\+\\.[0-9]\\+\\).*/\\1/p')
          echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
          echo "$OUTPUT"

      - name: Install dependencies
        run: pip install pytest

      - name: Lint
        run: {lint_cmd}

      - name: Run tests
        id: tests
        continue-on-error: true
        run: {test_cmd} || test $? -eq 5

      - name: Build
        run: {build_cmd}

      - name: Create issue on test failure
        if: steps.tests.outcome == 'failure'
        uses: actions/github-script@v9
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Release tests failed',
              body: 'Tests failed during release for version ${{ steps.version.outputs.new_version }}. Check the release workflow run for details.',
              labels: ['bug', 'auto-reported']
            })

      - name: Fail if tests failed
        if: steps.tests.outcome == 'failure'
        run: exit 1

      - name: Resolve tag collision
        id: resolve
        run: |
          NEW_VERSION="${{ steps.version.outputs.new_version }}"
          while git tag -l "v$NEW_VERSION" | grep -q .; do
            echo "Tag v$NEW_VERSION already exists — incrementing patch"
            IFS='.' read -r MAJOR MINOR PATCH <<< "$NEW_VERSION"
            PATCH=$((PATCH+1))
            NEW_VERSION="$MAJOR.$MINOR.$PATCH"
            python -m osdlc.version set "$NEW_VERSION" --root .
          done
          echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"

      - name: Commit version bump
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add "$(python -m osdlc.version detect --root . | cut -d' ' -f1)"
          git commit -m "chore: bump version to ${{ steps.resolve.outputs.new_version }} [skip ci]"
          git tag v${{ steps.resolve.outputs.new_version }}

      - name: Push changes
        run: |
          git push origin {default_branch}
          git push origin v${{ steps.resolve.outputs.new_version }}

      - name: Create Release
        uses: softprops/action-gh-release@v3
        with:
          tag_name: v${{ steps.resolve.outputs.new_version }}
          generate_release_notes: true
          make_latest: true

  publish:
    needs: release
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v7
        with:
          ref: v${{ needs.release.outputs.new_version }}
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.x'

      - name: Build wheel
        run: |
          pip install hatchling
          python -m hatchling build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
"""

CODEQL_WORKFLOW = """\
name: CodeQL

on:
  push:
    branches: [{default_branch}]
  pull_request:
    branches: [{default_branch}]
  schedule:
    - cron: '0 12 * * 1'

jobs:
  analyze:
    name: Analyze ({codeql_languages})
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    steps:
      - uses: actions/checkout@v7

      - uses: github/codeql-action/init@v4
        with:
          languages: {codeql_languages}

      - uses: github/codeql-action/autobuild@v4

      - uses: github/codeql-action/analyze@v4
"""

LINT_WORKFLOW = """\
name: Lint

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  super-linter:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - name: Super-Linter
        uses: super-linter/super-linter@v8.7.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VALIDATE_ALL_CODEBASE: false
          DEFAULT_BRANCH: {default_branch}
          VALIDATE_JAVA: {validate_java}
          VALIDATE_KOTLIN_KT_LINT: {validate_kotlin}
          VALIDATE_KOTLIN_BIOME: {validate_kotlin}
          VALIDATE_JAVASCRIPT_ES: {validate_javascript}
          VALIDATE_TYPESCRIPT_ES: {validate_typescript}
          VALIDATE_PYTHON: {validate_python}
          VALIDATE_GO: {validate_go}
          VALIDATE_RUST: {validate_rust}
          VALIDATE_RUBY: {validate_ruby}
          VALIDATE_PHP: {validate_php}
          VALIDATE_YAML: true
          VALIDATE_JSON: true
          VALIDATE_XML: true
          VALIDATE_MARKDOWN: true
          VALIDATE_GITHUB_ACTIONS: true
          VALIDATE_PROPERTIES: true
          FILTER_REGEX_EXCLUDE: \\.jks$|\\.jar$|\\.keystore$
"""

DEPENDABOT_YML = """\
version: 2
updates:
  - package-ecosystem: "{ecosystem}"
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore"
      prefix-development: "chore"
    labels:
      - "dependencies"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore"
    labels:
      - "dependencies"
"""


ALL_TEMPLATES = {
    "opencode.json": OPENCODE_JSON,
    "AGENTS.md": AGENTS_MD,
    ".opencode/package.json": PACKAGE_JSON,
    ".opencode/.gitignore": DOT_GITIGNORE,
    ".opencode/skills/version-management/SKILL.md": VERSION_MANAGEMENT_SKILL,
    ".opencode/skills/error-handling/SKILL.md": ERROR_HANDLING_SKILL,
    ".opencode/skills/analyze/SKILL.md": ANALYZE_SKILL,
    ".opencode/skills/plan/SKILL.md": PLAN_SKILL,
    ".github/workflows/opencode.yml": OPENCODE_WORKFLOW,
    ".github/workflows/pr-check.yml": PR_CHECK_WORKFLOW,
    ".github/workflows/release.yml": RELEASE_WORKFLOW,
    ".github/workflows/codeql.yml": CODEQL_WORKFLOW,
    ".github/workflows/lint.yml": LINT_WORKFLOW,
    ".github/dependabot.yml": DEPENDABOT_YML,
}

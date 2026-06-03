OPECODE_JSON = """\
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
| `/oc analyze` | Issue | Read the issue body and all comments. Perform a critical analysis, then post a detailed functional requirement as a new issue comment. Include: problem statement, affected areas, acceptance criteria, and open questions. The instruction payload may scope the analysis. |
| `/oc plan` | Issue | (Requires prior analyze comment) Read the analysed functional requirement from the issue. Produce a technical implementation plan with file-level breakdown, and post it as a new issue comment. List each file to create or modify, the approach, and any dependencies. |
| `/oc implement` | Issue | (Requires prior plan comment) Create a feature branch named `issue-{{number}}` from `{default_branch}`. Implement the plan file-by-file, committing each logical unit with a conventional commit message. Open a Pull Request targeting `{default_branch}` that includes `Closes #{{number}}` in the description. |
| `/oc fixCheck` | PR | Read the PR's automated check results (lint errors, test failures). For each failure, apply a fix, amend the PR branch, and re-trigger checks. Repeat up to 3 retries. When done (all passing or retries exhausted), post a status comment on the PR. |

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

OPECODE_WORKFLOW = """\
name: opencode

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

concurrency:
  group: ${{ github.event_name }}-${{ github.event.issue.number }}
  cancel-in-progress: true

jobs:
  opencode:
    if: >
      contains(github.event.comment.body, '/oc') ||
      contains(github.event.comment.body, '/opencode')
    runs-on: ubuntu-latest
    timeout-minutes: 180

    permissions:
      id-token: write
      contents: write
      pull-requests: write
      issues: write

    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: true
          fetch-depth: 0

      - name: Configure git identity
        run: |
          git config user.email "opencode@github.actions"
          git config user.name "opencode"

      - name: Install opencode
        run: |
          curl -fsSL https://opencode.ai/install | bash
          echo "$HOME/.opencode/bin" >> $GITHUB_PATH

      - name: Run opencode
        run: opencode github run
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MODEL: {model}
          USE_GITHUB_TOKEN: "true"
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
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

{language_setup}

      - name: Lint
        run: {lint_cmd}

      - name: Test
        run: {test_cmd}

      - name: Build
        run: {build_cmd}
"""

RELEASE_WORKFLOW = """\
name: Release

on:
  push:
    branches: [{default_branch}]
    paths-ignore:
      - '**.md'
      - '.gitignore'
      - 'LICENSE'
      - '.github/**'

permissions:
  contents: write
  issues: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
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
            echo "type=major" >> "$GITHUB_OUTPUT"
          elif echo "$COMMITS" | grep -q "^feat"; then
            echo "type=minor" >> "$GITHUB_OUTPUT"
          else
            echo "type=patch" >> "$GITHUB_OUTPUT"
          fi

      - name: Update version
        id: version
        run: |
          CURRENT=$(grep -oP '(?<=version=)[0-9]+[.][0-9]+[.][0-9]+' {version_file} || echo "0.0.0")
          IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
          case "${{ steps.bump.outputs.type }}" in
            major) MAJOR=$((MAJOR+1)); MINOR=0; PATCH=0 ;;
            minor) MINOR=$((MINOR+1)); PATCH=0 ;;
            patch) PATCH=$((PATCH+1)) ;;
          esac
          NEW_VERSION="$MAJOR.$MINOR.$PATCH"
          echo "new_version=$NEW_VERSION" >> "$GITHUB_OUTPUT"
          sed -i "s/version=$CURRENT/version=$NEW_VERSION/" {version_file}

      - name: Run tests
        id: tests
        continue-on-error: true
        run: {test_cmd}

      - name: Create issue on test failure
        if: steps.tests.outcome == 'failure'
        uses: actions/github-script@v7
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

      - name: Build artifact
        run: {build_cmd}

      - name: Commit version bump
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add {version_file}
          git commit -m "chore: bump version to ${{ steps.version.outputs.new_version }} [skip ci]"
          git tag v${{ steps.version.outputs.new_version }}

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: v${{ steps.version.outputs.new_version }}
          generate_release_notes: true
          make_latest: true

  publish:
    needs: release
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
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
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [{codeql_languages}]

    steps:
      - uses: actions/checkout@v4

      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - uses: github/codeql-action/autobuild@v3

      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
"""

LINT_WORKFLOW = """\
name: Lint

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  super-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Super-Linter
        uses: super-linter/super-linter@v7
        env:
          VALIDATE_ALL_CODEBASE: false
          DEFAULT_BRANCH: {default_branch}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VALIDATE_JAVA: {validate_java}
          VALIDATE_KOTLIN: {validate_kotlin}
          VALIDATE_JAVASCRIPT_ES: {validate_javascript}
          VALIDATE_TYPESCRIPT_ES: {validate_typescript}
          VALIDATE_PYTHON: {validate_python}
          VALIDATE_GO: {validate_go}
          VALIDATE_RUST: {validate_rust}
          VALIDATE_RUBY: {validate_ruby}
          VALIDATE_PHP: {validate_php}
          VALIDATE_YAML: true
          VALIDATE_JSON: true
          VALIDATE_XML: {validate_xml}
          VALIDATE_MARKDOWN: true
          VALIDATE_GITHUB_ACTIONS: true
          VALIDATE_PROPERTIES: {validate_properties}
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
    "opencode.json": OPECODE_JSON,
    "AGENTS.md": AGENTS_MD,
    ".opencode/package.json": PACKAGE_JSON,
    ".opencode/.gitignore": DOT_GITIGNORE,
    ".opencode/skills/version-management/SKILL.md": VERSION_MANAGEMENT_SKILL,
    ".opencode/skills/error-handling/SKILL.md": ERROR_HANDLING_SKILL,
    ".github/workflows/opencode.yml": OPECODE_WORKFLOW,
    ".github/workflows/pr-check.yml": PR_CHECK_WORKFLOW,
    ".github/workflows/release.yml": RELEASE_WORKFLOW,
    ".github/workflows/codeql.yml": CODEQL_WORKFLOW,
    ".github/workflows/lint.yml": LINT_WORKFLOW,
    ".github/dependabot.yml": DEPENDABOT_YML,
}

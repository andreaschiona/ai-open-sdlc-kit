# AI Open SDLC Kit

<p align="center">
  <img src="OSDLC%20Icon.png" alt="OSDLC Icon" width="120">
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+"></a>
  <a href="https://github.com/andreaschiona/ai-open-sdlc-kit/actions/workflows/pr-check.yml"><img src="https://github.com/andreaschiona/ai-open-sdlc-kit/actions/workflows/pr-check.yml/badge.svg" alt="PR Check"></a>
  <a href="https://github.com/andreaschiona/ai-open-sdlc-kit/actions/workflows/codeql.yml"><img src="https://github.com/andreaschiona/ai-open-sdlc-kit/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
  <a href="https://opencode.ai"><img src="https://img.shields.io/badge/agent-opencode-7B3FE4.svg" alt="OpenCode"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
</p>

CLI scaffolding tool that bootstraps any Git repository with an
opencode-native SDLC (Software Development Life Cycle) methodology.

The AI Open SDLC Kit generates a complete **agent-driven development workflow** --
including CI/CD pipelines, version management, error tracking, and a set of
opencode agents that respond to slash-commands on your GitHub issues and PRs.

---

## SDLC Methodology Overview

This kit implements a **cycle-based SDLC** orchestrated by opencode agents:

```
Issue (req)  →  /oc analyze  →  /oc plan  →  /oc implement  →  PR  →  Merge  →  Release
```

| Phase | Trigger | Description |
|-------|---------|-------------|
| **Requirements** | GitHub Issue | Feature request or bug report as a GitHub issue |
| **Analysis** | `/oc analyze` | Agent reads the issue and posts a structured functional requirement |
| **Planning** | `/oc plan` | Agent produces a file-level technical implementation plan |
| **Implementation** | `/oc implement` | Agent creates a branch, writes code, commits conventionally, and opens a PR |
| **Review** | Pull Request | PR checks (lint, test, build, CodeQL) run automatically |
| **Merge** | PR approval | Squash-merge to main |
| **Release** | Push to main | Version bump, git tag, and GitHub Release |

Quick fixes skip the analyze/plan steps:

| Trigger | Description |
|---------|-------------|
| `/oc fix` | Apply a quick corrective change directly from an issue |
| `/oc fixCheck` | Fix failing CI checks on a PR automatically |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Git
- [GitHub CLI](https://cli.github.com/) (`gh`)
- An opencode account at [opencode.ai](https://opencode.ai)

### 1. Run the kit init

```bash
python osdlc.py init
```

Interactive mode will prompt you for:

| Prompt | Default | Description |
|--------|---------|-------------|
| Project name | Directory name | Your project's display name |
| Default branch | `main` | Primary branch name |
| Version file | `VERSION` (auto-detected) | File to track version |
| Build command | Auto-detected | Command to build the project |
| Test command | Auto-detected | Command to run tests |
| Lint command | Auto-detected | Command to lint code |
| Language | Auto-detected | Programming language |
| Build system | Auto-detected | Package manager / build tool |
| Error-to-issue pipeline | No | Auto-report runtime errors as GitHub issues |
| Default model | `opencode/deepseek-v4-flash-free` | AI model for opencode agents |

### 2. Review the generated files

```bash
# Directory structure created by the kit:
.
├── opencode.json          # OpenCode agent configuration
├── AGENTS.md              # Agent instructions with /oc commands
├── .opencode/             # Skills (version management, error handling)
└── .github/
    ├── workflows/         # 5 CI/CD workflows
    └── dependabot.yml     # Automated dependency updates
```

### 3. Start the SDLC cycle

Create a GitHub issue for your feature or bug, then comment:

```
/oc analyze
```

The agent will analyze the issue and post a structured requirement. Continue
with `/oc plan` and `/oc implement` to close the cycle.

### Non-interactive mode

Skip prompts and use auto-detected defaults:

```bash
python osdlc.py init --non-interactive
```

### Force overwrite

Regenerate all files, overwriting existing ones:

```bash
python osdlc.py init --force
```

### Target a different directory

```bash
python osdlc.py init --target /path/to/project
```

---

## `/oc` Command Reference

Commands are triggered by commenting on a GitHub issue or PR. The comment must
start with `/oc` or `/opencode` followed by the command.

| Command | Scope | Behaviour |
|---------|-------|-----------|
| `/oc fix` | Issue | Apply a quick corrective change. Creates a throwaway fix branch from `main`, applies the fix, commits with `fix:`, pushes. Does **not** create a PR. |
| `/oc analyze` | Issue | Read the issue body and all comments. Posts a detailed functional requirement as a new comment: problem statement, affected areas, acceptance criteria, open questions. |
| `/oc plan` | Issue | (Requires prior analyze) Reads the analyzed requirement. Posts a technical implementation plan with file-level breakdown. |
| `/oc implement` | Issue | (Requires prior plan) Creates branch `issue-<number>`, implements file-by-file with conventional commits, opens a PR targeting `main` with `Closes #<number>`. |
| `/oc fixCheck` | PR | Reads automated check results. For each failure, applies a fix, amends the PR branch, re-triggers checks. Up to 3 retries. Posts a status comment when done. |

### Model Overrides

Append a keyword anywhere in your comment to switch the AI model:

| Keyword | Model |
|---------|-------|
| `GEMINI` | `google/gemini-2.5-flash` |
| `BIGPICKLE` | `opencode/big-pickle` |
| `NEMOTRON` | `opencode/nemotron-3-super-free` |
| (default) | `opencode/deepseek-v4-flash-free` |

Example: `/oc analyze GEMINI` uses Gemini for the analysis.

---

## Architecture / File Structure

### What the kit generates

```
<project-root>/
│
├── opencode.json                  # Agent config: model, permissions, providers
├── AGENTS.md                      # Agent instructions with /oc dispatch table
│
├── .opencode/
│   ├── package.json               # Skills package manifest
│   ├── .gitignore                 # Ignore rules for skills directory
│   └── skills/
│       ├── version-management/
│       │   └── SKILL.md           # Conventional commits, branching, versioning rules
│       └── error-handling/
│           └── SKILL.md           # Error-to-issue pipeline rules (optional)
│
└── .github/
    ├── dependabot.yml             # Weekly dependency updates
    └── workflows/
        ├── opencode.yml           # Agent orchestration (main entry point)
        ├── pr-check.yml           # Lint + test + build on every PR
        ├── release.yml            # Version bump + GitHub Release on push to main
        ├── codeql.yml             # CodeQL security analysis (weekly + PR)
        └── lint.yml               # Super-Linter on changed files
```

### Architecture overview

```
┌───────────────────────────────────────────────────────┐
│                   GitHub Repository                    │
│                                                       │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │
│  │  Issues   │   │    PRs   │   │  GitHub Actions  │  │
│  │  (reqs)   │   │ (review) │   │  (CI/CD)         │  │
│  └────┬─────┘   └────┬─────┘   └────────┬─────────┘  │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼──────────┐ │
│  │              opencode Agent                      │ │
│  │  (slash commands: /oc analyze, plan, implement)  │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                             │
│  ┌─────────────────────▼───────────────────────────┐ │
│  │           Skills (version, errors)              │ │
│  │  .opencode/skills/*/SKILL.md                    │ │
│  └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

---

## Configuration Guide

### `opencode.json`

The central configuration file generated by the kit:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["AGENTS.md"],
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
    }
  },
  "model": "opencode/deepseek-v4-flash-free"
}
```

### Key fields

| Field | Description |
|-------|-------------|
| `$schema` | JSON Schema URL for validation |
| `instructions` | Files containing agent instructions (AGENTS.md) |
| `skills.paths` | Directories containing skill definitions |
| `permission.bash` | Whether the agent can run shell commands (`allow` or `deny`) |
| `compaction.auto` | Auto-compact conversation context to manage token limits |
| `tool_output.max_lines` | Maximum lines of tool output shown to the agent |
| `provider.opencode` | Connection settings for the opencode API |
| `model` | Default AI model identifier |

### Providers

The kit supports multiple AI model providers. The `opencode` provider is always
configured. If you enable the error-to-issue pipeline, a `google` provider
section is added for Gemini models:

```json
"provider": {
  "opencode": {
    "options": {
      "timeout": 300000,
      "chunkTimeout": 60000
    }
  },
  "google": {
    "options": {
      "timeout": 300000,
      "chunkTimeout": 60000
    }
  }
}
```

### Model selection

The model is set in `opencode.json`:
- Default: `opencode/deepseek-v4-flash-free`
- Per-command override via comment keywords (GEMINI, BIGPICKLE, NEMOTRON)
- The opencode.yml workflow dynamically injects the model before each run

---

## CI/CD Pipeline

The kit generates five GitHub Actions workflows:

### 1. `opencode.yml` -- Agent orchestration

- **Triggers:** Issue comments, PR review comments, workflow run completion
- **What it does:**
  - Validates the comment author is the repository owner
  - Detects the `/oc` command and model override keywords
  - Installs opencode, runs it with the selected model
  - Retries up to 3 times on failure
  - **Auto-analyze job:** When a PR check fails, automatically collects failure
    context and posts an analysis comment on the PR

### 2. `pr-check.yml` -- PR quality gate

- **Triggers:** Every push to a PR targeting `main`
- **Checks:**
  - Lint (Python compile check)
  - Test (pytest with coverage)
  - Build (Python compile check)
- **Outputs:** Coverage artifact, PR comment with results

### 3. `release.yml` -- Versioned releases

- **Triggers:** Push to `main` (excluding docs, gitignore, workflow changes)
- **What it does:**
  - Determines semver bump (major/minor/patch) from conventional commits
  - Bumps the version in the detected version file
  - Runs lint, test, and build
  - Creates a git tag and GitHub Release
  - Creates an issue if tests fail during release

### 4. `codeql.yml` -- Security analysis

- **Triggers:** Push to main, PRs to main, weekly schedule (Mondays)
- **What it does:** Runs GitHub CodeQL analysis for security vulnerabilities

### 5. `lint.yml` -- Super-Linter

- **Triggers:** Every push to a PR (opened or updated)
- **What it does:** Runs [super-linter](https://github.com/super-linter/super-linter)
  with language-specific validators based on the detected project type

### `dependabot.yml` -- Dependency updates

- **Schedule:** Weekly on Mondays
- **Ecosystems:** Detected package manager + GitHub Actions
- **Limits:** 5 open PRs per ecosystem

---

## Language Detection

The kit auto-detects your project's build system by probing for known files
(checked in priority order):

| Probe file | Build system | Language |
|------------|-------------|----------|
| `pom.xml` | Maven | Java |
| `build.gradle.kts` | Gradle Kotlin | Kotlin/Java |
| `build.gradle` | Gradle | Java |
| `yarn.lock` | Yarn | JavaScript |
| `pnpm-lock.yaml` | pnpm | JavaScript |
| `package.json` | npm | JavaScript |
| `Cargo.toml` | Cargo | Rust |
| `pyproject.toml` | PEP 621 | Python |
| `setup.py` | setuptools | Python |
| `requirements.txt` | pip | Python |
| `go.mod` | Go modules | Go |
| `composer.json` | Composer | PHP |
| `Gemfile` | Bundler | Ruby |
| `CMakeLists.txt` | CMake | C/C++ |
| `mix.exs` | Mix | Elixir |

If no build system is detected, the kit falls back to file extension analysis
and prompts for manual configuration.

---

## Version Management

The kit includes a standalone version management module (`osdlc.version`) with
these subcommands:

| Command | Description |
|---------|-------------|
| `python -m osdlc.version detect` | Detect the version file in the project |
| `python -m osdlc.version get` | Read the current version |
| `python -m osdlc.version bump` | Determine semver bump from git log |
| `python -m osdlc.version set <ver>` | Write a new version to the version file |
| `python -m osdlc.version update` | Auto-detect, bump, and write new version |

Supported version file formats: `VERSION`, `pyproject.toml`, `package.json`,
`Cargo.toml`, `gradle.properties`, `version.py`, `version.go`, `composer.json`,
`CMakeLists.txt`, `mix.exs`.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b my-feature-branch`
3. Make your changes and commit using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: ...` for new features
   - `fix: ...` for bug fixes
   - `chore: ...` for maintenance
4. Run tests: `python -m pytest -v`
5. Run lint: `python -m py_compile osdlc.py src/osdlc/*.py`
6. Push your branch and open a Pull Request targeting `main`.
7. Ensure all PR checks pass before merge.

### Development setup

```bash
git clone https://github.com/andreaschiona/ai-open-sdlc-kit.git
cd ai-open-sdlc-kit
pip install pytest pytest-cov
python osdlc.py init --non-interactive --target /tmp/test-project
```

### Reporting issues

Open a GitHub issue with:
- A clear title and description
- Steps to reproduce (if bug)
- Expected vs actual behaviour
- Python version and OS

---

## License

MIT

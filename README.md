# AI Open SDLC Kit

Bootstraps any Git repository with a complete, AI-native SDLC methodology powered by [OpenCode](https://opencode.ai). No API keys required — works out of the box with free models via Open Zen.

## Why Open SDLC Kit?

Traditional CI/CD setups still rely on humans to write code, triage issues, review PRs, and fix broken builds. **Open SDLC Kit** replaces the human-in-the-loop with an OpenCode agent that handles the entire development lifecycle — from issue analysis to release — through simple `/oc` commands in GitHub comments.

The result is a **zero-cost, fully automated software lifecycle** where AI drives planning, implementation, verification, and release.

### Key Benefits

- **Zero-cost AI** — Default model is `opencode/deepseek-v4-flash-free` (Open Zen free tier). Optional Gemini fallback if `GEMINI_API_KEY` is set.
- **Agent-driven development** — One agent analyzes, plans, implements, and fixes code. Engage it with `/oc` in any issue or PR comment.
- **Conventional Commits** — Every commit follows `feat:`, `fix:`, `chore:`, `BREAKING CHANGE`. Version bumps are derived automatically.
- **Automatic CI/CD** — PRs trigger lint, test, build, and CodeQL checks. Merges to the default branch create GitHub Releases automatically.
- **Error-to-issue pipeline** (optional) — Wire a `GitHubIssueReporter` that auto-creates issues for runtime errors.

### What's New

- **Free, no-API-key AI** — Unlike GitHub Copilot or other tools that require paid subscriptions, this kit works with free models by default.
- **Full lifecycle automation** — Not just code completion. The agent analyzes issues, writes implementation plans, writes code, opens PRs, and fixes CI failures.
- **Model switching per command** — Include `GEMINI`, `BIGPICKLE`, or `NEMOTRON` in your comment to switch models on the fly.
- **Declarative scaffolding** — One `kit init` command generates the entire `.opencode/`, `.github/workflows/`, and configuration structure.

## Quick Start

```bash
# Run the interactive scaffolding tool in any Git repository
kit init
```

The tool will:
1. Detect your language/build system (Gradle, Maven, npm, pip, Cargo, Go, etc.)
2. Prompt for default branch, version config file, and build/test/lint commands
3. Ask whether to enable the error-to-issue pipeline
4. Generate every file needed for the agent-driven SDLC

After scaffolding, you'll see a summary of generated files and a quick-start note:

> Run `/oc analyze` on any issue to start the agent-driven SDLC cycle.

## Workflow: The `/oc` Protocol

OpenCode recognizes these slash-commands in issue and PR comments:

| Command | Scope | Behaviour |
|---|---|---|
| `/oc fix` | Issue | Analyzes the issue and applies a quick corrective change directly. Commits with `fix:`. |
| `/oc analyze` | Issue | Reads the issue body and comments, performs critical analysis, posts a functional requirement with problem statement, affected areas, acceptance criteria, and open questions. |
| `/oc plan` | Issue | (Requires prior `analyze`) Reads the analyzed requirement and produces a technical implementation plan with file-level breakdown, approach, and dependencies. |
| `/oc implement` | Issue | (Requires prior `plan`) Creates a feature branch from `main`, implements the plan file-by-file with conventional commits, and opens a Pull Request targeting `main` with `Closes #N`. |
| `/oc fixCheck` | PR | Reads PR check results, applies fixes for each failure, amends the PR branch, and re-triggers checks. Repeats up to a configurable retry limit. |

### Model Override Keywords

Append any of these tokens to your `/oc` command to select a different free model:

| Keyword | Model |
|---|---|
| *(default)* | `opencode/deepseek-v4-flash-free` |
| `GEMINI` | `google/gemini-2.5-flash` |
| `BIGPICKLE` | `opencode/big-pickle` |
| `NEMOTRON` | `opencode/nemotron-3-super-free` |

## Repository Structure

After running `kit init`, the following files are generated:

```
/
├── AGENTS.md                  # Project-specific agent instructions
├── opencode.json              # OpenCode configuration
├── .opencode/
│   ├── package.json
│   ├── .gitignore
│   └── skills/
│       ├── version-management/
│       │   └── SKILL.md
│       └── (optional) error-handling/
│           └── SKILL.md
└── .github/
    ├── dependabot.yml
    └── workflows/
        ├── opencode.yml       # Agent invocation on issue/PR comments
        ├── pr-check.yml       # Lint + test + build on every PR
        ├── release.yml        # Version bump + artifact + GitHub Release
        ├── codeql.yml         # Security analysis
        └── lint.yml           # Super-linter on changed files
```

## Generated Workflows

- **opencode.yml** — Triggered by issue/PR comments containing `/oc`. Checks out the repo, selects the model (from comment keywords), and runs `opencode github run` with up to 3 retries.
- **pr-check.yml** — Triggered on PRs to the default branch. Runs the linter, unit tests, and a debug build. Uploads test results and coverage as artifacts.
- **release.yml** — Triggered on push to the default branch. Parses commits since the last tag to determine the version bump (MAJOR for `BREAKING CHANGE`, MINOR for `feat`, else PATCH), increments the version, builds the release artifact, and creates a GitHub Release.
- **codeql.yml** — Standard CodeQL analysis on your project's language.
- **lint.yml** — Super-linter running on changed files (Kotlin/Java, YAML, JSON, XML, Markdown, Properties, GitHub Actions).
- **dependabot.yml** — Weekly dependency updates for your package ecosystem and GitHub Actions.

## Requirements

- Git repository (initialized)
- GitHub repository (for CI/CD workflows)
- No API key required (free Open Zen models work by default)

### Optional

- `GEMINI_API_KEY` — For Google Gemini fallback model
- `GITHUB_TOKEN` with `issues: write` — For error-to-issue pipeline

## Future Enhancements

- Plugin deployment (Firebase, AWS S3, Docker Hub) via release workflow
- Multi-language templates (Java, Kotlin, Python, Node.js, Rust, Go)
- Auto-merge for patch Dependabot updates
- Conventional commit lint hooks

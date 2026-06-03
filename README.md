# AI Open SDLC Kit

CLI scaffolding tool that bootstraps any Git repository with an
opencode-native SDLC methodology.

## Usage

```bash
python osdlc.py init
```

### Options

| Flag | Description |
| --- | ----------- |
| `--force`, `-f` | Overwrite existing files |
| `--target`, `-t` | Target directory (default: current directory) |
| `--non-interactive` | Skip interactive prompts (use detected defaults) |

### What it generates

| File | Description |
| --- | ----------- |
| `opencode.json` | OpenCode configuration |
| `AGENTS.md` | Agent instructions with project-specific commands |
| `.opencode/package.json` | Skills package manifest |
| `.opencode/.gitignore` | Skills directory ignore rules |
| `.opencode/skills/version-management/SKILL.md` | Version management workflow |
| `.opencode/skills/error-handling/SKILL.md` | Error-to-issue pipeline |
| `.github/workflows/opencode.yml` | Agent invocation on issue/PR comments |
| `.github/workflows/pr-check.yml` | Lint + test + build on every PR |
| `.github/workflows/release.yml` | Version bump on push to default branch |
| `.github/workflows/codeql.yml` | Security analysis |
| `.github/workflows/lint.yml` | Super-linter on changed files |
| `.github/dependabot.yml` | Automated dependency updates |

### Language detection

The kit automatically detects common build systems:

- `pom.xml` -- Maven (Java)
- `build.gradle.kts` -- Gradle Kotlin (Kotlin/Java)
- `build.gradle` -- Gradle (Java)
- `package.json` -- npm (JavaScript/TypeScript)
- `Cargo.toml` -- Cargo (Rust)
- `pyproject.toml` -- PEP 621 (Python)
- `go.mod` -- Go modules (Go)
- `composer.json` -- Composer (PHP)
- `Gemfile` -- Bundler (Ruby)
- `CMakeLists.txt` -- CMake (C/C++)
- `mix.exs` -- Mix (Elixir)

## Quick start

After running `osdlc init`, create a GitHub issue and comment with:

```bash
/oc analyze
```

This starts the agent-driven SDLC cycle.

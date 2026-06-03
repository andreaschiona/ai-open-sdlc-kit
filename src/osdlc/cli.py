import os
import sys
import argparse
from osdlc.detector import detect_project_type, suggest_language_by_extension
from osdlc.scaffold import scaffold


def prompt(prompt_text, default=None):
    if default is not None:
        user_input = input(f"{prompt_text} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt_text}: ").strip()


def confirm(prompt_text, default=True):
    default_str = "Y/n" if default else "y/N"
    user_input = input(f"{prompt_text} [{default_str}]: ").strip().lower()
    if not user_input:
        return default
    return user_input.startswith("y")


def print_banner():
    print("=" * 60)
    print("  AI Open SDLC Kit - Project Scaffolding")
    print("=" * 60)


def print_summary(generated, skipped, errors):
    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)

    if generated:
        print(f"\n  Generated ({len(generated)} files):")
        for f in generated:
            print(f"    + {f}")

    if skipped:
        print(f"\n  Skipped ({len(skipped)} files - already exist):")
        for f in skipped:
            print(f"    ~ {f}")
        print("\n  Use --force to overwrite existing files.")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for f, err in errors:
            print(f"    ! {f}: {err}")

    print()
    print("  Quick Start:")
    print("  -------------")
    print("  Run /oc analyze on any issue to start the agent-driven SDLC cycle.")
    print("  Create an issue and comment with '/oc analyze' to get started.")
    print()


def check_git_repo():
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="AI Open SDLC Kit - Bootstrap your repository with SDLC methodology"
    )
    parser.add_argument(
        "command", nargs="?", default="init",
        choices=["init"],
        help="Command to run (default: init)"
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "--target", "-t", default=".",
        help="Target directory (default: current directory)"
    )
    parser.add_argument(
        "--non-interactive", action="store_true",
        help="Skip interactive prompts (use defaults/detected values)"
    )

    args = parser.parse_args()

    if args.command != "init":
        print(f"Unknown command: {args.command}")
        return 1

    root = os.path.abspath(args.target)

    if not os.path.isdir(root):
        print(f"Error: target directory '{root}' does not exist.")
        return 1

    if not check_git_repo():
        print("Warning: Not inside a Git repository. Some features may not work.")
        print("Consider running 'git init' first.")

    print_banner()

    detected = detect_project_type(root)
    ext_lang = suggest_language_by_extension(root)

    if detected:
        print(f"\n  Detected: {detected['language']} ({detected['build_system']})")
    elif ext_lang:
        print(f"\n  Suggested language (by file extension): {ext_lang}")
    else:
        print("\n  No build system detected. You will be prompted for project details.")

    print()

    if args.non_interactive:
        if detected:
            config = detected.copy()
        else:
            config = {
                "build_system": "unknown",
                "language": ext_lang or "unknown",
                "version_file": "VERSION",
                "build_cmd": "echo 'no build command configured'",
                "test_cmd": "echo 'no test command configured'",
                "lint_cmd": "echo 'no lint command configured'",
                "probe": "manual",
            }
        config.setdefault("project_name", os.path.basename(root))
        config.setdefault("default_branch", "main")
        config.setdefault("error_to_issue", False)
        config.setdefault("provider_google", "")
        config.setdefault("model", "opencode/deepseek-v4-flash-free")
        config.setdefault("env_notes", "No special environment constraints.")
        config.setdefault("architectural_notes", "")
    else:
        config = {}

        template = detected or {}

        project_name = prompt("Project name", default=os.path.basename(root))
        config["project_name"] = project_name

        config["default_branch"] = prompt("Default branch name", default="main")

        version_file_default = template.get("version_file", "VERSION")
        config["version_file"] = prompt("Version config file path", default=version_file_default)

        config["build_cmd"] = prompt("Build command", default=template.get("build_cmd", "echo 'no build'"))
        config["test_cmd"] = prompt("Test command", default=template.get("test_cmd", "echo 'no tests'"))
        config["lint_cmd"] = prompt("Lint command", default=template.get("lint_cmd", "echo 'no linter'"))

        config["language"] = template.get("language", ext_lang or prompt("Language", default="unknown"))
        config["build_system"] = template.get("build_system", prompt("Build system", default="manual"))
        config["probe"] = template.get("probe", "manual")

        error_to_issue = confirm("Enable error-to-issue pipeline?", default=False)
        config["error_to_issue"] = error_to_issue

        if error_to_issue:
            config["github_token_env"] = prompt("GITHUB_TOKEN environment variable name", default="GITHUB_TOKEN")
            config["provider_google"] = '\n  },\n  "google": {\n    "options": {\n      "timeout": 300000,\n      "chunkTimeout": 60000\n    }\n  }'
        else:
            config["provider_google"] = ""

        config["model"] = prompt("Default model", default="opencode/deepseek-v4-flash-free")

        config["env_notes"] = prompt("Environment notes (optional)", default="No special environment constraints.")
        config["architectural_notes"] = prompt("Architectural notes (optional)", default="")

    print("Scaffolding project...")
    generated, skipped, errors = scaffold(config, root=root, force=args.force)

    print_summary(generated, skipped, errors)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

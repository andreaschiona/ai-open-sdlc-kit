import os
import sys
import argparse
from osdlc.detector import detect_project_type, suggest_language_by_extension
from osdlc.scaffold import scaffold, upgrade_scaffold
from osdlc.version import KIT_VERSION


def prompt(prompt_text, default=None):
    if default is not None:
        user_input = input(f"{prompt_text} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt_text}: ").strip()


def confirm(prompt_text, default=True):
    default_str = "Y/n" if default else "y/N"
    while True:
        user_input = input(f"{prompt_text} [{default_str}]: ").strip().lower()
        if not user_input:
            return default
        if user_input in ("y", "yes"):
            return True
        if user_input in ("n", "no"):
            return False
        print(f"  Please enter 'y'/'yes' or 'n'/'no'.")


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


def print_upgrade_summary(updated, skipped, conflicts, added, removed, errors, dry_run=False):
    label = " (dry run)" if dry_run else ""
    print()
    print("=" * 60)
    print(f"  Upgrade Summary{label}")
    print("=" * 60)

    if updated:
        print(f"\n  Updated ({len(updated)} files) - new template applied:")
        for f in updated:
            print(f"    * {f}")

    if skipped:
        print(f"\n  Skipped ({len(skipped)} files) - user modifications kept:")
        for f in skipped:
            print(f"    ~ {f}")

    if conflicts:
        print(f"\n  Conflicts ({len(conflicts)} files) - .new file created:")
        for f in conflicts:
            print(f"    ! {f}.new")
        print("\n  Review .new files and merge changes manually.")

    if added:
        print(f"\n  Added ({len(added)} files):")
        for f in added:
            print(f"    + {f}")

    if removed:
        print(f"\n  Removed from scaffold ({len(removed)} files) - preserved:")
        for f in removed:
            print(f"    - {f}")
        print("  These files are no longer generated but were kept as-is.")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for f, err in errors:
            print(f"    ! {f}: {err}")

    if not updated and not skipped and not conflicts and not added and not removed and not errors:
        print("\n  No changes detected.")

    print()


def check_git_repo(root="."):
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5,
            cwd=root
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
        choices=["init", "upgrade"],
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
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Show what would change without modifying files"
    )

    args = parser.parse_args()

    if args.command not in ("init", "upgrade"):
        print(f"Unknown command: {args.command}")
        return 1

    root = os.path.abspath(args.target)

    if not os.path.isdir(root):
        print(f"Error: target directory '{root}' does not exist.")
        return 1

    if not check_git_repo(root):
        print("Warning: Not inside a Git repository. Some features may not work.")
        print("Consider running 'git init' first.")

    if args.command == "upgrade":
        return run_upgrade(root, args)

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
            config["provider_google"] = ',\n    "google": {\n      "options": {\n        "timeout": 300000,\n        "chunkTimeout": 60000\n      }\n    }'
        else:
            config["provider_google"] = ""

        config["model"] = prompt("Default model", default="opencode/deepseek-v4-flash-free")

        config["env_notes"] = prompt("Environment notes (optional)", default="No special environment constraints.")
        config["architectural_notes"] = prompt("Architectural notes (optional)", default="")

    print("Scaffolding project...")
    generated, skipped, errors = scaffold(config, root=root, force=args.force)

    print_summary(generated, skipped, errors)

    return 0 if not errors else 1


def run_upgrade(root, args):
    detected = detect_project_type(root)
    ext_lang = suggest_language_by_extension(root)

    if not args.non_interactive:
        print("Interactive mode not supported for upgrade. Use --non-interactive flag.")
        return 1

    print("Running upgrade in non-interactive mode (using detected configuration).")

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

    from osdlc.scaffold import read_state
    state = read_state(root)
    if state is None:
        print("Error: Project was not scaffolded. Run 'osdlc init' first.")
        return 1

    old_version = state["kit_version"]
    print(f"\n  Upgrading from kit version {old_version} to {KIT_VERSION}")
    print()

    updated, skipped, conflicts, added, removed, errors = upgrade_scaffold(
        config, root=root, dry_run=args.dry_run
    )

    print_upgrade_summary(updated, skipped, conflicts, added, removed, errors, dry_run=args.dry_run)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

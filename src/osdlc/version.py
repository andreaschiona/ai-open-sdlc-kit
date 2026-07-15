import os
import re
import json
import subprocess
import sys

KIT_VERSION = "0.5.3"

VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")

VERSION_FILE_PROBES = [
    ("pyproject.toml", "pyproject_toml"),
    ("package.json", "package_json"),
    ("Cargo.toml", "cargo_toml"),
    ("gradle.properties", "gradle_properties"),
    ("version.py", "version_py"),
    ("version.go", "version_go"),
    ("VERSION", "version_txt"),
    ("composer.json", "composer_json"),
    ("CMakeLists.txt", "cmake"),
    ("mix.exs", "mix"),
]


def detect_version_file(root="."):
    for probe, fmt in VERSION_FILE_PROBES:
        path = os.path.join(root, probe)
        if os.path.exists(path):
            return path, fmt
    return None, None


def read_version(path, fmt):
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if fmt == "version_txt":
        m = re.search(r"^version\s*=\s*(\S+)", content, re.MULTILINE)
        if m:
            return m.group(1)
        m = VERSION_PATTERN.search(content)
        return m.group(0) if m else None
    elif fmt == "pyproject_toml":
        m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        return m.group(1) if m else None
    elif fmt in ("package_json", "composer_json"):
        data = json.loads(content)
        return data.get("version")
    elif fmt == "cargo_toml":
        m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        return m.group(1) if m else None
    elif fmt == "gradle_properties":
        m = re.search(r"^version\s*=\s*(\S+)", content, re.MULTILINE)
        return m.group(1) if m else None
    elif fmt == "version_py":
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not m:
            m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
        return m.group(1) if m else None
    elif fmt == "version_go":
        m = re.search(r'(?:var|const)\s+Version\s*=\s*"([^"]+)"', content)
        return m.group(1) if m else None
    elif fmt == "cmake":
        m = re.search(r"project\s*\(\s*\w+\s+VERSION\s+([0-9.]+)", content, re.IGNORECASE)
        return m.group(1) if m else None
    elif fmt == "mix":
        m = re.search(r'version:\s*"([^"]+)"', content)
        return m.group(1) if m else None
    return None


def write_version(path, fmt, new_version):
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if fmt == "version_txt":
        content_new = re.sub(
            r"^version\s*=\s*\S+",
            f"version={new_version}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if content_new == content:
            content_new = re.sub(
                VERSION_PATTERN, new_version, content, count=1
            )
    elif fmt == "pyproject_toml":
        content_new = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            count=1,
            flags=re.MULTILINE,
        )
    elif fmt == "package_json":
        data = json.loads(content)
        data["version"] = new_version
        content_new = json.dumps(data, indent=2) + "\n"
    elif fmt == "cargo_toml":
        content_new = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            content,
            count=1,
            flags=re.MULTILINE,
        )
    elif fmt == "gradle_properties":
        content_new = re.sub(
            r"^version\s*=\s*\S+",
            f"version={new_version}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
    elif fmt == "version_py":
        content_new = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content,
            count=1,
        )
        if content_new == content:
            content_new = re.sub(
                r'VERSION\s*=\s*["\'][^"\']+["\']',
                f'VERSION = "{new_version}"',
                content,
                count=1,
            )
    elif fmt == "version_go":
        content_new = re.sub(
            r'(var|const)\s+Version\s*=\s*"[^"]+"',
            f'\\1 Version = "{new_version}"',
            content,
            count=1,
        )
    elif fmt == "cmake":
        content_new = re.sub(
            r"(project\s*\(\s*\w+\s+VERSION\s+)\S+",
            f"\\g<1>{new_version}",
            content,
            count=1,
            flags=re.IGNORECASE,
        )
    elif fmt == "composer_json":
        data = json.loads(content)
        data["version"] = new_version
        content_new = json.dumps(data, indent=2) + "\n"
    elif fmt == "mix":
        content_new = re.sub(
            r'version:\s*"[^"]+"',
            f'version: "{new_version}"',
            content,
            count=1,
        )
    else:
        raise ValueError(f"Unknown format: {fmt}")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content_new)


def get_last_tag():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            return tag if tag else None
        return None
    except Exception:
        return None


def get_commits_since(tag=None):
    try:
        if tag:
            result = subprocess.run(
                ["git", "log", f"{tag}..HEAD", "--format=%s"],
                capture_output=True, text=True, timeout=10,
            )
        else:
            result = subprocess.run(
                ["git", "log", "--format=%s"],
                capture_output=True, text=True, timeout=10,
            )
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            return [l.strip() for l in lines if l.strip()]
        return []
    except Exception:
        return []


def determine_bump_type(commits):
    has_feat = False
    for msg in commits:
        if "BREAKING CHANGE" in msg or msg.startswith("feat!") or msg.startswith("fix!"):
            return "major"
        if msg.startswith("feat"):
            has_feat = True
    if has_feat:
        return "minor"
    return "patch"


def bump_version(current_version, bump_type):
    m = VERSION_PATTERN.match(current_version)
    if not m:
        raise ValueError(f"Cannot parse version: {current_version}")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")
    return f"{major}.{minor}.{patch}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Version management tool")
    sub = parser.add_subparsers(dest="command")

    p_detect = sub.add_parser("detect", help="Detect version file in root")
    p_detect.add_argument("--root", default=".")

    p_get = sub.add_parser("get", help="Read current version")
    p_get.add_argument("--root", default=".")

    p_bump = sub.add_parser("bump", help="Determine bump type from git log")
    p_bump.add_argument("--root", default=".")

    p_set = sub.add_parser("set", help="Set new version in version file")
    p_set.add_argument("version", help="New version string")
    p_set.add_argument("--root", default=".")

    p_update = sub.add_parser("update", help="Auto-detect, bump, and set version")
    p_update.add_argument("--root", default=".")

    args = parser.parse_args()

    if args.command == "detect":
        path, fmt = detect_version_file(args.root)
        if path:
            print(f"{path} {fmt}")
        else:
            print("none none")
        return 0

    if args.command == "get":
        path, fmt = detect_version_file(args.root)
        if not path:
            print("No version file detected")
            return 1
        ver = read_version(path, fmt)
        if ver:
            print(ver)
        else:
            print("Could not read version")
            return 1
        return 0

    if args.command == "bump":
        tag = get_last_tag()
        commits = get_commits_since(tag)
        bump = determine_bump_type(commits)
        print(bump)
        return 0

    if args.command == "set":
        path, fmt = detect_version_file(args.root)
        if not path:
            print("No version file detected")
            return 1
        write_version(path, fmt, args.version)
        print(f"Updated {path} to {args.version}")
        return 0

    if args.command == "update":
        path, fmt = detect_version_file(args.root)
        if not path:
            print("No version file detected")
            return 1
        current = read_version(path, fmt)
        if not current:
            print("Could not read current version")
            return 1
        tag = get_last_tag()
        commits = get_commits_since(tag)
        bump = determine_bump_type(commits)
        new_version = bump_version(current, bump)
        write_version(path, fmt, new_version)
        print(f"{current} -> {new_version} ({bump})")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

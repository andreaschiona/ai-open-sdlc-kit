import os
import json
import hashlib
from osdlc.templates import ALL_TEMPLATES
from osdlc.version import KIT_VERSION

OSDLC_STATE_FILE = ".osdlc-state.json"

TEMPLATE_FILES_TO_SKIP = {OSDLC_STATE_FILE}


def calculate_checksum(content):
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def read_state(root):
    state_path = os.path.join(root, OSDLC_STATE_FILE)
    if not os.path.exists(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_state(root, kit_version, file_checksums):
    state_path = os.path.join(root, OSDLC_STATE_FILE)
    state = {
        "kit_version": kit_version,
        "files": file_checksums,
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def detect_codeql_languages(language):
    mapping = {
        "Java": "java-kotlin",
        "Kotlin": "java-kotlin",
        "Kotlin/Java": "java-kotlin",
        "JavaScript": "javascript-typescript",
        "TypeScript": "javascript-typescript",
        "Python": "python",
        "Rust": "rust",
        "Go": "go",
        "Ruby": "ruby",
        "PHP": "python",
        "C/C++": "cpp",
        "C#": "csharp",
        "Swift": "swift",
        "Elixir": "python",
    }
    return mapping.get(language, "python")


def detect_ecosystem(build_system):
    mapping = {
        "Maven": "maven",
        "Gradle Kotlin": "gradle",
        "Gradle": "gradle",
        "npm": "npm",
        "Yarn": "npm",
        "pnpm": "npm",
        "Cargo": "cargo",
        "PEP 621": "pip",
        "setuptools": "pip",
        "pip": "pip",
        "Go modules": "go_mod",
        "Composer": "composer",
        "Bundler": "bundler",
        "CMake": "cmake",
        "Mix": "mix",
    }
    return mapping.get(build_system, "pip")


def detect_language_setup_step(language):
    mapping = {
        "Java": """\
      - name: Set up JDK 17
        uses: actions/setup-java@v5
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3""",
        "Kotlin/Java": """\
      - name: Set up JDK 17
        uses: actions/setup-java@v5
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3""",
        "JavaScript": """\
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 'latest'

      - name: Install dependencies
        run: npm ci""",
        "Python": """\
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: pip install .""",
        "Rust": """\
      - name: Setup Rust
        uses: dtolnay/action-rust-toolchain@stable""",
        "Go": """\
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: 'stable'""",
        "Ruby": """\
      - name: Setup Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.x'
          bundler-cache: true""",
        "PHP": """\
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'""",
        "C/C++": """\
      - name: Setup CMake
        uses: lukka/get-cmake@latest""",
        "Elixir": """\
      - name: Setup Elixir
        uses: erlef/setup-beam@v1
        with:
          elixir-version: 'latest'
          otp-version: 'latest'""",
    }
    return mapping.get(language, "")


def build_template_vars(config):
    language = config["language"]
    build_system = config["build_system"]
    codeql_lang = detect_codeql_languages(language)
    ecosystem = detect_ecosystem(build_system)
    lang_setup = detect_language_setup_step(language)

    l = language.lower()
    validate_java = "true" if l in ("java", "kotlin", "kotlin/java") else "false"
    validate_kotlin = "true" if l in ("kotlin", "kotlin/java") else "false"
    validate_javascript = "true" if l in ("javascript", "typescript", "react", "react typescript") else "false"
    validate_typescript = "true" if l in ("typescript", "react typescript") else "false"
    validate_python = "true" if l == "python" else "false"
    validate_go = "true" if l == "go" else "false"
    validate_rust = "true" if l == "rust" else "false"
    validate_ruby = "true" if l == "ruby" else "false"
    validate_php = "true" if l == "php" else "false"
    validate_xml = "true" if l in ("java", "kotlin", "kotlin/java") else "false"
    validate_properties = "true" if l in ("java", "kotlin", "kotlin/java") else "false"

    return {
        "project_name": config.get("project_name", "my-project"),
        "default_branch": config["default_branch"],
        "version_file": config["version_file"],
        "build_cmd": config["build_cmd"],
        "test_cmd": config["test_cmd"],
        "lint_cmd": config["lint_cmd"],
        "language_description": f"This project uses {language} with the {build_system} build system ({config['probe']}).",
        "env_notes": config.get("env_notes", "No special environment constraints."),
        "architectural_notes": config.get("architectural_notes", ""),
        "model": config.get("model", "opencode/deepseek-v4-flash-free"),
        "provider_google": config.get("provider_google", ""),
        "codeql_languages": repr(codeql_lang),
        "ecosystem": ecosystem,
        "language_setup": lang_setup,
        "validate_java": validate_java,
        "validate_kotlin": validate_kotlin,
        "validate_javascript": validate_javascript,
        "validate_typescript": validate_typescript,
        "validate_python": validate_python,
        "validate_go": validate_go,
        "validate_rust": validate_rust,
        "validate_ruby": validate_ruby,
        "validate_php": validate_php,
        "validate_xml": validate_xml,
        "validate_properties": validate_properties,
    }


def render_template(template, vars_dict):
    result = template
    for key, value in vars_dict.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value))
    return result


def scaffold(config, root=".", force=False):
    vars_dict = build_template_vars(config)
    generated = []
    skipped = []
    errors = []

    templates = dict(ALL_TEMPLATES)
    if not config.get("error_to_issue"):
        templates.pop(".opencode/skills/error-handling/SKILL.md", None)

    for key in TEMPLATE_FILES_TO_SKIP:
        templates.pop(key, None)

    dirs_to_create = set()
    for filepath in templates:
        full_path = os.path.join(root, filepath)
        parent = os.path.dirname(full_path)
        if parent:
            dirs_to_create.add(parent)

    for d in sorted(dirs_to_create):
        os.makedirs(d, exist_ok=True)

    for filepath, template in templates.items():
        full_path = os.path.join(root, filepath)

        if os.path.exists(full_path) and not force:
            skipped.append(filepath)
            continue

        try:
            content = render_template(template, vars_dict)
            with open(full_path, "w", newline="\n", encoding="utf-8") as f:
                f.write(content)
            generated.append(filepath)
        except Exception as e:
            errors.append((filepath, str(e)))

    checksums = {}
    for filepath in templates:
        full_path = os.path.join(root, filepath)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                checksums[filepath] = calculate_checksum(f.read())
    write_state(root, KIT_VERSION, checksums)

    return generated, skipped, errors


def upgrade_scaffold(config, root=".", dry_run=False):
    vars_dict = build_template_vars(config)
    updated = []
    skipped = []
    conflicts = []
    added = []
    removed = []
    errors = []

    state = read_state(root)
    if state is None:
        return updated, skipped, conflicts, added, removed, [
            ("<project>", "Project was not scaffolded. Run 'osdlc init' first.")
        ]

    old_version = state["kit_version"]
    old_checksums = state.get("files", {})

    templates = dict(ALL_TEMPLATES)
    if not config.get("error_to_issue"):
        templates.pop(".opencode/skills/error-handling/SKILL.md", None)

    for key in TEMPLATE_FILES_TO_SKIP:
        templates.pop(key, None)

    dirs_to_create = set()
    for filepath in templates:
        full_path = os.path.join(root, filepath)
        parent = os.path.dirname(full_path)
        if parent:
            dirs_to_create.add(parent)

    if not dry_run:
        for d in sorted(dirs_to_create):
            os.makedirs(d, exist_ok=True)

    new_files = [fp for fp in templates if fp not in old_checksums]
    for filepath in new_files:
        try:
            content = render_template(templates[filepath], vars_dict)
            if not dry_run:
                full_path = os.path.join(root, filepath)
                with open(full_path, "w", newline="\n", encoding="utf-8") as f:
                    f.write(content)
            added.append(filepath)
        except Exception as e:
            errors.append((filepath, str(e)))

    removed_files = [fp for fp in old_checksums if fp not in templates]
    removed = removed_files

    for filepath in templates:
        if filepath in new_files:
            continue

        template = templates[filepath]
        old_checksum = old_checksums.get(filepath)
        if old_checksum is None:
            continue

        full_path = os.path.join(root, filepath)

        if not os.path.exists(full_path):
            try:
                content = render_template(template, vars_dict)
                if not dry_run:
                    with open(full_path, "w", newline="\n", encoding="utf-8") as f:
                        f.write(content)
                updated.append(filepath)
            except Exception as e:
                errors.append((filepath, str(e)))
            continue

        try:
            new_content = render_template(template, vars_dict)
        except Exception as e:
            errors.append((filepath, str(e)))
            continue

        new_checksum = calculate_checksum(new_content.encode("utf-8"))

        try:
            with open(full_path, "rb") as f:
                current_content_bytes = f.read()
            current_checksum = calculate_checksum(current_content_bytes)
        except Exception as e:
            errors.append((filepath, str(e)))
            continue

        if current_checksum == old_checksum:
            if not dry_run:
                with open(full_path, "w", newline="\n", encoding="utf-8") as f:
                    f.write(new_content)
            updated.append(filepath)
        else:
            if new_checksum == old_checksum:
                skipped.append(filepath)
            else:
                if not dry_run:
                    conflict_path = full_path + ".new"
                    with open(conflict_path, "w", newline="\n", encoding="utf-8") as f:
                        f.write(new_content)
                conflicts.append(filepath)

    if not dry_run:
        new_checksums = {}
        for filepath in templates:
            full_path = os.path.join(root, filepath)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    new_checksums[filepath] = calculate_checksum(f.read())
        write_state(root, KIT_VERSION, new_checksums)

    return updated, skipped, conflicts, added, removed, errors

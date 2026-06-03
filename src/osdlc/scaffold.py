import os
from osdlc.templates import ALL_TEMPLATES


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
        "PHP": "ruby",
        "C/C++": "cpp",
        "C#": "csharp",
        "Swift": "swift",
        "Elixir": "ruby",
    }
    return mapping.get(language, "python")


def detect_ecosystem(build_system):
    mapping = {
        "Maven": "maven",
        "Gradle Kotlin": "gradle",
        "Gradle": "gradle",
        "npm": "npm",
        "Cargo": "cargo",
        "PEP 621": "pip",
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
        "codeql_languages": f"[{codeql_lang!r}]",
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

    dirs_to_create = set()
    for filepath in ALL_TEMPLATES:
        full_path = os.path.join(root, filepath)
        parent = os.path.dirname(full_path)
        if parent:
            dirs_to_create.add(parent)

    for d in sorted(dirs_to_create):
        os.makedirs(d, exist_ok=True)

    for filepath, template in ALL_TEMPLATES.items():
        if filepath == ".opencode/skills/error-handling/SKILL.md" and not config.get("error_to_issue"):
            continue

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

    return generated, skipped, errors

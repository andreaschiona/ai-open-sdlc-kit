import os

PROBES = [
    ("pom.xml",             "Maven",       "Java",        "pom.xml",              "mvn compile",           "mvn test",            "mvn checkstyle:check"),
    ("build.gradle.kts",    "Gradle Kotlin","Kotlin/Java","gradle.properties",    "./gradlew build",       "./gradlew test",      "./gradlew ktlintCheck"),
    ("build.gradle",        "Gradle",      "Java",        "gradle.properties",    "./gradlew build",       "./gradlew test",      "./gradlew check"),
    ("package.json",        "npm",         "JavaScript",  "package.json",         "npm run build",         "npm test",            "npm run lint"),
    ("Cargo.toml",          "Cargo",       "Rust",        "Cargo.toml",           "cargo build",           "cargo test",          "cargo clippy"),
    ("pyproject.toml",      "PEP 621",     "Python",      "pyproject.toml",       "python -m build",       "pytest",              "ruff check ."),
    ("go.mod",              "Go modules",  "Go",          "version.go",           "go build ./...",        "go test ./...",       "go vet ./..."),
    ("composer.json",       "Composer",    "PHP",         "composer.json",        "composer install",      "phpunit",             "phpcs"),
    ("Gemfile",             "Bundler",     "Ruby",        "lib/version.rb",       "bundle exec rake build", "bundle exec rspec",   "bundle exec rubocop"),
    ("CMakeLists.txt",      "CMake",       "C/C++",       "CMakeLists.txt",       "cmake --build build",   "ctest",               "cmake --build build --target lint"),
    ("mix.exs",             "Mix",         "Elixir",      "mix.exs",              "mix compile",           "mix test",            "mix credo"),
]

LANGUAGE_EXTENSIONS = {
    ".kt":   "Kotlin",
    ".kts":  "Kotlin",
    ".java": "Java",
    ".js":   "JavaScript",
    ".ts":   "TypeScript",
    ".jsx":  "React",
    ".tsx":  "React TypeScript",
    ".rs":   "Rust",
    ".py":   "Python",
    ".go":   "Go",
    ".rb":   "Ruby",
    ".ex":   "Elixir",
    ".exs":  "Elixir",
    ".php":  "PHP",
    ".cs":   "C#",
    ".swift":"Swift",
}


def detect_project_type(root="."):
    for probe, build_system, language, version_file, build_cmd, test_cmd, lint_cmd in PROBES:
        path = os.path.join(root, probe)
        if os.path.exists(path):
            return {
                "build_system": build_system,
                "language": language,
                "version_file": version_file,
                "build_cmd": build_cmd,
                "test_cmd": test_cmd,
                "lint_cmd": lint_cmd,
                "probe": probe,
            }
    return None


def suggest_language_by_extension(root="."):
    counts = {}
    for entry in os.scandir(root):
        if entry.is_file():
            _, ext = os.path.splitext(entry.name)
            if ext in LANGUAGE_EXTENSIONS:
                lang = LANGUAGE_EXTENSIONS[ext]
                counts[lang] = counts.get(lang, 0) + 1
    if counts:
        return max(counts, key=counts.get)
    return None

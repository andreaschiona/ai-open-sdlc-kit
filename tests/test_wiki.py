import os
import pytest
from osdlc.wiki import (
    slugify,
    extract_frontmatter,
    WikiIndex,
    WikiIngestor,
    WikiLinter,
    DEFAULT_CATEGORIES,
)


class TestSlugify:
    def test_basic(self):
        assert slugify("LLM Wiki Pattern") == "llm-wiki-pattern"

    def test_special_chars(self):
        assert slugify("Hello, World! How are you?") == "hello-world-how-are-you"

    def test_multiple_spaces(self):
        assert slugify("a   b   c") == "a-b-c"

    def test_leading_trailing(self):
        assert slugify("  hello  ") == "hello"


class TestExtractFrontmatter:
    def test_with_frontmatter(self):
        text = """---
title: Test Title
tags: foo, bar
---

Body content"""
        fm, body = extract_frontmatter(text)
        assert fm["title"] == "Test Title"
        assert fm["tags"] == "foo, bar"
        assert body == "Body content"

    def test_without_frontmatter(self):
        text = "Just body content"
        fm, body = extract_frontmatter(text)
        assert fm == {}
        assert body == "Just body content"

    def test_empty(self):
        fm, body = extract_frontmatter("")
        assert fm == {}
        assert body == ""


class TestWikiInit:
    def test_wiki_init_creates_structure(self, temp_dir):
        index = WikiIndex(temp_dir)
        assert not os.path.exists(index.wiki_dir)

        raw_dir = os.path.join(temp_dir, "raw")
        wiki_dir = os.path.join(temp_dir, "wiki")
        os.makedirs(raw_dir, exist_ok=True)
        for cat in DEFAULT_CATEGORIES:
            os.makedirs(os.path.join(wiki_dir, cat), exist_ok=True)
        index.write()

        assert os.path.isdir(raw_dir)
        assert os.path.isdir(wiki_dir)
        for cat in DEFAULT_CATEGORIES:
            assert os.path.isdir(os.path.join(wiki_dir, cat))
        assert os.path.isfile(index.index_path)

    def test_index_content(self, temp_dir):
        raw_dir = os.path.join(temp_dir, "raw")
        wiki_dir = os.path.join(temp_dir, "wiki")
        os.makedirs(raw_dir, exist_ok=True)
        for cat in DEFAULT_CATEGORIES:
            os.makedirs(os.path.join(wiki_dir, cat), exist_ok=True)

        index = WikiIndex(temp_dir)
        content = index.build()

        assert "# Indice Wiki" in content
        for cat in DEFAULT_CATEGORIES:
            title = cat.replace("-", " ").title()
            assert title in content

    def test_categories_empty_initially(self, temp_dir):
        index = WikiIndex(temp_dir)
        assert index.get_categories() == []


class TestWikiIngest:
    def test_ingest_creates_wiki_page(self, temp_dir):
        raw_dir = os.path.join(temp_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        source_path = os.path.join(raw_dir, "test-article.md")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write("""---
title: "Test Article"
tags: ai, test
---

This is a test article with some content.
- **Key point one**: description
- **Key point two**: description
Related to [[other-page]] and [[another-page]].
""")

        ingestor = WikiIngestor(temp_dir)
        page = ingestor.ingest(source_path, category="metodologie-dev")
        assert page.slug == "test-article"
        assert page.category == "metodologie-dev"
        assert "ai" in page.tags
        assert "test" in page.tags
        assert "Key point one" in page.key_points[0]
        assert "other-page" in page.related
        assert "another-page" in page.related

        wiki_path = os.path.join(temp_dir, "wiki", "metodologie-dev", "test-article.md")
        assert os.path.isfile(wiki_path)
        with open(wiki_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Test Article" in content
            assert "---" in content
            assert "test-article.md" in content

    def test_ingest_updates_index(self, temp_dir):
        raw_dir = os.path.join(temp_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        source_path = os.path.join(raw_dir, "doc.md")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write("# Just a doc")

        ingestor = WikiIngestor(temp_dir)
        ingestor.ingest(source_path, category="strumenti-ai")

        index = WikiIndex(temp_dir)
        content = index.build()
        assert "doc" in content or "Doc" in content


class TestWikiLint:
    def test_lint_no_wiki_dir(self, temp_dir):
        linter = WikiLinter(temp_dir)
        issues = linter.lint()
        assert any("non trovata" in i for i in issues)

    def test_lint_finds_no_issues(self, temp_dir):
        raw_dir = os.path.join(temp_dir, "raw")
        wiki_dir = os.path.join(temp_dir, "wiki")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(os.path.join(wiki_dir, "metodologie-dev"))

        source_path = os.path.join(raw_dir, "good.md")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write("# Good article")

        ingestor = WikiIngestor(temp_dir)
        ingestor.ingest(source_path, category="metodologie-dev")

        linter = WikiLinter(temp_dir)
        issues = linter.lint()
        assert len(issues) == 0

    def test_lint_finds_broken_wikilinks(self, temp_dir):
        raw_dir = os.path.join(temp_dir, "raw")
        wiki_dir = os.path.join(temp_dir, "wiki")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(os.path.join(wiki_dir, "metodologie-dev"))

        source_path = os.path.join(raw_dir, "with-link.md")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write("""---
title: With Link
tags: test
---

Links to [[missing-page]] that does not exist.
""")

        ingestor = WikiIngestor(temp_dir)
        ingestor.ingest(source_path, category="metodologie-dev")

        linter = WikiLinter(temp_dir)
        issues = linter.lint()
        broken = [i for i in issues if "missing-page" in i]
        assert len(broken) > 0

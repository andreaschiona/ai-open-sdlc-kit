import os
import re
from datetime import date
from dataclasses import dataclass, field

DEFAULT_CATEGORIES = [
    "architettura-enterprise",
    "metodologie-dev",
    "strumenti-ai",
]

WIKI_PAGE_TEMPLATE = """---
tags: {tags}
data_creazione: {data_creazione}
data_aggiornamento: {data_aggiornamento}
fonti:
{fonti}
---

# {titolo}

{descrizione}

## Punti chiave

{punti_chiave}

## Architettura

{architettura}

## Operazioni

{operazioni}

## Confronto

{confronto}

## Prospettiva futura

{prospettiva_futura}

## Articoli correlati

{articoli_correlati}

## Fonti

{fonti_list}
"""

INDEX_TEMPLATE = """# Indice Wiki

_{data}_

{contenuto}
"""


@dataclass
class WikiPage:
    slug: str
    title: str
    category: str
    tags: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    sources: list[str] = field(default_factory=list)
    description: str = ""
    key_points: list[str] = field(default_factory=list)
    architecture: str = ""
    operations: str = ""
    comparison: str = ""
    future: str = ""
    related: list[str] = field(default_factory=list)

    @property
    def filename(self):
        return f"{self.slug}.md"

    @property
    def filepath(self):
        return os.path.join(self.category, self.filename)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def today_str() -> str:
    return date.today().strftime("%d/%m/%Y")


def extract_frontmatter(text: str) -> tuple[dict, str]:
    body = text
    fm = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw = parts[1].strip()
            body = parts[2].strip()
            current_key = None
            list_vals = []
            for line in raw.split("\n"):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                if line_stripped.startswith("- "):
                    if current_key is not None:
                        list_vals.append(line_stripped[2:].strip())
                elif ":" in line_stripped:
                    if current_key is not None and list_vals:
                        fm[current_key] = "\n".join(list_vals)
                        list_vals = []
                    key, _, val = line_stripped.partition(":")
                    current_key = key.strip()
                    val = val.strip()
                    if val:
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1]
                        fm[current_key] = val
                        current_key = None
                    else:
                        list_vals = []
            if current_key is not None and list_vals:
                fm[current_key] = "\n".join(list_vals)
    return fm, body


class WikiIndex:
    def __init__(self, root: str):
        self.root = root
        self.wiki_dir = os.path.join(root, "wiki")
        self.index_path = os.path.join(root, "indice")

    def get_categories(self) -> list[str]:
        if not os.path.isdir(self.wiki_dir):
            return []
        return sorted(
            d for d in os.listdir(self.wiki_dir)
            if os.path.isdir(os.path.join(self.wiki_dir, d))
        )

    def get_pages(self, category: str) -> list[WikiPage]:
        cat_dir = os.path.join(self.wiki_dir, category)
        if not os.path.isdir(cat_dir):
            return []
        pages = []
        for fname in sorted(os.listdir(cat_dir)):
            if fname.endswith(".md"):
                path = os.path.join(cat_dir, fname)
                page = self._load_page(category, fname, path)
                if page:
                    pages.append(page)
        return pages

    def _load_page(self, category: str, fname: str, path: str) -> WikiPage | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None
        fm, body = extract_frontmatter(content)
        slug = fname.replace(".md", "")
        title = fm.get("titolo", slug.replace("-", " ").title())
        tags_str = fm.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        sources_str = fm.get("fonti", "")
        sources = [s.strip() for s in sources_str.split("\n") if s.strip()]
        return WikiPage(
            slug=slug,
            title=title,
            category=category,
            tags=tags,
            created=fm.get("data_creazione", ""),
            updated=fm.get("data_aggiornamento", ""),
            sources=sources,
        )

    def build(self) -> str:
        categories = self.get_categories()
        lines = []
        for cat in categories:
            cat_title = cat.replace("-", " ").title()
            lines.append(f"## {cat_title}\n")
            pages = self.get_pages(cat)
            if not pages:
                lines.append("_Nessuna pagina_\n")
            for p in pages:
                tags_str = ", ".join(p.tags) if p.tags else ""
                tag_info = f" — {tags_str}" if tags_str else ""
                lines.append(f"- [[{p.slug}]]{tag_info}")
            lines.append("")
        content = "\n".join(lines)
        return INDEX_TEMPLATE.format(
            data=today_str(),
            contenuto=content,
        )

    def write(self):
        content = self.build()
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            f.write(content)
        return content


class WikiIngestor:
    def __init__(self, root: str):
        self.root = root
        self.raw_dir = os.path.join(root, "raw")
        self.wiki_dir = os.path.join(root, "wiki")

    def ingest(self, source_path: str, category: str = "metodologie-dev") -> WikiPage:
        with open(source_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        fm, body = extract_frontmatter(raw_text)
        title = fm.get("title", os.path.splitext(os.path.basename(source_path))[0])
        title = _clean_title(title)
        slug = slugify(title)

        tags = self._infer_tags(fm, body, category)
        description = self._extract_description(body)
        key_points = self._extract_key_points(body)
        related = self._extract_wikilinks(body)

        rel_path = os.path.relpath(source_path, self.root)

        page = WikiPage(
            slug=slug,
            title=title,
            category=category,
            tags=tags,
            created=today_str(),
            updated=today_str(),
            sources=[rel_path],
            description=description,
            key_points=key_points,
            related=related,
        )
        self._write_page(page)
        return page

    def _write_page(self, page: WikiPage):
        cat_dir = os.path.join(self.wiki_dir, page.category)
        os.makedirs(cat_dir, exist_ok=True)
        tags_str = ", ".join(page.tags)
        fonti = "\n".join(f"  - {s}" for s in page.sources)
        punti_chiave = "\n".join(f"- {kp}" for kp in page.key_points) if page.key_points else "_Da compilare_"
        related_str = "\n".join(f"- [[{r}]]" for r in page.related) if page.related else "_Nessuno_"
        fonti_list = "\n".join(f"- {s}" for s in page.sources) if page.sources else "_Nessuna_"

        content = WIKI_PAGE_TEMPLATE.format(
            tags=tags_str,
            data_creazione=page.created,
            data_aggiornamento=page.updated,
            fonti=fonti,
            titolo=page.title,
            descrizione=page.description or "_Descrizione da compilare_",
            punti_chiave=punti_chiave,
            architettura="_Da compilare_",
            operazioni="_Da compilare_",
            confronto="_Da compilare_",
            prospettiva_futura="_Da compilare_",
            articoli_correlati=related_str,
            fonti_list=fonti_list,
        )

        filepath = os.path.join(cat_dir, page.filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def _infer_tags(self, fm: dict, body: str, category: str) -> list[str]:
        tags = {category}
        if "tags" in fm:
            raw = fm["tags"]
            for t in re.split(r"[,;\s]+", raw):
                t = t.strip().strip('"').strip("'")
                if t:
                    tags.add(t)
        lower = body.lower()
        keyword_tags = {
            "rag": ["rag", "retrieval"],
            "llm": ["llm", "large language model"],
            "ai": ["ai", "artificial intelligence", "intelligenza artificiale"],
            "karpathy": ["karpathy", "andrej"],
        }
        for tag, keywords in keyword_tags.items():
            if any(k in lower for k in keywords):
                tags.add(tag)
        return sorted(tags)

    def _extract_description(self, body: str) -> str:
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for p in paragraphs:
            p_clean = re.sub(r"^#{1,6}\s+", "", p).strip()
            if len(p_clean) > 40 and not p_clean.startswith("http"):
                return p_clean[:300]
        return ""

    def _extract_key_points(self, body: str) -> list[str]:
        points = []
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("- **") or line.startswith("* **"):
                points.append(line.lstrip("-* ").strip())
            elif re.match(r"^\d+\.\s+\*\*", line):
                points.append(re.sub(r"^\d+\.\s+", "", line).strip())
        return points[:8]

    def _extract_wikilinks(self, body: str) -> list[str]:
        return re.findall(r"\[\[([^\]]+)\]\]", body)


class WikiLinter:
    def __init__(self, root: str):
        self.root = root
        self.wiki_dir = os.path.join(root, "wiki")
        self.index = WikiIndex(root)

    def lint(self) -> list[str]:
        issues = []
        if not os.path.isdir(self.wiki_dir):
            return ["wiki/ directory non trovata"]

        all_pages: dict[str, WikiPage] = {}
        for cat in self.index.get_categories():
            for page in self.index.get_pages(cat):
                all_pages[page.slug] = page

        if not all_pages:
            issues.append("Nessuna pagina wiki trovata")

        for slug, page in all_pages.items():
            if not page.tags:
                issues.append(f"{page.filename}: nessun tag")
            if not page.created:
                issues.append(f"{page.filename}: data_creazione mancante")
            if not page.sources:
                issues.append(f"{page.filename}: nessuna fonte collegata")

        all_slugs = set(all_pages.keys())
        for slug, page in all_pages.items():
            path = os.path.join(self.wiki_dir, page.category, page.filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                linked = re.findall(r"\[\[([^\]]+)\]\]", content)
                for link in linked:
                    if link not in all_slugs:
                        issues.append(f"{page.filename}: wikilink [[{link}]] non trovato")

        return issues


def _clean_title(title: str) -> str:
    title = re.sub(r"\s*\|.*$", "", title)
    title = re.sub(r"^\"|\"$", "", title)
    return title.strip()

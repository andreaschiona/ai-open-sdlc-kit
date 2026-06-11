# Wiki Skill

## Purpose

This skill implements the **LLM Wiki pattern** (Karpathy, 2026): an LLM-maintained markdown knowledge base that compounds knowledge over time via three operations: Ingest, Query, Lint.

## Architecture

Three layers:
1. **Raw Sources** (`raw/`) -- Immutable original materials (articles, papers, transcripts)
2. **The Wiki** (`wiki/`) -- LLM-maintained markdown pages organized by category, with cross-references and master index
3. **The Schema** (this file + AGENTS.md) -- Configuration directing agent behavior

## Commands

### `osdlc wiki init`

Create the directory structure and master index:
```
raw/
wiki/
  architettura-enterprise/
  metodologie-dev/
  strumenti-ai/
indice
```

### `osdlc wiki ingest <file> [--category <cat>]`

1. Place the source file in `raw/`
2. Read the entire source
3. Generate a structured wiki page with:
   - YAML frontmatter (tags, dates, source path)
   - Title and description
   - Key points extracted from the source
   - Architecture section (three layers applied to this domain)
   - Operations section (Ingest/Query/Lint in context)
   - RAG vs LLM Wiki comparison table
   - Future perspective
   - Cross-references (`[[wikilink]]`) to related pages
4. Update the master index

### `osdlc wiki index`

Rebuild the master index at `indice` listing all pages grouped by category.

### `osdlc wiki lint`

Scan the wiki for:
- Stale claims or missing dates
- Orphan pages (no incoming wikilinks)
- Broken wikilinks (target page not found)
- Missing tags or sources

## Wiki Page Format

Every wiki page MUST follow this structure:

```markdown
---
tags: tag1, tag2
data_creazione: DD/MM/YYYY
data_aggiornamento: DD/MM/YYYY
fonti:
  - raw/nome-file.md
---

# Titolo Pagina

Descrizione del pattern o concetto.

## Punti chiave

- Punto chiave 1
- Punto chiave 2

## Architettura

### Layer 1: Raw Sources
...
### Layer 2: The Wiki
...
### Layer 3: The Schema
...

## Le tre operazioni

### Ingest
...
### Query
...
### Lint
...

## Confronto

| Aspetto | Opzione A | Opzione B |
|---------|-----------|-----------|
| ...     | ...       | ...       |

## Articoli correlati

- [[slug-pagina-correlata]]

## Fonti

- raw/nome-file.md
```

## Index Format

The master index (`indice`) follows this structure:

```markdown
# Indice Wiki

_GG/MM/AAAA_

## Nome Categoria

- [[slug-pagina]] — tag1, tag2

## Altra Categoria

- [[slug-pagina2]] — tag3, tag4
```

# ⚖ Project Janus

> A sovereign, closed-loop archival system — crawl, clone, archive and query
> the web with a fully local AI brain. No external APIs. No censorship.

[![CI](https://github.com/Grumpified-OGGVCT/Project_Janus/actions/workflows/ci.yml/badge.svg)](https://github.com/Grumpified-OGGVCT/Project_Janus/actions/workflows/ci.yml)
[![Demo](https://img.shields.io/badge/demo-GitHub_Pages-blue)](https://grumpified-oggvct.github.io/Project_Janus/)
[![License](https://img.shields.io/github/license/Grumpified-OGGVCT/Project_Janus)](LICENSE)

**[🌐 Live Demo Page →](https://grumpified-oggvct.github.io/Project_Janus/)**

---

## Architecture

```
User Prompt
    ↓
Mistral Large 3 (Ollama — 256K ctx, native function-calling)
    ↓ tool call          ↑ raw data
MCP Server (read-only librarian)
    ↓ queries
SQLite Vault + ChromaDB (vector index)
    ↑ populated by
Harvester  /  Site Cloner (field agents)
```

| Component | File | Role |
|-----------|------|------|
| Brain | `run_agent.py` | Mistral Large 3 via Ollama; drives tool-call loop |
| Librarian | `src/mcp_server/server.py` | MCP tools: `search_archives`, `view_thread_history` |
| Thread Harvester | `src/harvester/engine.py` | Per-thread crawl + Wayback CDX snapshots → `vault.db` |
| **Site Cloner** | `src/harvester/site_cloner.py` | **Full-domain Markdown mirror with rewritten links** |
| Vault | `src/vault/schema.sql` | SQLite schema with temporal versioning |

---

## Site Cloner — Full Markdown Mirror

The `SiteCloner` crawls an entire domain and produces a **fully navigable
Markdown clone** that works in GitHub, Obsidian, VS Code, or any Markdown
renderer:

```
data/site_mirror/your-site.net/
  _index.md               ← generated sitemap / navigation tree
  index.md                ← home page
  threads/
    some-thread.md
    another-thread.md
  forums/
    general.md
```

Every internal link is **rewritten to a relative `.md` path** so you can
navigate the entire mirror offline exactly as you would the live site.

```python
from src.harvester.site_cloner import SiteCloner

cloner = SiteCloner(output_dir="data/site_mirror", max_pages=1000)
cloner.clone("https://your-site.net/")
```

Or configure it in `main.py`:

```python
TARGET_SITE     = "https://your-site.net/"
CLONE_MAX_PAGES = 1000
```

---

## Features

- **Full-site Markdown clone** — entire domain mirrored as linked `.md` files; `_index.md` navigation tree auto-generated
- **Temporal versioning** — `live`, `wayback_oldest`, `wayback_recent` captures stored side-by-side
- **Immutable vault** — SHA-256 content hashes; MCP server always opens DB in `mode=ro`
- **Semantic search** — `all-MiniLM-L6-v2` embeddings + ChromaDB, entirely local
- **100% local AI** — zero OpenAI / Anthropic; all inference via Ollama
- **Native tool-calling** — Mistral Large 3 function-calling drives the MCP tool loop
- **CI-tested** — unit tests run on every push via GitHub Actions
- **Org-secret demo** — weekly auto-demo commits fresh output to the GitHub Pages demo site

---

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/Grumpified-OGGVCT/Project_Janus.git
cd Project_Janus
pip install -r requirements.txt

# 2. Configure targets (edit main.py)
TARGET_URLS = ["https://your-site.net/threads/example.123/"]  # per-thread harvest
TARGET_SITE = "https://your-site.net/"                        # full-site clone

# 3. Run (harvest → clone → launch AI agent)
python main.py

# Agent only
python run_agent.py
```

---

## GitHub Actions

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `CI` | Every push / PR | Install deps, run unit tests |
| `Live Demo` | Manual + weekly (Mon 00:00 UTC) | Run canned Ollama query, commit updated demo page |

### Required organisation secret

| Secret | Value |
|--------|-------|
| `OLLAMA_HOST` | URL of your remote Ollama server, e.g. `https://ollama.example.com` |

### Enable the demo page (one-time setup)

```
GitHub Repo → Settings → Pages
  Source: Deploy from branch → main → /docs → Save
```

The demo page will then be live at:
`https://grumpified-oggvct.github.io/Project_Janus/`

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```


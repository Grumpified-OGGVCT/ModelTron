# AGENTS.md — Agent Contextual Guide

> This file helps ALL agents (Jules, Copilot, Antigravity, Gemini CLI, etc.) understand the ModelTron repository.
> **Framework Version: 12-Hat Aegis-Nexus CoVE v2.0** | **Last Updated: 2026-03-03**

---

## 1. Project Overview

ModelTron is a **sovereign, closed-loop archival system**. It crawls, clones, archives, and queries the web using a fully local AI brain (Mistral Large 3 via Ollama). No external APIs. No censorship.

### Architecture

| Component | File | Role |
|---|---|---|
| Brain | `run_agent.py` | Mistral Large 3 via Ollama; drives tool-call loop with O(1) context bounding |
| Librarian | `src/mcp_server/server.py` | MCP tools: `search_archives`, `view_thread_history`, `deep_retrieve_context7` |
| Thread Harvester | `src/harvester/engine.py` | Per-thread crawl + Wayback CDX snapshots → vault.db |
| Site Cloner | `src/harvester/site_cloner.py` | Full-domain Markdown mirror with rewritten links (path traversal hardened) |
| Vault | `src/vault/schema.sql` | SQLite schema with temporal versioning |
| Live Demo | `docs/index.html` | GitHub Pages demo with inner thoughts panel |
| Setup Wizard | `scripts/setup_wizard.py` | Rich TUI wizard with Ollama integration |
| Hat Review Agent | `.github/agents/hats.agent.md` | Full 12-Hat CoVE v2.0 validation (849 lines, 49KB) |

### Project Layout

```
ModelTron/
├── .github/
│   ├── agents/hats.agent.md     # 12-Hat CoVE v2.0 review agent (FULL SPEC)
│   └── workflows/
│       ├── demo.yml             # Demo page CI
│       └── maintenance.yml      # Weekly security/test/doc audits
├── docs/
│   └── index.html               # Live demo page (GitHub Pages)
├── scripts/
│   └── setup_wizard.py          # Interactive TUI setup wizard
├── src/
│   ├── harvester/
│   │   ├── engine.py            # Thread harvester
│   │   └── site_cloner.py       # Full-domain Markdown mirror
│   ├── mcp_server/
│   │   └── server.py            # MCP tools (read-only vault access)
│   └── vault/
│       └── schema.sql           # SQLite schema
├── tests/                       # pytest test suite
├── run_agent.py                 # Agent runner with Infinite CTX
├── requirements.txt             # Python dependencies (40+)
├── install.bat / install.sh     # Cross-platform installers
├── run.bat / run.sh             # Quick launch scripts
└── AGENTS.md                    # THIS FILE — agent instructions
```

---

## 2. Anti-Reductionist Mandate

> **You are encouraged to build, code, enhance, and improve.** The restriction is specifically against **gratuitous deletion** — removing things simply because their use appears out of scope.

Jules MUST NEVER produce empty "all clean" reviews. If a hat genuinely has no findings, explain (in 2-3 sentences) what was examined and why it passed. Generic "looks good" is **prohibited** — this is a military-grade system.

### ✅ DO (encouraged)
- **Write new code** — add features, modules, tests, utilities
- **Enhance existing code** — improve performance, readability, error handling
- **Add new files** — create documentation, workflows, configs, helpers
- **Fix bugs** — correct broken behavior, add missing error handling
- **Expand tests** — increase coverage, add edge cases, new test files
- **Refactor for clarity** — restructure code to be cleaner, as long as all functionality is preserved
- **Add imports** — bring in new dependencies as needed for new features
- **Modify existing code** — update, extend, and evolve implementations

### ❌ DON'T (prohibited)
- **Delete imports** "because they're unused" — they may be used elsewhere, planned for use, or serve as documentation of available capabilities
- **Delete files** "for cleanup" — if a file exists, it was put there for a reason
- **Remove test cases** "to make tests pass" — fix the code, don't delete the test
- **Strip comments** "to clean up" — comments are documentation and context
- **Simplify code** by removing error handling, fallback paths, or edge case coverage
- **Remove features** "to reduce complexity" — complexity exists because the use case demands it
- **Delete configuration stanzas** because "they're not currently active"

### The Core Principle
> Stock AI agents are notorious for deleting imports, removing "unused" code, and stripping files that look redundant. **This is catastrophic behavior.** If you're not sure whether something is needed — leave it. If you want to deprecate something, add a deprecation notice comment, don't delete it.

---

## 3. Security Invariants (DO NOT VIOLATE)

These invariants MUST be maintained in every change:

1. **MCP Server is read-only** — `server.py` must never write to the vault
2. **SHA-256 integrity** — content hashing for deduplication must not be weakened
3. **No external API calls** — all inference runs through local Ollama
4. **Input sanitization** — any user-facing input (demo page) must be escaped for XSS
5. **No secrets in code** — API keys, tokens, and credentials go in environment variables or org secrets only
6. **Path traversal hardening** — `site_cloner.py` sanitization must not be weakened (blocks `../`, null bytes, absolute paths)

---

## 4. Test Conventions

- **Framework:** `pytest` with standard assertions
- **Run all tests:** `pytest tests/ -v --tb=short`
- **Naming:** `test_<feature>.py` with functions named `test_<scenario>()`
- **Coverage:** Test count must be >= previous baseline — never remove tests to make suite pass
- **Adversarial tests:** Security-critical code (site_cloner, input handling) includes adversarial regression tests

---

## 5. 12-Hat Aegis-Nexus Agent Personas (MANDATORY)

> **CRITICAL**: When decomposing tasks, Jules MUST use these 12-Hat personas instead of
> generic agent types. Organize all work, commits, and PR descriptions by hat category.

Jules MUST structure its work using the **12-Hat Aegis-Nexus CoVE v2.0** methodology.
Each hat represents a specialized adversarial analysis perspective. When working on any task:

1. **Assess** which hats are relevant to the current task
2. **Organize** your work and commits by hat category
3. **Label** each finding/change with its hat color and severity
4. **Never skip** the Black Hat (Security), Blue Hat (Process), or Purple Hat (Compliance) on any PR

### Hat Definitions

| Hat | Color | Focus Area | When to Apply |
|-----|-------|-----------|---------------|
| 🔴 Red Hat | Red | Fail-states, cascading failures, chaos testing, accessibility | Error handling, resilience, exception paths, UI interactions |
| ⚫ Black Hat | Black | Security exploits, OWASP Top 10, zero trust, supply chain | ALL code changes (mandatory) |
| ⚪ White Hat | White | Efficiency, token usage, data integrity, DB performance | Performance-sensitive code, LLM calls, queries |
| 🟡 Yellow Hat | Yellow | Synergies, optimization, cross-component 10x wins | Architecture, integration points, missed opportunities |
| 🟢 Green Hat | Green | Missing mechanisms, growth paths, i18n, feature completeness | New features, missing wiring, dead code, loose ends |
| 🔵 Blue Hat | Blue | Process completeness, observability, operational readiness | Documentation, config, specs, ALL PRs (mandatory) |
| 🟣 Indigo Hat | Indigo | Cross-feature architecture, DRY, API contracts, gate fusion | Refactoring, pipeline work, multi-file changes |
| 🩵 Cyan Hat | Cyan | Innovation, AI/ML validation, bias & fairness, feasibility | AI features, prompt engineering, model evaluation |
| 🟪 Purple Hat | Purple | AI safety, OWASP LLM Top 10, compliance, regulatory | ALL code changes (mandatory) |
| 🟠 Orange Hat | Orange | DevOps, CI/CD, Docker, Git hygiene, license governance | Infrastructure, deployment, SBOM, licensing |
| 🪨 Silver Hat | Silver | Context/token optimization, O(1) bounding, cost efficiency | LLM interactions, prompt engineering, context management |
| 🔷 Azure Hat | Azure | MCP workflow integrity, task lifecycle, HITL gates | MCP server, tool schemas, agent loops, task management |

### Mandatory Hats (Always Active)
- ⚫ **Black Hat** — Security is non-negotiable
- 🔵 **Blue Hat** — Process completeness on every PR
- 🟪 **Purple Hat** — AI safety and compliance always

### Severity Levels
- 🔴 **CRITICAL** — Must fix before merge. Security vulnerabilities, data loss risks, RCE, regulatory violations
- 🟠 **HIGH** — Should fix. Significant bugs, missing error handling, 25%+ user impact
- 🟡 **MEDIUM** — Fix soon. Performance issues, missing tests, UX friction
- 🟢 **LOW** — Nice to have. Code style, minor optimizations
- ℹ️ **INFO** — Informational. Architecture suggestions, future ideas

### Commit Message Format
```
feat(<hat>): <description>

Example:
feat(black-hat): add path sanitization to site_cloner
fix(red-hat): handle SQLite database locked under concurrency
feat(azure-hat): enforce HITL gate before task completion
feat(green-hat): wire inner thoughts panel to response parser
```

### Full CoVE Specification
For the complete 12-Hat validation checklists, Meta-Hat Router, CTX-Budget Protocol,
output formats (Markdown + JSON), compliance matrix, and per-hat detailed skill sets,
see **`.github/agents/hats.agent.md`** (849 lines, 49KB).

Jules MUST load and follow that file for all PR reviews and code validation.

---

## 6. Key Data Flow

```
User Input → run_agent.py → O(1) Context Bounding (snapshot + last ≤10 actions)
  → Ollama (Mistral Large 3) → Tool Call Decision
  → MCP Server (search_archives / view_thread_history / deep_retrieve_context7)
  → Vault (SQLite, read-only) → Response with Inner Thoughts
```

### Infinite CTX Protocol
- **O(1) Context Bounding**: Workspace snapshot + last ≤10 actions only
- **No linear accumulation**: Historical tokens actively discarded, context size constant
- **Global-reasoning threshold**: 10M+ token contexts only when explicitly justified
- **Gas metering**: Resource budgets tracked per operation

---

## 7. PR Checklist

Before submitting any PR, verify:

- [ ] No files were deleted (unless explicitly requested by the repo owner)
- [ ] No imports were removed just because they appear unused
- [ ] No test cases were removed to make the suite pass
- [ ] All new code includes inline documentation (comments explaining "why")
- [ ] Test count is >= previous baseline (run `pytest tests/ -v`)
- [ ] All existing features still work after changes
- [ ] `docs/index.html` still renders correctly and the inner thoughts panel functions
- [ ] Security invariants (Section 3) are maintained
- [ ] New features include corresponding tests where applicable
- [ ] Commit messages follow hat format: `feat(<hat>): <description>`

---

## 8. Code Quality Standards

- **Docstrings** on all public functions and classes
- **Type hints** for function signatures (Python 3.10+ style)
- **Error handling** — no bare `except:` clauses; catch specific exceptions
- **Logging** over `print()` for runtime output
- **UTF-8** encoding for all text files

---

## 9. Maintenance Tasks (Weekly)

The automated maintenance workflow (`.github/workflows/maintenance.yml`) runs weekly and covers:

1. **Security audit** — dependency vulnerability scanning (bandit, pip-audit)
2. **Dependency check** — report outdated packages (don't auto-update without review)
3. **Test execution** — full `pytest` suite with coverage report
4. **Documentation freshness** — verify README, AGENTS.md, and docs/ are current
5. **Demo page validation** — check that `docs/index.html` loads, inner thoughts panel works, mandatory UI elements present
6. **Lint check** — code style consistency (ruff or equivalent)

---

## 10. GUI & Demo Page Upkeep (MANDATORY)

Four hats carry designated **UPKEEP** responsibilities to ensure every code change is fully represented in the GUI and demo page — no mocks, no placeholders:

- **🔴 Red Hat**: Verify demo page functional integrity after ANY backend change
  - Inner thoughts panel parses responses properly
  - Self-update checker works against GitHub API
  - Form submission → Ollama API → response rendering pipeline intact
  - All interactive elements (accordions, buttons, notifications) function
- **🔵 Blue Hat**: Ensure GUI/demo documentation stays in sync with new features
  - New MCP tools must appear in the tool list on the demo page
  - README live demo link must remain functional
  - No placeholders — features shown in GUI must be real, working implementations
- **🟢 Green Hat**: Audit feature parity between backend and demo page
  - Backend features not yet in demo page must be flagged
  - GUI elements referencing removed functionality must be flagged
  - No orphaned UI — every visible element connects to live functionality
- **🟣 Indigo Hat**: Verify frontend-backend wiring after cross-component changes
  - API contract changes propagate to demo page fetch calls
  - Error states from backend changes handled in frontend
  - Setup wizard and install scripts work end-to-end
  - Auto-update checker and version badge are current

---

## 11. Anti-Reduction Checklist (MANDATORY for every Jules PR)

> **PR Completion Gate** — every item below MUST be checked before a PR may be merged.
> A PR that has not passed the CoVE audit (compact or full) **must not be merged**.

- [ ] No files deleted
- [ ] No tests removed or weakened
- [ ] No features simplified or scope-reduced
- [ ] No transparency features hidden or removed
- [ ] No security invariants weakened
- [ ] Coverage >= baseline
- [ ] Test count >= baseline
- [ ] 12-Hat review completed (minimum: ⚫ Black, 🔵 Blue, 🟪 Purple)
- [ ] Commit messages follow hat format
- [ ] Demo page verified functional after all changes (UPKEEP)
- [ ] GUI reflects all current backend capabilities (UPKEEP)
- [ ] README reflects current features, setup instructions, and architecture (UPKEEP)
- [ ] Setup wizard and install scripts work end-to-end (UPKEEP)
- [ ] Auto-update checker and version badge are current (UPKEEP)
- [ ] MCP pipeline wiring intact after changes (UPKEEP)
- [ ] O(1) context bounding verified (snapshot + ≤10 actions) (🪨 Silver)
- [ ] MCP lifecycle gates verified (🔷 Azure)

---

## 12. Companion Context

- **Parent Project**: Sovereign Agentic OS with HLF (`../Sovereign_Agentic_OS_with_HLF/`)
- **ALIGN rules** (R-001 to R-008+): Regex-based safety gates
- **Epistemic modifiers**: [BELIEVE]/[DOUBT] — must not affect security decisions
- **Gas metering**: Resource budgets for agent operations
- **Deployment tiers**: hearth (dev) → forge (staging) → sovereign (prod)
- **Host functions**: READ, WRITE, SPAWN, WEB_SEARCH — tiered capabilities
- **MCP Task Lifecycle**: `request_planning` → `approve_task_completion` → `get_next_task`
- **Infinite CTX Protocol**: O(1) bounded prompts via workspace snapshot + last ≤10 actions
- **CTX-Budget**: Dynamic tier scaling (base 4K → sovereign unlimited). Gas metering for cost visibility

---

**Every agent operating on this repository MUST read and follow this file plus `.github/agents/hats.agent.md`.**

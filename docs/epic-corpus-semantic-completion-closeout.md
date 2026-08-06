# Epic Closeout: Corpus Semantic Completion & Verified Report Path

**Branch (local)**: `feat/corpus-semantic-completion-workflows`  
**Closeout date**: 2026-08-05  
**Remote**: none yet (local git only; no push/PR until a remote exists)  
**Latest HEAD at closeout**: `4c9f245` (`feat: add verified report gap backlog`)

This note is a **local handoff / future PR draft**, not a runtime source of truth.  
Authoritative status remains `docs/roadmap.md` and `specs/README.md`.

---

## 1. Why stop here

The operator loop for verified research reports is complete enough to demo and use:

```text
Latest:      017 deterministic → 018 verified report (Skill)
Historical:  024 gap backlog → 023 suggest next step → 016/015 one action
             → 019 publish (Skill) → 020 catalog / 021 revalidate
```

No remote repository is configured, so epic “PR” cannot be opened yet.  
**Do not add another thin MCP tool only to re-filter coverage.** Next product work should wait for a remote baseline or a clear new capability (not Tool 22-for-filter).

---

## 2. Scope delivered (015 → 024)

| Package | Capability | Surface |
| --- | --- | --- |
| 015 | Standalone semantic summary/review | CLI |
| 016 | Human one-action completion | CLI, MCP, Skill |
| 017 | Latest deterministic readiness | CLI, MCP, Skill |
| 018 | Latest verified report (ack + digest bundle) | CLI, MCP, Skill |
| 019 | Explicit-episode assemble/publish (no LLM/ack when ready) | CLI, MCP, Skill |
| 020 | Catalog list/search/inspect | CLI, MCP Tool 17 |
| 021 | Exact-locator source revalidation | CLI, MCP Tool 18 |
| 022 | Episode coverage (inventory × bundles) | CLI, MCP Tool 19 |
| 023 | Historical next-step suggest + one-confirm Skill | CLI, MCP Tool 20, Skill |
| 024 | Gap backlog (022 `has_bundle=false` projection, B-lite) | CLI, MCP Tool 21 |

**MCP registry at closeout: exact 21 reviewed tools.**

---

## 3. Operator recipes (local)

```powershell
# Gaps
python scripts/list_verified_report_gap_backlog.py gooaye --limit 20

# One episode next step (zero-write)
python scripts/suggest_historical_verified_report_next_step.py gooaye EP672

# Then human-gated confirm via MCP Skills:
# - corpus-episode-completion (016)
# - episode-verified-research-report (019)
# - historical-episode-verified-report-path (023 protocol)
```

Boundaries (unchanged):

- Dry-run first for side effects; one confirmed action per human gate  
- Exact `api_cost_ack` only where LLM is involved  
- No live market API; no investment advice  
- No automatic cache rebuild  
- `.env` local-only, never committed  

---

## 4. Commits on this branch (after `main` @ 014-era base)

Relative to local `main` (`2b2aeea`), this branch includes at least:

```text
dce1acb fix: SPEC 014 workflow selection, confirmed reporting, and review findings
6ef07c5 docs: finalize corpus workflow specifications
af0185b feat: add semantic remediation and episode completion workflows
fe9669a feat: implement SPEC 017 latest episode workflow
d53083c feat: implement SPEC 018 verified research report workflow
586c9fe feat: implement SPEC 019 explicit-episode verified report workflow
1f74a2a feat: add verified report catalog
89f2278 feat: add verified report source revalidation
b17a7ed docs: align Spec Kit and MCP current status
7f1aec0 docs: complete 019-021 Spec Kit registry mappings
4af0c80 feat: add verified report coverage index
f7d5ad6 feat: add historical verified report path
4c9f245 feat: add verified report gap backlog
```

Verify before any future remote publish:

```powershell
python -m pytest
python -m compileall src scripts
git status -sb
```

Last full suite at 024 land: **1191 passed, 7 skipped** (platform capability skips + known pytest-cache ACL warning on this machine).

---

## 5. Local hygiene decisions

| Item | Decision at closeout |
| --- | --- |
| `uv.lock` | **Do not commit.** Project packaging is setuptools/`pyproject.toml`; lock is local-only noise. Prefer gitignore. |
| Remote / PR | Deferred until a remote URL exists. |
| Next package number | **025** (unused). |

---

## 6. Recommended work *after* closeout (ordered)

1. **When remote exists**: push `feat/corpus-semantic-completion-workflows` and open PR using this doc as the body skeleton.  
2. **Batch 3C** — **done** on this branch after epic closeout: runtime ban on direct `OpenAICompatibleProvider(...)` via private factory token.  
3. **Engineering**: split `mcp_server.py` / `test_mcp_server.py` before Tool 22+.  
4. **Product 025+** only with full Spec Kit and a real new capability (e.g. bounded gap+suggest backlog), not another coverage alias.

---

## 7. Future PR title / body sketch

**Title**: `feat: corpus semantic completion through verified-report gap backlog (015–024)`

**Body** (paste-ready skeleton):

```markdown
## Summary
Delivers the corpus semantic completion and verified-research-report operator path:
015–017 readiness/completion, 018–019 report publish, 020–024 catalog/revalidate/coverage/suggest/gap backlog.
MCP registry: exact 21 tools (Tools 17–21 read-query append-only).

## Operator loop
- Latest: 017 → 018
- Historical: 024 gaps → 023 suggest → 016/015 one action → 019 publish
- Audit: 020 catalog, 021 revalidate

## Safety
- Dry-run first; one human-gated confirm; exact api_cost_ack for LLM
- No live market API; no investment advice; no automatic cache rebuild
- .env local-only

## Test plan
- [ ] python -m pytest
- [ ] python -m compileall src scripts
- [ ] scripts/validate_mcp_setup.py (local)
```

---

## 8. Out of scope (still)

Web UI, scheduler, embedding/vector search, live market API, investment advice engine, full-corpus auto-remediation.

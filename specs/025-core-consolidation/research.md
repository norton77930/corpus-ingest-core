# Research: Core Consolidation

## Evidence base (audited 2026-08-08)

- `_is_safe_local_path` defined 4× with divergent behavior: `corpus_episode_completion_workflow_runner.py:1210` (A), `corpus_episode_workflow_runner.py:1119` (B), `corpus_semantic_remediation_runner.py:978` (C, drops final round-trip), `corpus_latest_episode_deterministic_workflow_runner.py:735` (D, rejects all `:` / leading separators — spec 017's deliberate tighter boundary). Shared structural constants are byte-identical across the four.
- Weak `.part` write body copy-pasted in 5 modules (`corpus_audio_download_runner`, `corpus_local_transcription_runner`, `corpus_remediation_runner`, `corpus_episode_workflow_runner:942`, `corpus_episode_intake:280`); strong `write_atomic_audit_report_pair` used by 3 runners and **changes artifact bytes** (injects `audit_report_pair` JSON key + Markdown marker line).
- `mcp_server.py` 1,217 lines / 21 tools; `docs/epic-corpus-semantic-completion-closeout.md:118` already recommends splitting before Tool 22. Registry test resolves tools via `mcp.list_tools()` + `getattr(mcp_server, name)` — a facade with re-exports keeps it green untouched. `tests/test_mcp_server.py` monkeypatches only via `mcp_server.<dependency-module>` aliases (0 direct `setattr(mcp_server, ...)`).
- Doc count drift: `docs/architecture.md:60`=21 vs `:93`=20 (same file); `docs/agent-handoff.md:7,61`=18 vs `:9`=21; `specs/README.md:225`=20; mapping tables stop at 022.
- No `tests/conftest.py`; `_use_tmp_data_dirs` helper copied ~20×; root cause `storage.py:9` `DATA_DIR = Path("data")`.

## Decisions

1. **Per-context strictness, not strictest-union** — D's tighter set and A/B/C's absolute-path acceptance are both spec'd contracts; a shared skeleton with `allow_absolute` preserves each accepted set exactly. C's missing round-trip is preserved and recorded (fixing it = 015 behavior change).
2. **Dedupe the weak writer, do not upgrade** — upgrade changes report bytes → out of scope; post-025 candidate #1.
3. **Facade split, registration by import order** — FastMCP registers at decorator execution; module caching makes duplicate imports no-ops; one `FastMCP` instance total.
4. **Docs: classify claims, don't pin literals** — current-marked claims must equal live-registry N; historical-marked exempt; unmarked fail. Kills the drift class instead of chasing instances.
5. **Opt-in conftest fixture with reflection** — autouse would perturb 926 existing tests; reflection over `storage` keeps coverage complete as dirs are added.

## Rejected

- Strictest-union predicate merge (observable accepted-set changes).
- Sub-packaging / runner-engine extraction in this epic (blast radius, low marginal payoff while the DAG is clean).
- Deleting the ~20 existing `_use_tmp_data_dirs` copies (churn without behavior benefit; allowlist freeze prevents new ones).

## Deviations discovered during implement (converge log)

1. **017 predicate is not strictly tighter** — it also *omits* the path-separator requirement (accepts bare filenames like `corpus-index.json`), so the skeleton gained a second knob `require_separator` (empirically pinned in the characterization table).
2. **Episode intake's writer was a third variant** (JSON via `_write_json`, markdown-only `.part` staging with `finally` cleanup), not one of the byte-identical copies; absorbed as `run_report_io.write_part_staged_markdown`. Weak-family error messages also differ per runner (`{exc}` vs `{type(exc).__name__}`) and stay module-local.
3. **Eight `_write_run_report` definitions exist, not six** — the two strong-protocol runners (015/017) also define it; the boundary guard covers all eight.
4. **One deliberate test edit for the facade split**: `tests/test_mcp_server.py` catalog-delegation test patched `tool_success` as a same-module global of the pre-split `mcp_server`; the white-box patch seam moved with the tool to `mcp_server.mcp_tools_verified_report_queries` (single occurrence in the suite; external behavior unchanged). `tests/test_cache_rebuild_guard.py`'s module allowlist likewise gained the facade/runtime/group module names.
5. **The drift class was worse than audited**: `tests/test_spec_020_*_docs.py` positively pinned the stale "恰好 18 個 reviewed tools" strings (a docs test actively protecting a wrong count — flipped to a negative assertion after the sync), and `docs/verification-matrix.md:21` carried an unaudited "恰好暴露 19 個". The checker's claim regexes therefore allow `MCP`/`reviewed`/`暴露` infixes so such phrasings can no longer hide.
6. **Superseded-pin removal narrowed**: existing correct literal pins (`"exact 21 tools"`, `"exactly 21 tools"`, `"恰 21 個"`) are retained alongside the registry-derived checker instead of being deleted — they are consistent today and removing them is pure cleanup; recorded as post-025 debt.
7. **Post-review facade helper binding fixed**: `mcp_tools_read` and `mcp_tools_side_effect` now access private `mcp_runtime` helpers through module-qualified attributes instead of value-binding them with `from ... import`; public helper imports and existing monkeypatch seams remain unchanged. The facade boundary guard rejects future private-helper value bindings.

## Spec Kit

Full flow: constitution (no amendment) → specify → clarify (session 2026-08-08) → plan → checklist → tasks → analyze → implement → converge.

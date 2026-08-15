# Skill Routing and Protocol Contract

## Routing oracle

This is not a natural-language parser. An upstream component supplies a bounded `Intent` only.

| Intent | Outcome |
| --- | --- |
| one-step advance | 016 `corpus-episode-completion` |
| latest deterministic without semantic/report | 017 `corpus-latest-episode-processing` |
| latest verified report | 018 `latest-episode-verified-research-report` |
| named/historical verified report | 019 `episode-verified-research-report` |
| read-only | no side-effect Skill |
| unknown/conflicting/non-enum | `clarification_required` |

## Normative protocols

1. **016 completion**: preview `action=next`, `confirm=false`; obtain explicit canonical episode plus action approval (semantic work also requires exact acknowledgement); execute one `confirm=true` child action; report and stop. It enforces a closed shape for every 016 event slot: preview, approval, confirmed call, report, and stop reject irrelevant tool, approval, action, confirmation, and preview fields. No second preview, auto-next, retry, or fallback.
2. **017 latest deterministic**: explicit request is one authorization; no preview; exactly one `confirm=true` high-level call. Core may run its bounded deterministic ladder and stops at `ready_for_semantic_summary`. No semantic work, retry, cache rebuild, or fallback.
3. **018 latest verified report**: preview; receive exact expected reference plus exact acknowledgement; execute one `confirm=true` high-level call; Core may deterministically prepare, semantically process/review, research, and publish; report and stop. No retry, partial/force, second latest, or fallback.
4. **019 named report**: preview the exact reference with bounded `PreviewOutcome`. `BLOCKED` means one preview, report, and stop; approval, `confirm=true`, remediation, retry, fallback, or upstream chaining is rejected. `READY` then permits exact-reference approval, one `confirm=true` assemble/publish/reuse call, report, and stop. There is no acknowledgement; no latest/RSS/LLM/upstream chaining/fallback.

The four tool names are `run_corpus_episode_completion_workflow`, `run_corpus_latest_episode_deterministic_workflow`, `run_latest_episode_verified_research_report_workflow`, and `run_episode_verified_research_report_workflow`. This contract preserves the exact 21-tool registry and introduces no Tool 22.
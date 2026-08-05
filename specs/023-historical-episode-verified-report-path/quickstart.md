# Quickstart: Historical Episode Verified Report Path

## Suggest next step

```powershell
python scripts/suggest_historical_verified_report_next_step.py gooaye EP672
```

## Operator flow (Skill)

1. Optionally list gaps: `query_verified_research_report_coverage` with `has_bundle=false`.
2. Pick one `episode_ref` (human choice).
3. Call `suggest_historical_verified_report_next_step`.
4. Follow Skill: preview the recommended tool with `confirm=false`, approve, one `confirm=true`, stop.

## Notes

- Not investment advice.
- Does not revalidate sources (use Tool 18) or batch publish.

# Research: Stock Lens MCP Tool

## Why the capability existed but was unreachable

Spec 001 User Story 3 (P3, recorded there as the capability closest to the
user's long-term goal) shipped as Core plus CLI: `stock_lens.py`,
`gooaye_lens.py`, `scripts/generate_stock_lens_report.py`. It was never added to
the MCP registry, so an agent had no way to call it. The gap was in exposure,
not capability.

## Why side-effect rather than read-query

`generate_stock_lens_report` writes JSON and Markdown under `data/stock-lens/`
and takes `force` to overwrite. Tools 17-21 are read-queries with no `confirm`;
Tools 7-12 are dry-run-first writers. This belongs with the latter.

## Why a fifth group module

Registration order is import order and every prior package promised "Tools 1-N
unchanged". Appending to an existing group would have renumbered the tools after
it. A new group imported last is the only placement that is both append-only and
semantically honest. The facade already documented this as the Tool 22 playbook.

## Why the count change is not a literal sweep

33 files mention 21, but only a few enforce it. The enforcing chain is
`hermes_skill_protocol._registry_tool_names_from_source`, which returns `None`
unless the AST-derived set has the expected size, cascading into the Spec 029
interposer and its tests. Updating literals without the source guard produced a
larger failure set than before the change; the guard has to move first.

## Red line check

`docs/mvp-requirements.md` forbids stock analysis framed as investment advice.
The forbidden output is advice: buy/sell/hold, target price, guaranteed return.
Spec 001 US3 asks for an evidence framework and explicitly requires refusing
advice. The report carries `not_investment_advice` and keeps inference separated
from podcast fact, so it satisfies US3 without crossing the line.

## Observed behaviour on real corpus data

Sampled against the existing gooaye mapping artifacts before finalising:

- A stock named aloud appears under direct evidence with timestamps.
- A stock reachable only through an industry-chain node appears under inferred
  leads with `needs_verification`, never as podcast fact.
- A stock mentioned once in passing yields one thin evidence row and an
  `unverified` ticker rather than a fabricated identity.

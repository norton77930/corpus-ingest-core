# Research: Historical Episode Verified Report Path

## Decisions

1. **Skill-first, not mega-runner** — preserves one-action human control from 016/018/019.
2. **Suggest = composition of previews** — 020-safe digests → 019 `confirm=false` → 016 `confirm=false`; never confirmed work.
3. **Tool 20 read-query** — agents get a stable next-step code without inventing chains.
4. **Coverage (022) is optional input** for episode picking, not embedded auto-batch.

## Rejected

- Single confirm that runs full ladder + publish.
- Automatic second MCP call after success.

## Spec Kit process note (2026-08-05)

Initial delivery compressed clarify/analyze/converge. Retroactive gates recorded in `spec.md` Clarifications, `tasks.md` Phase Formal Spec Kit gates (T008–T010), and this research note.

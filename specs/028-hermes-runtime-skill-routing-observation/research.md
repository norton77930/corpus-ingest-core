# Research: Pinned Hermes Source Capability Boundary

## Fixed identity

The reviewed first-party identity is repository `NousResearch/hermes-agent`, release `Hermes Agent v0.20.0`, annotated tag `v2026.8.3`, tag object `7de39e700d2c329e15d32eb0b96e2f7cdd9fbdb2`, and target commit `3c27eb6234bf91b8ceee9e9071591b31e9b148cb`. The reviewed hooks path is `website/docs/user-guide/features/hooks.md` at blob `be8b9c0caa2792a24bb34dba9400400acdf91eaa`.

## Finding

The tag-pinned first-party contract documents pre/post tool hooks, but it does not provide canonical selected-Skill-to-tool linkage, explicit fallback-used, explicit fallback-not-used, guaranteed Skill/tool correlation, or an official safe fallback positive control. The bounded actual verdict is therefore `BLOCKED_CAPABILITY`.

No raw official page, hook payload, example prompt, arguments, or results is retained. This research is offline and does not re-fetch the source.

# Safety checklist

- [x] No live scenario, Docker, Hermes, listener, inference, `.env`/container env/config/session read, or C6 rerun; only the explicit test-only ephemeral control key is read
- [x] Unknown/default controller modes fail closed and invalid argv is not echoed
- [x] Plugin blocks before execution; only strict `confirm=false` plus `action=next` projects S016, and callback errors cannot weaken it
- [x] Safe evidence and snapshot contain no raw call values, paths, or session material; owner-ledger presence is factory-identity bound
- [x] Spec028 and C6 status are inherited only; neither is upgraded or rerun

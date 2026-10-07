# Safety requirements checklist

Requirements quality only; runtime evidence belongs to implementation-log.md.

- [x] Preview cannot initialize/download models or write files.
- [x] Approved settings bind confirm and worker execution.
- [x] Unavailable GPU never authorizes downgrade/retry.
- [x] Historical artifacts/jobs cannot be relabelled/migrated on reads.
- [x] New completion requires matching recorded settings.
- [x] .env/secrets/provider settings and arbitrary model paths are excluded.
- [x] Host/slot/uncertainty/partial safeguards remain.
- [x] Skill fresh consent, single confirmation and stop remain.
- [x] No automatic notes/Q&A/cache rebuild/advice/market API/deployment.
- [x] Offline, real media and live Hermes evidence are separately labelled.

# Spec 030 — Hermes G1R Offline Remediation Gate

Spec 030 is **static-only**. `PASS_OFFLINE_REMEDIATION` proves only closed offline fact consistency, never runtime proof, execution, activation, observation, or G2/G3a authorization.

The closed plan has ordered operations `CREATE_DISPOSABLE`, `ATTACH_ONE_SHOT_INPUT`, `WAIT_FOR_SAFE_PROJECTION`, `DESTROY_DISPOSABLE`; six tmpfs roles; `ONE_SHOT_STDIN`, `LogSink.NONE`, read-only credential reference, rootfs, zero durable mounts/volumes/host ports, no raw argv/TTY/shell, fresh session, and destroy intents. G2/G3a/live authorization are false and runtime observation is `not_run`.
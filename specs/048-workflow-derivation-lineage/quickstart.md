# Offline acceptance walkthrough

Implemented and offline-verified; see implementation-log.md. Reproduce verification in the existing checkout without creating a branch/worktree/commit. Select this package via SPECIFY_FEATURE_DIRECTORY.

1. Fake-provider generation preview: pair planned_writes length2, metadata_writes length1; assert no mutation/provider construction. Confirm with existing exact ack, inspect matching default-context fixture -> current.
2. Alter each consumed lecture, effective tool ordering/duplicates, rendered recipe/request and each output independently -> stale with the exact ordered roles. Change comments/unused YAML only -> current. Mutate a source during fake provider execution -> resulting receipt records the old consumed value and inspection reports stale.
3. Exercise no pair, legacy complete pair, custom context, partial/orphan pair, malformed/oversized/duplicate-key receipt, foreign identity and unsupported schema. Assert contract states and zero writes/network/provider/cache activity. Insert private sentinel text and assert it never appears in public results.
4. Inject staged pair/receipt writes, hashing, renames, rollback, cleanup and report failures. Check matching old/new tuples or explicit existing recovery state; compare every unrelated file's bytes. Test force collision refusal before provider access.
5. Run Skill offline approval oracle, Tool25 metadata contract, Tool27 unchanged scenarios, registry/facade/setup/docs guards. Verify first27 tool slots/signatures, with Tool28 appended only.

Use .\.venv\Scripts\python.exe -m pytest with a fresh repository-local --basetemp for each run. Then full pytest, compileall -q src scripts, and git diff --check. Record actual commands, exit codes, skip reasons and RED/GREEN evidence in implementation-log.md. No live provider/manual artifact generation is needed.

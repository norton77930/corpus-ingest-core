# Data Model and State Table

**Feature**: 044 | **Status**: design; no stored schema changes.

## Existing Entities

| Entity | Identity/fields | Policy |
| --- | --- | --- |
| Episode | configured podcast, explicit episode, canonical transcript title | existing selection; reject empty/unsafe/reserved aliases |
| Semantic source | canonical `.semantic.md` | learning-notes; existing 2 MiB cap; no transcript provider input |
| Lecture bundle | shared directory; four lecture filenames | owns only 00/03/04/07 |
| Workflow derivation | exact 05/06 filenames | any entry blocks upstream generation, not safe reuse/cover repair |
| `StudyGuideBundleResult` | existing fields/defaults | unchanged dataclass and success/report schema |
| Report pair | existing storage paths | writes on every successful confirm, including reuse; separate from bundle transaction |

Canonical transcript JSON is read for identity metadata. `planned_reads` names artifact dependencies including that JSON; it is not an exhaustive syscall log. No transcript body enters prompts/responses.

## Pure Plan Projection (new, not persisted)

`describe_study_guide_plan(result)` returns `requires_llm: bool` and `report_writes: list[str]`. The boolean is the intersection of full planned write paths with bundle/03, bundle/04, bundle/07. The two report paths use existing storage helpers. No filesystem/provider/profile access or model changes. Preview's existing actual report-path fields stay `None`.

## Action Selection

After identity/profile/source and no-follow safety checks, readable means the existing bounded UTF-8 check. Filesystem/permission errors cause refusal, not overwrite authority.

| Lecture state | force | Any 05/06 | Action | LLM/ack | Writes | Reuses |
| --- | --- | --- | --- | --- | --- | --- |
| four readable roles | false | either | reuse | no | none | 00/03/04/07 |
| 03/04/07 readable; 00 absent or safe regular but fails bounded UTF-8 readability | false | either | cover-only | no | 00 | 03/04/07 |
| any branch generating 03/04/07 | either | yes | refuse | no | none | no success result |
| partial, not cover-only | false | no | refuse partial | no | none | no success result |
| no readable lecture roles | false | no | generate | yes on confirm | 00/03/04/07 | none |
| any allowed state | true | no | generate | yes on confirm | 00/03/04/07 | none |

Confirm writes the two reports after successful actions; preview writes none. Extra files are preserved but are not added as lecture `planned_reuses` or `output_paths`.

## Refusal Precedence

1. Invalid explicit identity.
2. Unsupported/missing profile; unresolved/invalid canonical identity.
3. Unsafe paths or pre-existing sibling `.part`, `.old`, `.wfderive.part`, `.wfderive.old`; all modes refuse.
4. Source restrictions and role readability.
5. Derivation conflict for generation; otherwise existing partial refusal.
6. Confirmed generation only: exact ack, then provider.

Identity metadata may be read to locate source/bundle before step 3. Every file's own safety validation precedes its bytes. Step 3 precedes summary/lecture bodies, provider and writes. Missing normal output parents may be planned, not created in preview.

## Publication State

| Phase | Public bundle | Failure behavior |
| --- | --- | --- |
| preflight/provider/staging | old complete or absent | preserve old bytes, no success report |
| old renamed; before publication | recoverable old backup | rollback if possible; otherwise retain old/staging and report recovery required |
| staging renamed to destination | complete new bundle | committed; no rollback after this point |
| cleanup | complete new bundle | fixed published-cleanup failure, retained remnants |
| report write | complete new or reused bundle | published-report or reused-report failure; no automatic regeneration |

Report failure can leave one report file changed under the existing weak protocol. Do not claim bundle/report transactional atomicity.

## New Typed Error (not persisted)

`StudyGuideBundleStateError(StudyGuideBundleError)` has finite `reason_code`: `invalid_identity`, `unsafe_path`, `recovery_required`, `derivation_conflict`, `publish_failed`, `rollback_failed`, `published_cleanup_failed`, `published_report_failed`, `reused_report_failed`. No body or provider response is attached for serialization. Unknown codes map to a generic safe message.

## Unchanged / Excluded

No manifests, database tables, lineage digest, artifact ladder, summary profiles/prompts, output filenames, report format, provider parameters or workflow-context settings. No source-currentness, ACL/mtime/inode preservation or concurrent-writer guarantee.

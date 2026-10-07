# Implementation Plan: Learning bundle recovery diagnosis
Created2026-10-04. Approved scope: read-only recovery diagnosis; immediate implementation. No branch.
## Technical Context
Python3.11+, FastMCP/PyYAML/pytest already installed. Local filesystem only; five directories;256 direct entries/location; identity64MiB,receipt64KiB,output64MiB. No dependencies. Secure readers/listing and canonical resolver remain public boundary sources.
## Constitution Check
I traceable metadata/finite uncertainty; II new thick Core plus thin MCP; III no side effects or confirm; IV no provider/env/secrets; V non_atomic/publication scope warnings; VI no advice; VII no APIs; VIII no cache writes; IX TDD/full checks/reviews. PASS before and after design; no amendment.
## Phase0 Research
See research.md. Exact observation, receipt semantics, unsafe precedence, original sibling stem and manual-review limits resolved from local evidence.
## Phase1 Design
New src/corpus_ingest_core/learning_bundle_recovery.py contains Core identity resolution, no-follow classification and fixed output mapping. Reuse public resolve_canonical_transcript_asset_paths, storage paths, secure_directory_names/secure_read_bytes,048/049 decode_record and bytes_digest only; no private cross-module imports or generation callbacks. New mcp_tools_learning_recovery.py delegates once, fixed errors, registers last as Tool30. Existing generators/Skills/lineage queries untouched. contracts/recovery.md and data-model.md define exact fields and precedence.
## Delivery phases
Setup -> US1 Core directory observation -> US2 receipt consistency -> US3 wrapper/registry/current docs -> targeted/full/review/converge. One writer; read-only reviewers may inspect independently. No branch/worktree/scripts creating Git objects.
## Planned paths
Create learning_bundle_recovery.py,mcp_tools_learning_recovery.py,tests/test_learning_bundle_recovery.py,tests/test_mcp_learning_bundle_recovery.py,spec050 docs guard/package. Modify mcp_server.py group/re-export, scripts/validate_mcp_setup.py, current docs and count guards. After review, also narrowly correct bounded enumeration in secure_local_snapshot.py and its race/cap tests; public API and accepted-state semantics stay unchanged. Protect all044-049 packages, all current generation/query/codec/Skill modules, pyproject/config/data/cache/history. Baseline compare before completion.
## Complexity Tracking
No shared safety refactor. Review found secure_directory_names used eager os.listdir before applying its existing cap. A narrow secure_local_snapshot.py iterator correction passes the existing max_entries to scandir/islice, preserves its public signature/safety proofs, and stops at cap+1 overflow witness; corresponding race and iteration-cap tests are included. New observer owns finite path metadata classification while relying on existing secure snapshot APIs. Directory rows are independently read; no atomic cross-location claim or repair algorithm.

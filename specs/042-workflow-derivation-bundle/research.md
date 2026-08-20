# Research: Workflow Derivation Bundle

## 1. Separate family vs completing 038

- **Decision**: New family `workflow_derivation`. Lecture family unchanged.
- **Rationale**: Spec 038 Success Criteria treat four readable files as a finished lecture. Folding `05`/`06` into that set would make a complete lecture look unfinished, and would re-open the fabrication trap 038 closed.
- **Alternatives**: One eight-file family (rejected). A second directory tree (rejected; prototype sequence is one folder).

## 2. Operator context source

- **Decision**: YAML at `config/operator_workflow.yaml` with `allowed_tools` list; CLI may pass another path.
- **Rationale**: HANDOFF required operator-supplied context. Hard-coding this machine's tools in Core would lie for the next operator and fail the Copilot-omission test.
- **Alternatives**: Markdown free text (harder to fail-close). Environment variables (easy to leak, not auditable).

## 3. LLM input window

- **Decision**: Send `03`/`04`/`07` bodies plus serialised context. Never transcript, never `00` (cover facts are unused for derivation), never chunk-summary dumps from the semantic file.
- **Rationale**: Principle IV. Lecture is already the evidence-bound reshape of the summary.
- **Alternatives**: Re-read the semantic summary (redundant). Send transcript (forbidden).

## 4. Atomicity

- **Decision**: Copy 038's `.part` directory then replace for the two files only.
- **Rationale**: FR-011. Lecture four must not be part of the replace set.
- **Alternatives**: Write in place (can leave one new and one old file).

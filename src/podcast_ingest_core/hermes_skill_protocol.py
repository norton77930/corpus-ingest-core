"""Closed, assurance-only contracts for the four Hermes-managed Skills.

This module never receives natural-language prompts, invokes MCP tools, or
connects to the Hermes runtime.  It validates only bounded protocol models.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from podcast_ingest_core import hermes_integration


class Skill(str, Enum):
    """The exact four Skills managed by the Hermes integration."""

    COMPLETION = "corpus-episode-completion"
    LATEST_DETERMINISTIC = "corpus-latest-episode-processing"
    LATEST_VERIFIED_REPORT = "latest-episode-verified-research-report"
    NAMED_VERIFIED_REPORT = "episode-verified-research-report"


class Intent(str, Enum):
    """Closed intent categories supplied by an upstream bounded classifier."""

    ONE_STEP_ADVANCE = "one_step_advance"
    LATEST_DETERMINISTIC = "latest_deterministic"
    LATEST_VERIFIED_REPORT = "latest_verified_report"
    NAMED_VERIFIED_REPORT = "named_verified_report"
    READ_ONLY = "read_only"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


class RouteDisposition(str, Enum):
    ROUTE = "route"
    NO_SIDE_EFFECT_SKILL = "no_side_effect_skill"
    CLARIFICATION_REQUIRED = "clarification_required"


@dataclass(frozen=True)
class SkillRoute:
    disposition: RouteDisposition
    skill: Skill | None = None


_ROUTES = {
    Intent.ONE_STEP_ADVANCE: Skill.COMPLETION,
    Intent.LATEST_DETERMINISTIC: Skill.LATEST_DETERMINISTIC,
    Intent.LATEST_VERIFIED_REPORT: Skill.LATEST_VERIFIED_REPORT,
    Intent.NAMED_VERIFIED_REPORT: Skill.NAMED_VERIFIED_REPORT,
}


def expected_skill_for_intent(intent: Intent) -> SkillRoute:
    """Return a bounded routing decision; arbitrary values fail closed."""

    if not isinstance(intent, Intent):
        return SkillRoute(RouteDisposition.CLARIFICATION_REQUIRED)
    if intent is Intent.READ_ONLY:
        return SkillRoute(RouteDisposition.NO_SIDE_EFFECT_SKILL)
    skill = _ROUTES.get(intent)
    if skill is None:
        return SkillRoute(RouteDisposition.CLARIFICATION_REQUIRED)
    return SkillRoute(RouteDisposition.ROUTE, skill)


class Tool(str, Enum):
    """The only high-level tools permitted by each managed Skill."""

    COMPLETION = "run_corpus_episode_completion_workflow"
    LATEST_DETERMINISTIC = "run_corpus_latest_episode_deterministic_workflow"
    LATEST_VERIFIED_REPORT = "run_latest_episode_verified_research_report_workflow"
    NAMED_VERIFIED_REPORT = "run_episode_verified_research_report_workflow"


class FailureCode(str, Enum):
    NONE = "none"
    INVALID_ARTIFACT_SET = "invalid_artifact_set"
    MISSING_REQUIRED_CLAUSE = "missing_required_clause"
    UNORDERED_CLAUSES = "unordered_clauses"
    INVALID_EVENT_SEQUENCE = "invalid_event_sequence"
    INVALID_CONFIRM = "invalid_confirm"
    CALL_BUDGET_EXCEEDED = "call_budget_exceeded"
    INVALID_EVIDENCE = "invalid_evidence"
    INVALID_MANAGED_ALLOWLIST = "invalid_managed_allowlist"
    MALFORMED_ARTIFACT = "malformed_artifact"
    WRONG_TOOL_MAPPING = "wrong_tool_mapping"
    INVALID_REGISTRY_TOOLSET = "invalid_registry_toolset"


@dataclass(frozen=True)
class SkillArtifact:
    """A repository Skill source supplied only to the offline contract checker."""

    skill: Skill
    text: str


@dataclass(frozen=True)
class SkillToolBinding:
    skill: Skill
    tool: Tool


@dataclass(frozen=True)
class ArtifactValidation:
    ok: bool
    failure: FailureCode
    bindings: tuple[SkillToolBinding, ...]
    managed_allowlist_ok: bool = False


@dataclass(frozen=True)
class _SkillContract:
    tool: Tool
    clauses: tuple[str, ...]


_SKILL_CONTRACTS = {
    Skill.COMPLETION: _SkillContract(
        Tool.COMPLETION,
        (
            "name: corpus-episode-completion",
            "run_corpus_episode_completion_workflow",
            "`action=next` and `confirm=false`",
            "canonical episode reference",
            "Ask one explicit approval question",
            "`confirm=true`",
            "exact acknowledgement text",
            "Report the bounded result and stop",
            "Do not start another preview or action",
            "Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, or autonomous loop as a fallback.",
        ),
    ),
    Skill.LATEST_DETERMINISTIC: _SkillContract(
        Tool.LATEST_DETERMINISTIC,
        (
            "name: corpus-latest-episode-processing",
            "one-time execution authorization",
            "run_corpus_latest_episode_deterministic_workflow",
            "exactly once with `confirm=true`",
            "Report the metadata-only result once and stop",
            "ready_for_semantic_summary",
            "Do not call with `confirm=false` before the confirmed call",
            "Do not call this tool more than once",
            "Do not use a terminal, CLI, another side-effect tool, cron/scheduler, retry, batch, cache rebuild, or autonomous loop as a fallback.",
            "Do not invoke semantic summary or semantic review.",
            "Do not resolve a new latest episode during the same request.",
        ),
    ),
    Skill.LATEST_VERIFIED_REPORT: _SkillContract(
        Tool.LATEST_VERIFIED_REPORT,
        (
            "name: latest-episode-verified-research-report",
            "run_latest_episode_verified_research_report_workflow",
            "`confirm=false`",
            "canonical episode reference",
            "exact previewed `expected_episode_ref`",
            "and the exact\n   `api_cost_ack`",
            "`confirm=true`",
            "Report the bounded completion",
            "Do not use CLI or a terminal fallback.",
            "Do not retry",
            "scheduler, schedule, loop, force,",
            "select partial mode",
            "rebuild cache",
            "call another side-effect tool",
            "resolve a\nsecond latest episode",
            "call an external live provider",
            "Do not replace the\npreview/approval protocol with autonomous execution.",
        ),
    ),
    Skill.NAMED_VERIFIED_REPORT: _SkillContract(
        Tool.NAMED_VERIFIED_REPORT,
        (
            "name: episode-verified-research-report",
            "run_episode_verified_research_report_workflow",
            "`confirm=false`",
            "exact `episode_ref`",
            "If preview\n   is `blocked`, list missing/stale roles and stop.",
            "explicit approval of that exact `episode_ref`",
            "There is **no** `api_cost_ack`",
            "`confirm=true`",
            "Report the `completed`, `reused`, `blocked`, or error outcome once and stop",
            "Do not use CLI or a terminal fallback",
            "Do not retry, schedule, loop, force,",
            "partial mode",
            "rebuild cache",
            "call 015/016/017/018",
            "call LLM tools",
            "resolve\nRSS latest",
            "provide investment advice",
            "do not auto-chain remediation.",
        ),
    ),
}


def canonical_skill_bindings() -> tuple[SkillToolBinding, ...]:
    """Return the single canonical managed Skill-to-tool projection."""

    return tuple(
        SkillToolBinding(skill, _SKILL_CONTRACTS[skill].tool) for skill in Skill
    )


def _managed_allowlist_is_exact(managed_skills: object) -> bool:
    return isinstance(managed_skills, tuple) and managed_skills == tuple(
        skill.value for skill in Skill
    )


def _has_portable_frontmatter(artifact: SkillArtifact) -> bool:
    if not isinstance(artifact.text, str):
        return False
    lines = artifact.text.splitlines()
    return (
        len(lines) >= 4
        and lines[0] == "---"
        and lines[1] == f"name: {artifact.skill.value}"
        and lines[2].startswith("description: ")
        and lines[2] != "description: "
        and lines[3] == "---"
    )


_MCP_TOOL_SOURCE_FILES = (
    "mcp_tools_read.py",
    "mcp_tools_side_effect.py",
    "mcp_tools_corpus_workflows.py",
    "mcp_tools_verified_report_queries.py",
    "mcp_tools_stock_lens.py",
    "mcp_tools_x_video.py",
    "mcp_tools_youtube_video.py",
)
def _is_direct_mcp_tool_reference(expression: ast.AST) -> bool:
    return (
        isinstance(expression, ast.Attribute)
        and expression.attr == "tool"
        and isinstance(expression.value, ast.Name)
        and expression.value.id == "mcp"
    )


def _registry_name_from_direct_mcp_tool_decorator(
    decorator: ast.Call,
    function_name: str,
) -> str | None:
    if decorator.args or any(keyword.arg is None for keyword in decorator.keywords):
        return None
    name_keywords = [
        keyword for keyword in decorator.keywords if keyword.arg == "name"
    ]
    if len(name_keywords) > 1:
        return None
    if not name_keywords:
        return function_name
    value = name_keywords[0].value
    if not isinstance(value, ast.Constant) or type(value.value) is not str or not value.value:
        return None
    return value.value


def _tool_names_from_python_source(source: object) -> frozenset[str] | None:
    """Collect only unambiguous top-level ``@mcp.tool(...)`` names without execution."""

    if not isinstance(source, str):
        return None
    try:
        module = ast.parse(source)
    except SyntaxError:
        return None

    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "tool"
        for node in ast.walk(module)
    ):
        return None

    names: list[str] = []
    accepted_decorator_reference_ids: set[int] = set()
    accepted_decorator_call_ids: set[int] = set()
    accepted_mcp_name_ids: set[int] = set()
    for node in module.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        mcp_tool_decorators = [
            decorator
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and _is_direct_mcp_tool_reference(decorator.func)
        ]
        if len(mcp_tool_decorators) > 1:
            return None
        if not mcp_tool_decorators:
            continue
        decorator = mcp_tool_decorators[0]
        registry_name = _registry_name_from_direct_mcp_tool_decorator(
            decorator,
            node.name,
        )
        if registry_name is None:
            return None
        names.append(registry_name)
        accepted_decorator_reference_ids.add(id(decorator.func))
        accepted_decorator_call_ids.add(id(decorator))
        accepted_mcp_name_ids.add(id(decorator.func.value))

    for function_node in ast.walk(module):
        if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if function_node.decorator_list and not any(
            id(decorator) in accepted_decorator_call_ids
            for decorator in function_node.decorator_list
        ):
            return None
        for decorator in function_node.decorator_list:
            for decorator_node in ast.walk(decorator):
                if (
                    isinstance(decorator_node, ast.Call)
                    and isinstance(decorator_node.func, ast.Attribute)
                    and decorator_node.func.attr == "tool"
                    and id(decorator_node) not in accepted_decorator_call_ids
                ):
                    return None
                if (
                    isinstance(decorator_node, ast.Name)
                    and decorator_node.id == "mcp"
                    and id(decorator_node) not in accepted_mcp_name_ids
                ):
                    return None

    tool_reference_ids = {
        id(node)
        for node in ast.walk(module)
        if isinstance(node, ast.Attribute) and node.attr == "tool"
    }
    if tool_reference_ids != accepted_decorator_reference_ids:
        return None
    mcp_name_ids = {
        id(node)
        for node in ast.walk(module)
        if isinstance(node, ast.Name) and node.id == "mcp"
    }
    if mcp_name_ids != accepted_mcp_name_ids:
        return None
    if any(
        isinstance(node, ast.Attribute) and node.attr == "mcp"
        for node in ast.walk(module)
    ):
        return None
    if len(names) != len(set(names)):
        return None
    return frozenset(names)


def _registry_tool_names_from_source() -> frozenset[str] | None:
    """Read AST-derived decorator names without importing the MCP runtime."""

    names: set[str] = set()
    definition_count = 0
    try:
        for filename in _MCP_TOOL_SOURCE_FILES:
            source = Path(__file__).with_name(filename).read_text(encoding="utf-8")
            source_names = _tool_names_from_python_source(source)
            if source_names is None or names.intersection(source_names):
                return None
            definition_count += len(source_names)
            names.update(source_names)
    except OSError:
        return None
    if definition_count != len(names):
        return None
    source_tool_names = frozenset(names)
    if (
        len(source_tool_names) != 24
        or not frozenset(tool.value for tool in Tool) <= source_tool_names
    ):
        return None
    return source_tool_names


def canonical_registry_tool_names_from_source() -> frozenset[str] | None:
    """Return the offline AST-derived exact-24 registry without MCP import."""

    return _registry_tool_names_from_source()


def _resolve_registry_tool_names(
    registry_tool_names: frozenset[str] | None,
) -> frozenset[str] | None:
    source_tool_names = canonical_registry_tool_names_from_source()
    if source_tool_names is None:
        return None
    if registry_tool_names is None:
        return source_tool_names
    if (
        not isinstance(registry_tool_names, frozenset)
        or not all(type(name) is str for name in registry_tool_names)
        or registry_tool_names != source_tool_names
    ):
        return None
    return source_tool_names


def validate_skill_artifacts(
    artifacts: tuple[SkillArtifact, ...],
    *,
    managed_skills: tuple[str, ...] | None = None,
    registry_tool_names: frozenset[str] | None = None,
) -> ArtifactValidation:
    """Validate managed Skill sources without returning source content or values."""

    actual_managed_skills = (
        hermes_integration.MANAGED_SKILLS if managed_skills is None else managed_skills
    )
    managed_allowlist_ok = _managed_allowlist_is_exact(actual_managed_skills)
    if not managed_allowlist_ok:
        return ArtifactValidation(
            False, FailureCode.INVALID_MANAGED_ALLOWLIST, (), False
        )
    resolved_registry_tool_names = _resolve_registry_tool_names(registry_tool_names)
    if resolved_registry_tool_names is None:
        return ArtifactValidation(
            False, FailureCode.INVALID_REGISTRY_TOOLSET, (), True
        )
    if (
        not isinstance(artifacts, tuple)
        or len(artifacts) != len(Skill)
        or any(not isinstance(artifact, SkillArtifact) for artifact in artifacts)
    ):
        return ArtifactValidation(False, FailureCode.INVALID_ARTIFACT_SET, (), True)
    if any(not isinstance(artifact.skill, Skill) for artifact in artifacts):
        return ArtifactValidation(False, FailureCode.MALFORMED_ARTIFACT, (), True)
    if {artifact.skill for artifact in artifacts} != set(Skill):
        return ArtifactValidation(False, FailureCode.INVALID_ARTIFACT_SET, (), True)

    for artifact in artifacts:
        if not _has_portable_frontmatter(artifact):
            return ArtifactValidation(False, FailureCode.MALFORMED_ARTIFACT, (), True)
        contract = _SKILL_CONTRACTS[artifact.skill]
        other_registry_tools = resolved_registry_tool_names - {contract.tool.value}
        if any(tool_name in artifact.text for tool_name in other_registry_tools):
            return ArtifactValidation(False, FailureCode.WRONG_TOOL_MAPPING, (), True)
        positions = [artifact.text.find(clause) for clause in contract.clauses]
        if any(position < 0 for position in positions):
            return ArtifactValidation(False, FailureCode.MISSING_REQUIRED_CLAUSE, (), True)
        if positions != sorted(positions):
            return ArtifactValidation(False, FailureCode.UNORDERED_CLAUSES, (), True)
    return ArtifactValidation(True, FailureCode.NONE, canonical_skill_bindings(), True)


class EventKind(str, Enum):
    APPROVAL = "approval"
    CALL = "call"
    REPORT = "report"
    STOP = "stop"
    FALLBACK = "fallback"
    RETRY = "retry"


class Approval(str, Enum):
    NONE = "none"
    EXPLICIT = "explicit"
    EXACT_ACK = "exact_ack"
    EXACT_REFERENCE = "exact_reference"
    EXACT_REFERENCE_AND_ACK = "exact_reference_and_ack"
    REJECTED = "rejected"


class PreviewOutcome(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


class CompletionAction(str, Enum):
    NEXT = "next"
    DETERMINISTIC = "deterministic"
    SEMANTIC_SUMMARY = "semantic_summary"
    SEMANTIC_REVIEW = "semantic_review"


@dataclass(frozen=True)
class ProtocolEvent:
    """A bounded event projection, never a raw Hermes event or argument payload."""

    kind: EventKind
    tool: Tool | None = None
    confirm: object = False
    approval: Approval = Approval.NONE
    action: CompletionAction | None = None
    preview_outcome: PreviewOutcome | None = None


@dataclass(frozen=True)
class SequenceVerification:
    skill: Skill | None
    ok: bool
    failure: FailureCode
    observed_call_count: int
    call_budget: int


_CALL_BUDGETS = {
    Skill.COMPLETION: 2,
    Skill.LATEST_DETERMINISTIC: 1,
    Skill.LATEST_VERIFIED_REPORT: 2,
    Skill.NAMED_VERIFIED_REPORT: 2,
}
_SUCCESS_CALL_COUNTS = {
    Skill.COMPLETION: frozenset({2}),
    Skill.LATEST_DETERMINISTIC: frozenset({1}),
    Skill.LATEST_VERIFIED_REPORT: frozenset({2}),
    Skill.NAMED_VERIFIED_REPORT: frozenset({1, 2}),
}


def _sequence_result(
    skill: Skill | None,
    ok: bool,
    failure: FailureCode,
    call_count: int,
    budget: int,
) -> SequenceVerification:
    return SequenceVerification(skill, ok, failure, min(call_count, 3), budget)


def _event_shape_is_closed(event: object) -> bool:
    return (
        isinstance(event, ProtocolEvent)
        and isinstance(event.kind, EventKind)
        and (event.tool is None or isinstance(event.tool, Tool))
        and type(event.confirm) is bool
        and isinstance(event.approval, Approval)
        and (event.action is None or isinstance(event.action, CompletionAction))
        and (
            event.preview_outcome is None
            or isinstance(event.preview_outcome, PreviewOutcome)
        )
    )


def _completion_sequence_is_valid(events: tuple[ProtocolEvent, ...]) -> bool:
    if len(events) != 5:
        return False
    preview, approval, confirmed, report, stop = events
    if (
        preview.kind is not EventKind.CALL
        or preview.tool is not Tool.COMPLETION
        or preview.confirm is not False
        or preview.approval is not Approval.NONE
        or preview.action is not CompletionAction.NEXT
        or preview.preview_outcome is not None
        or approval.kind is not EventKind.APPROVAL
        or approval.tool is not None
        or approval.confirm is not False
        or approval.action is not None
        or approval.preview_outcome is not None
        or confirmed.kind is not EventKind.CALL
        or confirmed.tool is not Tool.COMPLETION
        or confirmed.confirm is not True
        or confirmed.approval is not Approval.NONE
        or confirmed.action in (None, CompletionAction.NEXT)
        or confirmed.preview_outcome is not None
        or report.kind is not EventKind.REPORT
        or report.tool is not None
        or report.confirm is not False
        or report.approval is not Approval.NONE
        or report.action is not None
        or report.preview_outcome is not None
        or stop.kind is not EventKind.STOP
        or stop.tool is not None
        or stop.confirm is not False
        or stop.approval is not Approval.NONE
        or stop.action is not None
        or stop.preview_outcome is not None
    ):
        return False
    required_approval = (
        Approval.EXACT_ACK
        if confirmed.action is CompletionAction.SEMANTIC_SUMMARY
        else Approval.EXPLICIT
    )
    return approval.approval is required_approval


def _fixed_sequence_is_valid(
    events: tuple[ProtocolEvent, ...],
    tool: Tool,
    approval: Approval,
    *,
    requires_preview: bool,
    preview_outcome: PreviewOutcome | None = None,
) -> bool:
    if requires_preview:
        expected = (
            (EventKind.CALL, tool, False, Approval.NONE, preview_outcome),
            (EventKind.APPROVAL, None, False, approval, None),
            (EventKind.CALL, tool, True, Approval.NONE, None),
            (EventKind.REPORT, None, False, Approval.NONE, None),
            (EventKind.STOP, None, False, Approval.NONE, None),
        )
    else:
        expected = (
            (EventKind.APPROVAL, None, False, approval, None),
            (EventKind.CALL, tool, True, Approval.NONE, None),
            (EventKind.REPORT, None, False, Approval.NONE, None),
            (EventKind.STOP, None, False, Approval.NONE, None),
        )
    return len(events) == len(expected) and all(
        (
            event.kind,
            event.tool,
            event.confirm,
            event.approval,
            event.preview_outcome,
        )
        == required
        and event.action is None
        for event, required in zip(events, expected, strict=True)
    )


def _named_blocked_sequence_is_valid(events: tuple[ProtocolEvent, ...]) -> bool:
    if len(events) != 3:
        return False
    preview, report, stop = events
    return (
        preview.kind is EventKind.CALL
        and preview.tool is Tool.NAMED_VERIFIED_REPORT
        and preview.confirm is False
        and preview.approval is Approval.NONE
        and preview.action is None
        and preview.preview_outcome is PreviewOutcome.BLOCKED
        and report.kind is EventKind.REPORT
        and report.tool is None
        and report.confirm is False
        and report.approval is Approval.NONE
        and report.action is None
        and report.preview_outcome is None
        and stop.kind is EventKind.STOP
        and stop.tool is None
        and stop.confirm is False
        and stop.approval is Approval.NONE
        and stop.action is None
        and stop.preview_outcome is None
    )


def verify_event_sequence(
    skill: Skill,
    events: tuple[ProtocolEvent, ...],
) -> SequenceVerification:
    """Verify the per-Skill reducer and bounded high-level call budget."""

    if not isinstance(skill, Skill):
        return _sequence_result(None, False, FailureCode.INVALID_EVENT_SEQUENCE, 0, 0)
    budget = _CALL_BUDGETS[skill]
    if not isinstance(events, tuple) or not all(_event_shape_is_closed(event) for event in events):
        return _sequence_result(skill, False, FailureCode.INVALID_CONFIRM, 0, budget)
    call_count = sum(event.kind is EventKind.CALL for event in events)
    if call_count > budget:
        return _sequence_result(
            skill, False, FailureCode.CALL_BUDGET_EXCEEDED, call_count, budget
        )
    if skill is Skill.COMPLETION:
        valid = _completion_sequence_is_valid(events)
    elif skill is Skill.LATEST_DETERMINISTIC:
        valid = _fixed_sequence_is_valid(
            events, Tool.LATEST_DETERMINISTIC, Approval.EXPLICIT, requires_preview=False
        )
    elif skill is Skill.LATEST_VERIFIED_REPORT:
        valid = _fixed_sequence_is_valid(
            events,
            Tool.LATEST_VERIFIED_REPORT,
            Approval.EXACT_REFERENCE_AND_ACK,
            requires_preview=True,
        )
    else:
        valid = _named_blocked_sequence_is_valid(events) or _fixed_sequence_is_valid(
            events,
            Tool.NAMED_VERIFIED_REPORT,
            Approval.EXACT_REFERENCE,
            requires_preview=True,
            preview_outcome=PreviewOutcome.READY,
        )
    return _sequence_result(
        skill,
        valid,
        FailureCode.NONE if valid else FailureCode.INVALID_EVENT_SEQUENCE,
        call_count,
        budget,
    )


@dataclass(frozen=True)
class ContractEvidence:
    """Safe, fixed-shape evidence without source text or raw event content."""

    route: RouteDisposition
    skill: Skill | None
    artifact_ok: bool
    managed_allowlist_ok: bool
    sequence_ok: bool
    failure: FailureCode
    call_count: int

    def to_dict(self) -> dict[str, str | bool | int | None]:
        route = self.route if isinstance(self.route, RouteDisposition) else RouteDisposition.CLARIFICATION_REQUIRED
        skill = self.skill if isinstance(self.skill, Skill) else None
        failure = self.failure if isinstance(self.failure, FailureCode) else FailureCode.INVALID_EVIDENCE
        artifact_ok = self.artifact_ok if type(self.artifact_ok) is bool else False
        managed_allowlist_ok = (
            self.managed_allowlist_ok
            if type(self.managed_allowlist_ok) is bool
            else False
        )
        sequence_ok = self.sequence_ok if type(self.sequence_ok) is bool else False
        call_count = self.call_count if type(self.call_count) is int else 0
        return {
            "schema_version": "hermes-skill-protocol-evidence-v1",
            "ok": (
                failure is FailureCode.NONE
                and artifact_ok
                and managed_allowlist_ok
                and sequence_ok
            ),
            "route": route.value,
            "skill": skill.value if skill is not None else None,
            "artifact_ok": artifact_ok,
            "managed_allowlist_ok": managed_allowlist_ok,
            "sequence_ok": sequence_ok,
            "failure_code": failure.value,
            "call_count": min(max(call_count, 0), 3),
            "hermes_runtime_observation": "not_evaluated",
        }


def build_contract_evidence(
    route: SkillRoute,
    artifacts: ArtifactValidation,
    sequence: SequenceVerification,
) -> ContractEvidence:
    """Compose consistent bounded evidence and discard all input payload content."""

    invalid = ContractEvidence(
        RouteDisposition.CLARIFICATION_REQUIRED,
        None,
        False,
        False,
        False,
        FailureCode.INVALID_EVIDENCE,
        0,
    )
    if (
        not isinstance(route, SkillRoute)
        or not isinstance(route.disposition, RouteDisposition)
        or (route.skill is not None and not isinstance(route.skill, Skill))
    ):
        return invalid
    artifact_is_closed = (
        isinstance(artifacts, ArtifactValidation)
        and type(artifacts.ok) is bool
        and isinstance(artifacts.failure, FailureCode)
        and isinstance(artifacts.bindings, tuple)
        and artifacts.bindings == canonical_skill_bindings()
        and type(artifacts.managed_allowlist_ok) is bool
        and artifacts.ok is True
        and artifacts.failure is FailureCode.NONE
        and artifacts.managed_allowlist_ok is True
    )
    sequence_is_closed = (
        isinstance(sequence, SequenceVerification)
        and isinstance(sequence.skill, Skill)
        and type(sequence.ok) is bool
        and isinstance(sequence.failure, FailureCode)
        and type(sequence.observed_call_count) is int
        and type(sequence.call_budget) is int
        and sequence.call_budget in _CALL_BUDGETS.values()
        and 0 <= sequence.observed_call_count <= sequence.call_budget
        and sequence.ok is True
        and sequence.failure is FailureCode.NONE
    )
    if not artifact_is_closed or not sequence_is_closed:
        return invalid
    if (
        route.disposition is not RouteDisposition.ROUTE
        or route.skill is None
        or sequence.skill is not route.skill
        or sequence.call_budget != _CALL_BUDGETS[route.skill]
        or sequence.observed_call_count not in _SUCCESS_CALL_COUNTS[route.skill]
    ):
        return invalid
    return ContractEvidence(
        route.disposition,
        route.skill,
        True,
        True,
        True,
        FailureCode.NONE,
        sequence.observed_call_count,
    )

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict

import pytest

ACK = (
    "I understand this may call an external LLM API, send transcript text outside this machine, "
    "and incur costs."
)


def _workflow_result(*, dry_run: bool, confirm: bool):
    from corpus_ingest_core.models import ResearchWorkflowResult, ResearchWorkflowStep

    return ResearchWorkflowResult(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query="台積電",
        workflow_status="planned" if dry_run else "completed",
        dry_run=dry_run,
        requires_confirmation=dry_run,
        requires_api_cost_ack=dry_run,
        required_acknowledgement=ACK if dry_run else None,
        transcript_status="valid",
        steps=[
            ResearchWorkflowStep(
                name="generate_stock_lens_synthesis_report",
                status="planned" if dry_run else "completed",
                action="Run stock lens LLM synthesis.",
                planned_reads=["data/stock-lens/gooaye/台積電.stock-lens.json"],
                planned_writes=[
                    "data/stock-lens/gooaye/台積電.stock-lens-synthesis.json",
                    "data/stock-lens/gooaye/台積電.stock-lens-synthesis.md",
                ],
                risks=["Calls an external LLM API", "May incur API cost risk"],
                generated_artifacts=[]
                if dry_run
                else ["data/stock-lens/gooaye/台積電.stock-lens-synthesis.json"],
                reused_artifacts=[],
            )
        ],
        planned_reads=["data/transcripts/gooaye/EP672__title.json"],
        planned_writes=["data/stock-lens/gooaye/台積電.stock-lens-synthesis.json"],
        written_artifacts=[] if dry_run else ["data/stock-lens/gooaye/台積電.stock-lens-synthesis.json"],
        generated_artifacts=[] if dry_run else ["data/stock-lens/gooaye/台積電.stock-lens-synthesis.json"],
        reused_artifacts=[],
        external_api_steps=["semantic_summarize_episode", "generate_stock_lens_synthesis_report"],
        warnings=["Cache may be stale. Run rebuild_cache manually after workflow completion."],
        not_investment_advice=True,
    )


def test_research_llm_smoke_dry_run_calls_workflow_without_confirm(
    monkeypatch, tmp_path, capsys
):
    from scripts import run_research_llm_smoke

    config_path = tmp_path / "llm_profiles.yaml"
    config_path.write_text(
        """
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
""".strip(),
        encoding="utf-8",
    )
    calls = []

    def fake_workflow(*args, **kwargs):
        calls.append((args, kwargs))
        return _workflow_result(dry_run=True, confirm=kwargs["confirm"])

    monkeypatch.setattr(run_research_llm_smoke, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--llm-profile",
            "gb10",
            "--llm-profile-path",
            str(config_path),
        ],
    )

    run_research_llm_smoke.main()

    payload = json.loads(capsys.readouterr().out)
    assert calls[0][1]["confirm"] is False
    assert calls[0][1]["include_stock_lens_synthesis"] is True
    assert calls[0][1]["include_external_data_verification"] is True
    assert calls[0][1]["include_semantic_summary"] is False
    assert calls[0][1]["include_semantic_context_in_synthesis"] is False
    assert calls[0][1]["semantic_model"] == "GB10"
    assert calls[0][1]["semantic_base_url"] == "https://api.example.com/v1"
    assert calls[0][1]["semantic_api_key_env"] == "API_KEY"
    assert calls[0][1]["synthesis_model"] == "GB10"
    assert calls[0][1]["synthesis_base_url"] == "https://api.example.com/v1"
    assert calls[0][1]["synthesis_api_key_env"] == "API_KEY"
    assert payload["dry_run"] is True
    assert payload["requires_api_cost_ack"] is True
    assert payload["codex_session_backend_supported"] is False
    assert payload["llm_runtime"] == "openai-compatible /chat/completions"
    assert payload["api_key_value_read"] is False
    assert payload["provider_config"]["llm_profile"] == "gb10"
    assert payload["provider_config"]["model"] == "GB10"
    assert "API_KEY" in payload["provider_config"]["api_key_env"]
    assert "secret-value" not in capsys.readouterr().out


def test_research_llm_smoke_confirm_requires_exact_ack_before_workflow(
    monkeypatch, capsys
):
    from scripts import run_research_llm_smoke

    monkeypatch.setattr(
        run_research_llm_smoke,
        "run_research_workflow",
        lambda *args, **kwargs: pytest.fail("workflow must not run without exact ack"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--confirm",
            "--api-cost-ack",
            "wrong",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        run_research_llm_smoke.main()

    assert exc_info.value.code == 1
    assert "exact api_cost_ack" in capsys.readouterr().err


def test_research_llm_smoke_confirm_passes_expected_workflow_options(
    monkeypatch, capsys
):
    from scripts import run_research_llm_smoke

    import corpus_ingest_core.stock_lens_synthesis as synthesis

    calls = []

    def fake_workflow(*args, **kwargs):
        calls.append((args, kwargs))
        calls.append(("debug_env", os.environ.get(synthesis.DEBUG_OUTPUT_PATH_ENV)))
        return _workflow_result(dry_run=False, confirm=kwargs["confirm"])

    monkeypatch.setattr(run_research_llm_smoke, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--confirm",
            "--force",
            "--allow-partial",
            "--include-semantic-summary",
            "--include-semantic-context",
            "--semantic-context-max-chars",
            "9000",
            "--api-cost-ack",
            ACK,
            "--provider",
            "openai-compatible",
            "--model",
            "test-model",
            "--base-url",
            "https://example.test/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--max-prompt-chars",
            "12000",
            "--debug-llm-output",
        ],
    )

    run_research_llm_smoke.main()

    payload = json.loads(capsys.readouterr().out)
    kwargs = calls[0][1]
    assert kwargs["confirm"] is True
    assert kwargs["force"] is True
    assert kwargs["allow_partial"] is True
    assert kwargs["include_semantic_summary"] is True
    assert kwargs["include_semantic_context_in_synthesis"] is True
    assert kwargs["include_stock_lens_synthesis"] is True
    assert kwargs["include_external_data_verification"] is True
    assert kwargs["api_cost_ack"] == ACK
    assert kwargs["semantic_provider"] == "openai-compatible"
    assert kwargs["semantic_model"] == "test-model"
    assert kwargs["semantic_base_url"] == "https://example.test/v1"
    assert kwargs["semantic_api_key_env"] == "TEST_API_KEY"
    assert kwargs["synthesis_provider"] == "openai-compatible"
    assert kwargs["synthesis_model"] == "test-model"
    assert kwargs["synthesis_base_url"] == "https://example.test/v1"
    assert kwargs["synthesis_api_key_env"] == "TEST_API_KEY"
    assert kwargs["synthesis_max_prompt_chars"] == 12000
    assert kwargs["synthesis_semantic_context_max_chars"] == 9000
    debug_path = calls[1][1]
    assert debug_path.endswith(".llm-output.md")
    assert "gooaye" in debug_path
    assert "EP672" in debug_path
    assert "台積電" in debug_path
    assert payload["dry_run"] is False
    assert payload["workflow"]["workflow_status"] == "completed"
    assert payload["debug_llm_output_path"] == debug_path


def test_research_llm_smoke_stdout_does_not_expose_sensitive_or_raw_text(
    monkeypatch, capsys
):
    from scripts import run_research_llm_smoke

    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    monkeypatch.setattr(
        run_research_llm_smoke,
        "run_research_workflow",
        lambda *args, **kwargs: _workflow_result(dry_run=True, confirm=False),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--api-key-env",
            "TEST_API_KEY",
        ],
    )

    run_research_llm_smoke.main()

    output = capsys.readouterr().out
    assert "secret-value" not in output
    assert "traceback" not in output.lower()
    assert "今天聊到台積電" not in output
    assert "raw transcript" not in output.lower()
    assert json.loads(output)["provider_config"]["api_key_value_exposed"] is False


def test_research_llm_smoke_loads_env_file(monkeypatch, tmp_path, capsys):
    from scripts import run_research_llm_smoke

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=file-model\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    captured = {}

    def fake_workflow(*args, **kwargs):
        captured["api_key"] = os.environ.get("API_KEY")
        captured["model"] = os.environ.get("MODEL")
        captured["kwargs"] = kwargs
        return _workflow_result(dry_run=True, confirm=False)

    monkeypatch.setattr(run_research_llm_smoke, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--env-file",
            str(env_path),
            "--api-key-env",
            "API_KEY",
        ],
    )

    run_research_llm_smoke.main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert captured["api_key"] == "secret-value"
    assert captured["model"] == "file-model"
    assert captured["kwargs"]["semantic_api_key_env"] == "API_KEY"
    assert payload["local_env"]["env_file_loaded"] is True
    assert payload["local_env"]["loaded_env_var_names"] == ["API_KEY", "MODEL"]
    assert "secret-value" not in output


def test_research_llm_smoke_no_env_file_disables_loading(monkeypatch, tmp_path, capsys):
    from scripts import run_research_llm_smoke

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("API_KEY", raising=False)

    def fake_workflow(*args, **kwargs):
        assert os.environ.get("API_KEY") is None
        return _workflow_result(dry_run=True, confirm=False)

    monkeypatch.setattr(run_research_llm_smoke, "run_research_workflow", fake_workflow)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--no-env-file",
        ],
    )

    run_research_llm_smoke.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["local_env"]["env_file_loaded"] is False
    assert payload["local_env"]["loaded_env_var_names"] == []


def test_research_llm_smoke_jsonable_workflow_payload():
    payload = json.dumps(asdict(_workflow_result(dry_run=True, confirm=False)), ensure_ascii=False)
    assert "台積電" in payload

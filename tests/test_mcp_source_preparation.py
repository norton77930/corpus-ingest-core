"""Append-only tools, safe envelopes and an owned stdio process workflow."""
import asyncio
from contextlib import asynccontextmanager
import os
import socket
import subprocess
import inspect
import json
import sys
import time

import pytest

from tests.test_source_preparation import configured_source, URL
from tests.test_source_preparation_worker import process_helpers, wait_for_entered


def facade():
    from corpus_ingest_core import mcp_server
    return mcp_server


def test_tools_are_last_two_and_have_only_declared_parameters():
    server=facade()
    names=[tool.name for tool in asyncio.run(server.mcp.list_tools())]
    assert len(names)==35 and names[31:34]==["advance_learning_workflow","prepare_learning_source","inspect_source_preparation_job"]
    signature=inspect.signature(server.prepare_learning_source)
    assert list(signature.parameters)==["url","confirm","expected_plan_id"]
    assert signature.parameters["confirm"].default is False
    assert signature.parameters["expected_plan_id"].default==""
    assert list(inspect.signature(server.inspect_source_preparation_job).parameters)==["job_id"]


def test_preview_submit_and_status_delegate_once(configured_source,monkeypatch):
    from corpus_ingest_core import source_preparation as core
    calls=[]
    monkeypatch.setattr(core,"launch_worker",lambda job:calls.append(job["job_id"]))
    preview=facade().prepare_learning_source(URL)
    assert preview["ok"] and preview["dry_run"] and preview["data"]["requires_confirmation"]
    result=facade().prepare_learning_source(URL,confirm=True,expected_plan_id=preview["data"]["plan_id"])
    assert result["ok"] and "dry_run" not in result
    assert calls==[result["data"]["job_id"]]
    status=facade().inspect_source_preparation_job(result["data"]["job_id"])
    assert status["ok"] and status["data"]["read_only"] and not status["data"]["network_access"]


@pytest.mark.parametrize("reason", ["invalid_request","plan_changed","busy","store_unavailable","launch_failed","outcome_unconfirmed","invalid_transcription_settings","transcription_runtime_unavailable","private diagnostic"])
def test_preparation_errors_are_fixed_and_do_not_echo_details(configured_source,monkeypatch,reason):
    from corpus_ingest_core import source_preparation as core
    def refused(*a,**k):
        raise core.PreparationError(reason)
    monkeypatch.setattr(core,"prepare_learning_source",refused)
    result=facade().prepare_learning_source(URL)
    assert result["ok"] is False and result["error_type"]=="PreparationError"
    assert "private diagnostic" not in json.dumps(result)
    assert result["reason"] in {"invalid_request","plan_changed","busy","store_unavailable","launch_failed","outcome_unconfirmed","invalid_transcription_settings","transcription_runtime_unavailable"}


def test_unexpected_and_malformed_errors_remain_safe(configured_source,monkeypatch):
    from corpus_ingest_core import source_preparation as core
    for error in (RuntimeError("private diagnostic"),core.PreparationError([])):
        monkeypatch.setattr(core,"prepare_learning_source",lambda *a,**k:(_ for _ in ()).throw(error))
        result=facade().prepare_learning_source(URL)
        assert result["ok"] is False and "private diagnostic" not in json.dumps(result)


def test_unknown_status_remains_finite_and_does_not_create_store(configured_source):
    result=facade().inspect_source_preparation_job("f"*32)
    assert result["ok"] and result["data"]["status"]=="unknown"
    assert not (configured_source/"preparation-jobs").exists()
    invalid=facade().inspect_source_preparation_job("../private")
    assert invalid["ok"] is False and "../private" not in json.dumps(invalid)


def test_launch_error_preserves_known_job_reference(configured_source,monkeypatch):
    from corpus_ingest_core import source_preparation as core
    from corpus_ingest_core import source_preparation_jobs as jobs
    server=facade()
    monkeypatch.setattr(core.subprocess,"Popen",lambda *a,**k:(_ for _ in ()).throw(OSError("owned refusal")))
    plan=server.prepare_learning_source(URL)["data"]
    result=server.prepare_learning_source(URL,confirm=True,expected_plan_id=plan["plan_id"])
    assert result["ok"] is False and result["reason"]=="launch_failed"
    assert jobs.inspect(result["job_id"])["reason"]=="launch_failed"


@pytest.mark.parametrize("configured", [False, True])
def test_actual_owned_transport_submit_disconnect_and_later_status(configured_source, configured):
    from tests.test_source_preparation_transcription import configure, DEFAULT, MEDIUM
    if configured:
        configure(configured_source)
    expected_settings = MEDIUM if configured else DEFAULT
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from corpus_ingest_core import source_preparation_jobs as jobs
    _,server_script,environment=process_helpers(configured_source)
    parameters=StdioServerParameters(command=sys.executable,args=[str(server_script)],env=environment)
    http_process=None
    if os.name=="nt":
        from mcp.client.streamable_http import streamable_http_client
        with socket.socket() as listener:
            listener.bind(("127.0.0.1",0))
            port=listener.getsockname()[1]
        http_script=configured_source/"owned_http_server.py"
        http_script.write_text(server_script.read_text(encoding="utf-8").replace("mcp_server.run()",f"mcp_server.run_streamable_http(mcp_server.StreamableHttpConfig(port={port}))"),encoding="utf-8")
        http_process=subprocess.Popen([sys.executable,str(http_script)],env=environment,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    @asynccontextmanager
    async def connection():
        if http_process is None:
            async with stdio_client(parameters) as streams:
                yield streams
        else:
            deadline=time.monotonic()+20
            while True:
                assert http_process.poll() is None,"owned HTTP server exited"
                try:
                    with socket.create_connection(("127.0.0.1",port),timeout=.1):pass
                    break
                except OSError:
                    assert time.monotonic()<deadline,"owned HTTP startup timeout"
                    await asyncio.sleep(.05)
            async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read,write,_):
                yield read,write
    def data(result):
        return result.structuredContent or json.loads(result.content[0].text)
    async def submit():
        async with connection() as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                names=[tool.name for tool in (await session.list_tools()).tools]
                assert names[32:34]==["prepare_learning_source","inspect_source_preparation_job"]
                preview=data(await session.call_tool("prepare_learning_source",{"url":URL}))
                assert preview["ok"] and preview["dry_run"]
                assert preview["data"]["transcription"] == expected_settings
                assert preview["data"]["actual_transcription"] is None
                accepted=data(await session.call_tool("prepare_learning_source",{"url":URL,"confirm":True,"expected_plan_id":preview["data"]["plan_id"]}))
                assert accepted["ok"]
                assert accepted["data"]["transcription"] == expected_settings
                job_id=accepted["data"]["job_id"]
                pending=data(await session.call_tool("inspect_source_preparation_job",{"job_id":job_id}))
                assert pending["ok"] and pending["data"]["status"] in jobs.ACTIVE
                return job_id
    async def observe(job_id):
        async with connection() as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                return data(await session.call_tool("inspect_source_preparation_job",{"job_id":job_id}))
    try:
        job_id=asyncio.run(submit())
        assert wait_for_entered(configured_source)["job_id"]==job_id
        (configured_source/"worker-gate").write_text("continue")
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and jobs.inspect(job_id)["status"] in jobs.ACTIVE:
            time.sleep(.02)
        result=asyncio.run(observe(job_id))
        assert result["ok"] and result["data"]["transcript_ready"]
        assert result["data"]["transcription"] == expected_settings
        assert result["data"]["actual_transcription"] == expected_settings
        assert not result["data"]["study_guide_ready"]
    finally:
        (configured_source/"worker-gate").write_text("stop waiting")
        if http_process is not None:
            http_process.terminate()
            http_process.wait(timeout=10)


@pytest.mark.skipif(sys.platform != "win32",reason="Windows SDK job policy")
def test_default_windows_sdk_host_blocks_submission_before_any_job(configured_source):
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    _,script,environment=process_helpers(configured_source)
    async def preview():
        async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(script)],env=environment)) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                result=await session.call_tool("prepare_learning_source",{"url":URL})
                return result.structuredContent or json.loads(result.content[0].text)
    result=asyncio.run(preview())
    assert result["ok"] and result["data"]["status"]=="blocked"
    assert result["data"]["reason"]=="worker_host_incompatible"
    assert not (configured_source/"preparation-jobs").exists()
    assert not (configured_source/"worker-entered").exists()

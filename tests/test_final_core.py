from __future__ import annotations
import json
from pathlib import Path
from urllib.error import HTTPError
import pytest
from jarvis.audit import AuditLog
from jarvis.configuration import DEFAULT_BASE_URL, Settings
from jarvis.core import JarvisCore
from jarvis.intelligence import IntelligenceProvider, ModelUnavailableError, NvidiaProvider, ProviderConfigurationError, StructuredResponseError
from jarvis.memory import MemoryStore
from jarvis.sandbox import Sandbox
from jarvis.security import ApprovalGate, KillSwitch, SecurityError, SecurityKernel
from jarvis.tasks import Task, TaskState
from jarvis.verification import VerificationEngine
from jarvis.development import RepairLoop
from jarvis.research import UnavailableResearchProvider, ResearchUnavailable
from jarvis.dashboard import render_dashboard


class CandidateProvider(IntelligenceProvider):
    def generate(self, prompt: str) -> str:
        return "{}"
    def plan(self, prompt: str) -> dict:
        return {"plan": ["write test"], "files": [{"path": "test_candidate.py", "content": "def test_candidate(): assert True\n"}]}
    def repair(self, prompt: str) -> dict:
        raise AssertionError("repair is not expected")

def test_configuration_defaults_and_no_key_repr(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False); settings=Settings.from_env()
    assert settings.nvidia_base_url == DEFAULT_BASE_URL and settings.nvidia_api_key is None

def test_memory_categories_search_and_unconfirmed_inference(tmp_path):
    store=MemoryStore(tmp_path/"memory.db"); store.save("semantic","inferred thing",source="inference")
    found=store.search("thing"); assert found[0].confirmed is False and found[0].source == "inference"

def test_task_state_machine_rejects_invalid_transition():
    task=Task("x"); task.transition(TaskState.PLANNING); task.transition(TaskState.RUNNING); task.transition(TaskState.VERIFYING); task.transition(TaskState.COMPLETED)
    with pytest.raises(ValueError): task.transition(TaskState.RUNNING)

def test_core_mission_and_authorized_stop(tmp_path):
    core=JarvisCore(Settings(data_dir=tmp_path)); mission=core.create_mission("build memory")
    assert core.report(mission.id)["production_changes"] == "NO"; assert "cancelamento" in core.process("PARAR")
    with pytest.raises(SecurityError): core.kill_switch.check()

def test_sandbox_permissions_traversal_and_verification(tmp_path):
    sandbox=Sandbox(tmp_path/"candidate", SecurityKernel()); sandbox.write("ok.py", "x = 1\n")
    assert sandbox.read("ok.py") == "x = 1\n"
    with pytest.raises(ValueError): sandbox.write("../escape", "bad")
    with pytest.raises(SecurityError): sandbox.write("production.py", "bad")
    # No pytest tests in candidate is a valid no-test collection result only if package adds one.
    sandbox.write("test_ok.py", "def test_ok(): assert True\n")
    assert VerificationEngine().verify(sandbox, ["ok.py"])[0]

def test_approval_and_audit_redaction(tmp_path):
    gate=ApprovalGate(); assert not gate.can_integrate("m"); gate.approve("m"); assert gate.can_integrate("m"); gate.deny("m"); assert not gate.can_integrate("m")
    path=tmp_path/"audit.jsonl"; AuditLog(path).record("x","ok", api_key="secret", mission_id="m")
    assert "secret" not in path.read_text() and "mission_id" in path.read_text()

def test_missing_key():
    with pytest.raises(ProviderConfigurationError): NvidiaProvider(Settings(nvidia_model="model")).generate("hi")

def test_http_410(monkeypatch):
    def broken(*a, **k): raise HTTPError("url",410,"gone",None,None)
    monkeypatch.setattr("jarvis.intelligence.request.urlopen", broken)
    with pytest.raises(ModelUnavailableError, match="não está mais disponível"):
        NvidiaProvider(Settings(nvidia_api_key="not-real",nvidia_model="model")).generate("hi")

def test_nvidia_response_and_invalid_structured_response(monkeypatch):
    class Response:
        def read(self): return json.dumps({"choices":[{"message":{"content":"{\"ok\": true}"}}]}).encode()
        def __enter__(self): return self
        def __exit__(self,*a): pass
    monkeypatch.setattr("jarvis.intelligence.request.urlopen", lambda *a,**k: Response())
    assert NvidiaProvider(Settings(nvidia_api_key="not-real",nvidia_model="model")).understand("x") == {"ok":True}
    class Bad(IntelligenceProvider):
        def generate(self, prompt): return "nope"
    with pytest.raises(StructuredResponseError): Bad().plan("x")

def test_repair_loop_repairs_candidate_and_research_is_explicit(tmp_path):
    sandbox=Sandbox(tmp_path/"candidate", SecurityKernel()); sandbox.write("test_fix.py", "def test_fix(): assert False\n")
    def repair(issues): sandbox.write("test_fix.py", "def test_fix(): assert True\n")
    outcome=RepairLoop(VerificationEngine(), 2).run(sandbox, repair)
    assert outcome.passed and outcome.attempts == 1
    with pytest.raises(ResearchUnavailable): UnavailableResearchProvider().search("anything")

def test_autonomous_development_creates_verified_candidate_and_needs_approval(tmp_path):
    core = JarvisCore(Settings(data_dir=tmp_path))
    mission = core.create_mission("create a test candidate")
    result = core.develop(mission.id, CandidateProvider())
    assert result.state is TaskState.WAITING
    assert (tmp_path / "candidates" / mission.id / "test_candidate.py").is_file()
    assert core.approval.can_integrate(mission.id) is False
    assert core.approve(mission.id) is True
    assert core.approval.can_integrate(mission.id) is True

def test_autonomous_development_obeys_kill_switch(tmp_path):
    core = JarvisCore(Settings(data_dir=tmp_path)); mission = core.create_mission("do not run")
    core.kill_switch.request(); result = core.develop(mission.id, CandidateProvider())
    assert result.state is TaskState.CANCELLED

def test_dialogue_development_asks_before_releasing_verified_candidate(tmp_path):
    core = JarvisCore(Settings(data_dir=tmp_path), development_provider=CandidateProvider())
    reply = core.process("JARVIS, desenvolva memória de longo prazo")
    assert "Posso liberar" in reply
    assert core.conversation.pending_approval is not None
    assert "Aprovado" in core.process("sim")

def test_plugins_and_presentation_modes_do_not_enable_integrations(tmp_path):
    core = JarvisCore(Settings(data_dir=tmp_path))
    assert "Discord: PLANNED" in core.process("quais plugins e integrações existem?")
    assert "MODO GAMER" in core.process("modo gamer")
    assert "não iniciei desenvolvimento" in core.process("JARVIS, desenvolva um plugin Discord")

def test_dashboard_is_local_companion_markup_and_escapes_mission_data(tmp_path):
    core = JarvisCore(Settings(data_dir=tmp_path))
    core.create_mission("<unsafe mission>")
    page = render_dashboard(core, "<reply>")
    assert "JARVIS ESSENCE" in page
    assert "&lt;unsafe mission&gt;" in page and "&lt;reply&gt;" in page
    assert "127.0.0.1" not in page

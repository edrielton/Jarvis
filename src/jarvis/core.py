"""Provider-agnostic mission coordinator."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
from .audit import AuditLog
from .configuration import Settings
from .memory import MemoryStore
from .security import ApprovalGate, KillSwitch, SecurityKernel
from .tasks import Task, TaskState
from .tasks import TaskOrchestrator
from .sandbox import Sandbox
from .verification import VerificationEngine
from .development import AutonomousDeveloper
from .intelligence import IntelligenceProvider
from .security import SecurityError
from .plugins import PluginRegistry
from .personality import Personality
from .conversation import Conversation

@dataclass
class Mission:
    objective: str; id: str = field(default_factory=lambda: str(uuid4())); requirements: list[str] = field(default_factory=list); plan: list[str] = field(default_factory=list); tasks: list[Task] = field(default_factory=list); state: TaskState = TaskState.PENDING; files: list[str] = field(default_factory=list); attempts: int = 0; tests: list[str] = field(default_factory=list); results: list[str] = field(default_factory=list); evidence: list[str] = field(default_factory=list); checkpoint: str | None = None

class JarvisCore:
    def __init__(self, settings: Settings | None = None, development_provider: IntelligenceProvider | None = None) -> None:
        self.settings=settings or Settings.from_env(); self.settings.data_dir.mkdir(parents=True,exist_ok=True)
        self.memory=MemoryStore(self.settings.data_dir/"memory.sqlite3"); self.audit=AuditLog(self.settings.data_dir/"audit.jsonl")
        self.security=SecurityKernel(); self.kill_switch=KillSwitch(); self.approval=ApprovalGate(); self.missions: dict[str,Mission]={}; self.tasks=TaskOrchestrator()
        self.development_provider = development_provider
        self.plugins = PluginRegistry()
        self.personality = Personality()
        self.conversation = Conversation(self, self.personality)
    def create_mission(self, objective: str) -> Mission:
        mission=Mission(objective=objective); task=Task(objective=objective); mission.tasks.append(task); self.tasks.add(task); self.missions[mission.id]=mission
        self.memory.save("mission_history", objective, source="mission", confirmed=True); self.audit.record("mission_create","ok",mission_id=mission.id); return mission
    def develop(self, mission_id: str, provider: IntelligenceProvider) -> Mission:
        """Run the autonomous candidate workflow and stop before production."""
        mission = self.missions[mission_id]
        task = mission.tasks[0]
        try:
            self.kill_switch.check()
            task.transition(TaskState.PLANNING); mission.state = TaskState.PLANNING
            task.transition(TaskState.RUNNING); mission.state = TaskState.RUNNING
            sandbox = Sandbox(self.settings.data_dir / "candidates" / mission.id, self.security)
            outcome = AutonomousDeveloper(provider, VerificationEngine(), self.settings.max_repair_iterations).run(
                mission.objective, sandbox, self.kill_switch
            )
            mission.files = outcome.files; mission.attempts = outcome.attempts
            task.transition(TaskState.VERIFYING); mission.state = TaskState.VERIFYING
            mission.tests.append("pytest")
            if outcome.ready_for_approval:
                task.transition(TaskState.WAITING); mission.state = TaskState.WAITING
                mission.evidence.append("Candidate verified; explicit approval required for integration")
                self.audit.record("development_candidate", "ready_for_approval", mission_id=mission.id, files=mission.files)
            else:
                task.transition(TaskState.FAILED); mission.state = TaskState.FAILED
                mission.results.extend(outcome.issues)
                self.audit.record("development_candidate", "failed", mission_id=mission.id, error=outcome.issues)
        except (SecurityError, RuntimeError) as exc:
            if task.state not in {TaskState.FAILED, TaskState.CANCELLED, TaskState.COMPLETED}:
                task.transition(TaskState.CANCELLED if self.kill_switch.requested else TaskState.FAILED)
            mission.state = task.state; mission.results.append(str(exc))
            self.audit.record("development_candidate", "cancelled" if self.kill_switch.requested else "failed", mission_id=mission.id, error=str(exc))
        return mission
    def approve(self, mission_id: str) -> bool:
        mission = self.missions[mission_id]
        if mission.state is not TaskState.WAITING:
            return False
        self.approval.approve(mission_id)
        self.audit.record("approval", "approved", mission_id=mission_id)
        return True
    def deny(self, mission_id: str) -> None:
        self.approval.deny(mission_id)
        mission = self.missions[mission_id]
        if mission.state is TaskState.WAITING: mission.state = TaskState.CANCELLED
        self.audit.record("approval", "denied", mission_id=mission_id)
    def process(self, message: str) -> str:
        return self.conversation.reply(message)
    def report(self, mission_id: str) -> dict[str, object]:
        m=self.missions[mission_id]
        return {"objective":m.objective,"status":m.state.value,"plan":m.plan,"files":m.files,"tests":m.tests,"repair_attempts":m.attempts,"checkpoint":m.checkpoint,"production_changes":"NO","next_step":"APPROVE or DENY when candidate is verified"}

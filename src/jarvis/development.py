"""Bounded autonomous development of a candidate, never production."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from .sandbox import Sandbox
from .verification import VerificationEngine
from .intelligence import IntelligenceProvider, StructuredResponseError
from .security import KillSwitch

@dataclass(frozen=True)
class RepairOutcome:
    passed: bool; attempts: int; issues: list[str]

class CodingAgent:
    """Applies reviewed model proposals only through Sandbox controls."""
    def apply_patch(self, sandbox: Sandbox, relative_path: str, content: str) -> None:
        sandbox.write(relative_path, content)

    def apply_files(self, sandbox: Sandbox, files: object) -> list[str]:
        if not isinstance(files, list):
            raise StructuredResponseError("Development response must contain a files list")
        written: list[str] = []
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
                raise StructuredResponseError("Each proposed file requires string path and content")
            self.apply_patch(sandbox, item["path"], item["content"])
            written.append(item["path"])
        return written

class RepairLoop:
    def __init__(self, verifier: VerificationEngine, max_iterations: int = 5) -> None:
        self.verifier, self.max_iterations = verifier, max_iterations
    def run(self, sandbox: Sandbox, repair: Callable[[list[str]], None], required_files: list[str] | None = None) -> RepairOutcome:
        for attempt in range(self.max_iterations + 1):
            passed, issues, _ = self.verifier.verify(sandbox, required_files)
            if passed: return RepairOutcome(True, attempt, [])
            if attempt == self.max_iterations: return RepairOutcome(False, attempt, issues)
            repair(issues)
        raise AssertionError("unreachable")


@dataclass(frozen=True)
class DevelopmentOutcome:
    ready_for_approval: bool
    files: list[str]
    attempts: int
    issues: list[str]


class AutonomousDeveloper:
    """Executes understand/plan/generate/test/repair for one candidate mission.

    The provider can suggest content, but it cannot execute tools: all writes and
    tests are mediated by ``Sandbox`` and security policy.
    """
    def __init__(self, provider: IntelligenceProvider, verifier: VerificationEngine, max_repairs: int) -> None:
        self.provider, self.verifier = provider, verifier
        self.max_repairs = max_repairs

    def run(self, objective: str, sandbox: Sandbox, kill_switch: KillSwitch) -> DevelopmentOutcome:
        kill_switch.check()
        plan = self.provider.plan(f"Create a safe sandbox candidate for: {objective}. Include plan and files.")
        files = CodingAgent().apply_files(sandbox, plan.get("files"))
        required = plan.get("required_files", files)
        if not isinstance(required, list) or not all(isinstance(path, str) for path in required):
            raise StructuredResponseError("required_files must be a list of paths")

        def repair(issues: list[str]) -> None:
            kill_switch.check()
            proposal = self.provider.repair(
                f"Repair candidate for objective: {objective}. Test issues: {issues}. Return files patches."
            )
            CodingAgent().apply_files(sandbox, proposal.get("files"))

        outcome = RepairLoop(self.verifier, self.max_repairs).run(sandbox, repair, required)
        return DevelopmentOutcome(outcome.passed, files, outcome.attempts, outcome.issues)

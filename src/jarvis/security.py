from __future__ import annotations
from dataclasses import dataclass

class SecurityError(PermissionError): pass
@dataclass
class KillSwitch:
    requested: bool = False
    def request(self) -> None: self.requested = True
    def check(self) -> None:
        if self.requested: raise SecurityError("Execution stopped by authorized user")
class SecurityKernel:
    protected = {"production", "security", "approval", "audit", "checkpoint"}
    def authorize(self, action: str, target: str = "") -> None:
        if any(word in target.lower() for word in self.protected): raise SecurityError("Protected target cannot be modified")
        if action not in {"read", "write_sandbox", "run_test", "create_checkpoint"}: raise SecurityError("Action denied by policy")
class ApprovalGate:
    def __init__(self) -> None: self.decisions: dict[str, bool] = {}
    def approve(self, mission_id: str) -> None: self.decisions[mission_id] = True
    def deny(self, mission_id: str) -> None: self.decisions[mission_id] = False
    def can_integrate(self, mission_id: str) -> bool: return self.decisions.get(mission_id, False)

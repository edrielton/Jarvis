from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4

class TaskState(str, Enum):
    PENDING="PENDING"; PLANNING="PLANNING"; RUNNING="RUNNING"; WAITING="WAITING"; VERIFYING="VERIFYING"; RECOVERING="RECOVERING"; COMPLETED="COMPLETED"; FAILED="FAILED"; CANCELLED="CANCELLED"

ALLOWED = {TaskState.PENDING:{TaskState.PLANNING,TaskState.CANCELLED}, TaskState.PLANNING:{TaskState.RUNNING,TaskState.FAILED,TaskState.CANCELLED}, TaskState.RUNNING:{TaskState.WAITING,TaskState.VERIFYING,TaskState.RECOVERING,TaskState.FAILED,TaskState.CANCELLED}, TaskState.WAITING:{TaskState.RUNNING,TaskState.CANCELLED}, TaskState.VERIFYING:{TaskState.COMPLETED,TaskState.WAITING,TaskState.RECOVERING,TaskState.FAILED,TaskState.CANCELLED}, TaskState.RECOVERING:{TaskState.RUNNING,TaskState.FAILED,TaskState.CANCELLED}, TaskState.COMPLETED:set(),TaskState.FAILED:set(),TaskState.CANCELLED:set()}
@dataclass
class Task:
    objective: str; priority: int = 0; dependencies: list[str] = field(default_factory=list); deadline: datetime | None = None; id: str = field(default_factory=lambda: str(uuid4())); state: TaskState = TaskState.PENDING; checkpoint: str | None = None
    def transition(self, target: TaskState) -> None:
        if target not in ALLOWED[self.state]: raise ValueError(f"invalid task transition {self.state} -> {target}")
        self.state = target

class TaskOrchestrator:
    """Priority selection never discards a running task; it marks it waiting."""
    def __init__(self) -> None: self.tasks: dict[str, Task] = {}
    def add(self, task: Task) -> None: self.tasks[task.id] = task
    def next(self) -> Task | None:
        candidates=[t for t in self.tasks.values() if t.state == TaskState.PENDING and all(self.tasks[d].state == TaskState.COMPLETED for d in t.dependencies if d in self.tasks)]
        return max(candidates, key=lambda t:t.priority, default=None)
    def preempt(self, running: Task, urgent: Task, checkpoint: str) -> None:
        if urgent.priority <= running.priority: raise ValueError("task is not urgent")
        running.checkpoint=checkpoint; running.transition(TaskState.WAITING)

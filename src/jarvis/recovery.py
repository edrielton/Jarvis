from __future__ import annotations
from pathlib import Path
import subprocess
class CheckpointManager:
    def __init__(self, repository: Path) -> None: self.repository=repository
    def create(self, label: str) -> str:
        subprocess.run(["git","add","-A"],cwd=self.repository,check=True,capture_output=True)
        result=subprocess.run(["git","commit","-m",f"jarvis checkpoint: {label}"],cwd=self.repository,text=True,capture_output=True)
        if result.returncode not in (0,1): raise RuntimeError(result.stderr)
        return subprocess.check_output(["git","rev-parse","HEAD"],cwd=self.repository,text=True).strip()
    def list(self) -> list[str]: return subprocess.check_output(["git","log","--format=%H %s"],cwd=self.repository,text=True).splitlines()
    def recover(self, revision: str) -> None: subprocess.run(["git","checkout",revision,"--","."],cwd=self.repository,check=True,capture_output=True)

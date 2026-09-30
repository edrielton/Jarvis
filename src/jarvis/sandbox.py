"""Constrained candidate workspace; it never writes to production root."""
from __future__ import annotations
from pathlib import Path
import subprocess
from .security import SecurityKernel

class Sandbox:
    def __init__(self, root: Path, security: SecurityKernel, output_limit: int = 50_000) -> None:
        self.root=root.resolve(); self.root.mkdir(parents=True, exist_ok=True); self.security=security; self.output_limit=output_limit
    def _path(self, relative: str) -> Path:
        path=(self.root / relative).resolve()
        if self.root != path and self.root not in path.parents: raise ValueError("path escapes sandbox")
        return path
    def write(self, relative: str, content: str) -> None:
        self.security.authorize("write_sandbox", relative); path=self._path(relative); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content, encoding="utf8")
    def read(self, relative: str) -> str: self.security.authorize("read", relative); return self._path(relative).read_text(encoding="utf8")
    def list_files(self) -> list[str]: return [str(p.relative_to(self.root)) for p in self.root.rglob("*") if p.is_file()]
    def remove(self, relative: str) -> None: self.security.authorize("write_sandbox", relative); self._path(relative).unlink()
    def run_tests(self, timeout: int = 60) -> "TestResult":
        self.security.authorize("run_test"); proc=subprocess.run(["python", "-m", "pytest"],cwd=self.root,text=True,capture_output=True,timeout=timeout)
        return TestResult(proc.returncode,proc.stdout[-self.output_limit:],proc.stderr[-self.output_limit:])

class TestResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str) -> None: self.exit_code,self.stdout,self.stderr=exit_code,stdout,stderr
    @property
    def passed(self) -> bool: return self.exit_code == 0

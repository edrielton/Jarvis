from __future__ import annotations
from pathlib import Path
import compileall
from .sandbox import Sandbox, TestResult
class VerificationEngine:
    def verify(self, sandbox: Sandbox, required_files: list[str] | None = None) -> tuple[bool, list[str], TestResult | None]:
        issues=[]
        for file in required_files or []:
            if not (sandbox.root/file).is_file(): issues.append(f"missing required file: {file}")
        if not compileall.compile_dir(sandbox.root, quiet=1): issues.append("Python syntax verification failed")
        result=sandbox.run_tests()
        if not result.passed: issues.append("test suite failed")
        return not issues, issues, result

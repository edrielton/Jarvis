from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
class AuditLog:
    def __init__(self, path: Path) -> None: path.parent.mkdir(parents=True, exist_ok=True); self.path=path
    def record(self, action: str, result: str, **details: object) -> None:
        safe = {k:v for k,v in details.items() if "key" not in k.lower() and "secret" not in k.lower()}
        with self.path.open("a", encoding="utf8") as f: f.write(json.dumps({"timestamp":datetime.now(timezone.utc).isoformat(),"action":action,"result":result,**safe})+"\n")

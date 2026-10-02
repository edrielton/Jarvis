"""Persistent, typed SQLite memory. Facts and inferences remain distinguishable."""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MEMORY_TYPES = {"working", "episodic", "semantic", "procedural", "project", "preferences", "mission_history"}

@dataclass(frozen=True)
class MemoryItem:
    id: int; kind: str; content: str; confidence: float; source: str; confirmed: bool; created_at: str

class MemoryStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True); self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY, kind TEXT, content TEXT, confidence REAL, source TEXT, confirmed INTEGER, created_at TEXT)")
        self.db.commit()
    def save(self, kind: str, content: str, *, confidence: float = .5, source: str = "user", confirmed: bool = False) -> int:
        if kind not in MEMORY_TYPES: raise ValueError("unknown memory type")
        now = datetime.now(timezone.utc).isoformat()
        cur = self.db.execute("INSERT INTO memory(kind,content,confidence,source,confirmed,created_at) VALUES(?,?,?,?,?,?)", (kind,content,confidence,source,int(confirmed),now)); self.db.commit(); return int(cur.lastrowid)
    def search(self, query: str, *, kind: str | None = None, limit: int = 10) -> list[MemoryItem]:
        sql = "SELECT * FROM memory WHERE content LIKE ?"; args: list[object] = [f"%{query}%"]
        if kind: sql += " AND kind=?"; args.append(kind)
        sql += " ORDER BY id DESC LIMIT ?"; args.append(limit)
        return [MemoryItem(*row[:5], bool(row[5]), row[6]) for row in self.db.execute(sql, args)]
    def close(self) -> None: self.db.close()

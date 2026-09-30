"""Research boundary that refuses to invent sources."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
@dataclass(frozen=True)
class ResearchResult: information: str; source: str; timestamp: datetime; confidence: float; contradictions: list[str]
class ResearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[ResearchResult]: ...
class ResearchUnavailable(RuntimeError): pass
class UnavailableResearchProvider(ResearchProvider):
    def search(self, query: str) -> list[ResearchResult]: raise ResearchUnavailable("Research provider is not configured")

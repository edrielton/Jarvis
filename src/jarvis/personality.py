"""Presentation-only personality modes; they never affect security policy."""
from __future__ import annotations

from enum import Enum


class PersonalityMode(str, Enum):
    NORMAL = "NORMAL"
    SERIOUS = "SERIOUS"
    HUMOR = "HUMOR"
    ADVISOR = "ADVISOR"
    RESEARCH = "RESEARCH"
    DEVELOPMENT = "DEVELOPMENT"
    DEFENSE = "DEFENSE"
    GAMER = "GAMER"


class Personality:
    def __init__(self) -> None:
        self.mode = PersonalityMode.NORMAL

    def set(self, requested: str) -> PersonalityMode | None:
        normalized = requested.strip().upper().replace(" ", "_")
        try:
            self.mode = PersonalityMode(normalized)
        except ValueError:
            return None
        return self.mode

    def decorate(self, response: str) -> str:
        if self.mode is PersonalityMode.HUMOR:
            return f"{response}\n\nModo humor ativo: sem piadas com sua segurança — ela continua séria."
        if self.mode is PersonalityMode.GAMER:
            return f"[MODO GAMER] {response}"
        return response

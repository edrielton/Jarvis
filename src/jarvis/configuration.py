"""Central, secret-safe configuration."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_PURPOSE = (
    "Aumentar a capacidade do usuário de alcançar seus objetivos por meio de "
    "inteligência, conhecimento, planejamento, desenvolvimento e execução "
    "controlada, preservando segurança, integridade do sistema e controle humano."
)


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str | None = None
    nvidia_model: str | None = None
    nvidia_base_url: str = DEFAULT_BASE_URL
    data_dir: Path = Path(".jarvis")
    max_repair_iterations: int = 5
    purpose: str = DEFAULT_PURPOSE

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            nvidia_api_key=os.getenv("NVIDIA_API_KEY") or None,
            nvidia_model=os.getenv("NVIDIA_MODEL") or None,
            nvidia_base_url=os.getenv("NVIDIA_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            data_dir=Path(os.getenv("JARVIS_DATA_DIR", ".jarvis")),
            max_repair_iterations=int(os.getenv("MAX_REPAIR_ITERATIONS", "5")),
        )

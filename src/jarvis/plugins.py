"""Declarative plugin registry; plugins have no authority until implemented and approved."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PluginManifest:
    identifier: str
    display_name: str
    platform: str
    capabilities: tuple[str, ...]
    status: str
    reason: str


class PluginRegistry:
    """Lists extension points without silently connecting to third-party apps."""

    def __init__(self) -> None:
        self._plugins = {
            item.identifier: item
            for item in (
                PluginManifest("terminal", "Terminal / Termux", "termux,linux,windows", ("conversation", "status"), "READY", "built-in interface"),
                PluginManifest("desktop", "Desktop UI", "windows,linux,macos", ("dashboard", "conversation"), "PLANNED", "no graphical backend installed"),
                PluginManifest("discord", "Discord", "cross-platform", ("read_messages", "send_messages"), "PLANNED", "requires a dedicated adapter and user token"),
                PluginManifest("browser", "Browser", "cross-platform", ("navigate", "research"), "PLANNED", "requires a dedicated adapter and approval"),
                PluginManifest("gamer", "Gamer mode", "cross-platform", ("game_assistance",), "PLANNED", "conversation mode only; no game-control adapter exists"),
            )
        }

    def list(self) -> list[PluginManifest]:
        return list(self._plugins.values())

    def summary(self) -> str:
        return "\n".join(
            f"- {plugin.display_name}: {plugin.status} — {plugin.reason}"
            for plugin in self.list()
        )

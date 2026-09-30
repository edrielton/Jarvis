"""Natural-language dialogue that mediates every requested action through Core."""
from __future__ import annotations

from .personality import Personality


class Conversation:
    def __init__(self, core: object, personality: Personality) -> None:
        self.core = core
        self.personality = personality
        self.pending_approval: str | None = None

    def reply(self, message: str) -> str:
        text, lower = message.strip(), message.strip().casefold()
        if lower in {"sair", "exit", "quit"}:
            return "Até logo."
        if lower in {"stop", "halt", "cancel", "parar"}:
            self.core.kill_switch.request()
            return "Entendido. Execução marcada para cancelamento na próxima fronteira segura."
        if self.pending_approval:
            return self._approval(lower)
        if lower.startswith("modo "):
            mode = self.personality.set(text[5:])
            return self.personality.decorate(f"Modo {mode.value} ativado.") if mode else "Modo desconhecido. Tente humor, gamer, serious ou advisor."
        if "desenvolva" in lower:
            return self._develop(text)
        if "plugin" in lower or "integraç" in lower or "aplicativo" in lower:
            return self.personality.decorate(self.core.plugins.summary())
        if "o que você" in lower and any(word in lower for word in {"faz", "pode", "consegue"}):
            return self.personality.decorate("Posso conversar, criar missões de desenvolvimento em sandbox, testar candidatos e mostrar plugins planejados. Diga o resultado que você quer alcançar.")
        return self.personality.decorate("Entendi. Conte o objetivo, contexto e restrições; eu vou transformar isso em uma missão segura.")

    def _develop(self, objective: str) -> str:
        mission = self.core.create_mission(objective)
        if self.core.development_provider is None:
            return self.personality.decorate(f"Criei a missão {mission.id}, mas não iniciei desenvolvimento: configure NVIDIA_API_KEY e NVIDIA_MODEL.")
        result = self.core.develop(mission.id, self.core.development_provider)
        if result.state.value == "WAITING":
            self.pending_approval = result.id
            return self.personality.decorate("Terminei o candidato, executei as verificações e ele está isolado. Posso liberar este candidato para a próxima etapa de integração? (sim/não)")
        return self.personality.decorate(f"A missão terminou com estado {result.state.value}. Não vou afirmar que a integração foi criada.")

    def _approval(self, lower: str) -> str:
        mission_id = self.pending_approval
        if lower in {"sim", "s", "aprovo", "pode adicionar", "pode integrar"}:
            self.pending_approval = None
            if self.core.approve(mission_id):
                return self.personality.decorate("Aprovado para a próxima etapa. O candidato continua separado: ainda não há integração automática em produção.")
        if lower in {"não", "nao", "n"}:
            self.pending_approval = None
            return self.personality.decorate("Tudo bem. O candidato permanece isolado e nada foi aplicado ao sistema.")
        return self.personality.decorate("Responda sim para aprovar a próxima etapa ou não para manter o candidato isolado.")

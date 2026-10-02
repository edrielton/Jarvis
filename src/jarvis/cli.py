from __future__ import annotations
import argparse
from .configuration import Settings
from .core import JarvisCore
from .intelligence import NvidiaProvider, IntelligenceError
from .dashboard import serve_dashboard

def main() -> None:
    parser=argparse.ArgumentParser(prog="jarvis"); parser.add_argument("command",nargs="?",default="help"); parser.add_argument("text",nargs="*"); args=parser.parse_args()
    settings=Settings.from_env()
    if args.command == "doctor":
        print("Python: OK"); print("NVIDIA API: CONFIGURED" if settings.nvidia_api_key else "NVIDIA API: NOT CONFIGURED")
        print("Model: CONFIGURED" if settings.nvidia_model else "Model: NOT CONFIGURED")
        if settings.nvidia_api_key and settings.nvidia_model:
            try: NvidiaProvider(settings).generate("Reply with OK"); print("Authentication: OK\nModel: AVAILABLE")
            except IntelligenceError as exc: print(f"Provider check: FAILED ({exc})")
        return
    provider = NvidiaProvider(settings) if settings.nvidia_api_key and settings.nvidia_model else None
    core=JarvisCore(settings, development_provider=provider)
    if args.command in {"help","--help"}: print("Commands: chat dashboard [port] plugins interface help status doctor develop exit")
    elif args.command == "chat":
        print("JARVIS: Olá. Fale naturalmente; digite 'sair' para encerrar.")
        while True:
            try: message = input("Você: ")
            except EOFError: break
            print(f"JARVIS: {core.process(message)}")
            if message.strip().casefold() in {"sair", "exit", "quit"}: break
    elif args.command == "plugins": print(core.plugins.summary())
    elif args.command == "dashboard":
        port = int(args.text[0]) if args.text else 8765
        serve_dashboard(core, port)
    elif args.command == "interface":
        print("JARVIS ESSENCE\nPlatform: Terminal / Termux / PC console\nType 'jarvis chat' for dialogue.\nPlugins:\n" + core.plugins.summary())
    elif args.command == "develop":
        objective = " ".join(args.text).strip()
        if not objective:
            parser.error("develop requires an objective")
        mission = core.create_mission(objective)
        if not settings.nvidia_api_key or not settings.nvidia_model:
            print(f"Mission created: {mission.id}. Development not started: configure NVIDIA_API_KEY and NVIDIA_MODEL.")
            return
        result = core.develop(mission.id, provider)
        print(f"Mission: {result.id}\nStatus: {result.state.value}\nCandidate files: {', '.join(result.files) or 'none'}")
    elif args.command == "status": print(f"missions={len(core.missions)} purpose={settings.purpose}")
    else: print(core.process(" ".join([args.command,*args.text])))
if __name__ == "__main__": main()

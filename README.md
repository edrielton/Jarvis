# JARVIS ESSENCE 1.0 — FINAL CORE

JARVIS Essence is a Python 3.10+ provider-agnostic agent core designed to prepare and verify changes in an isolated candidate sandbox. Production integration is deliberately outside automated authority and requires explicit approval.

## Install (including Termux)

```sh
pkg install python git   # Termux only
python -m pip install -e '.[test]'
```

## NVIDIA NIM configuration

```sh
export NVIDIA_API_KEY='set-this-in-your-shell-only'
export NVIDIA_MODEL='your-current-nim-model'
export NVIDIA_BASE_URL='https://integrate.api.nvidia.com/v1' # optional default
jarvis doctor
```

No credential is persisted, logged, or included in this repository. `NVIDIA_MODEL` is entirely environment-configured, so a discontinued model can be replaced without source edits. HTTP 410 reports that the configured model is unavailable.

## Commands

Use `jarvis chat` for a dialogue instead of fixed commands. `jarvis interface` is a dependency-free PC/Termux console interface, and `jarvis plugins` shows extension points. `jarvis develop <objective>` remains available for scripts.

### Companion dashboard (PC and Termux)

`jarvis dashboard` starts a local-only browser dashboard at `http://127.0.0.1:8765` (or use `jarvis dashboard 9000`). It is a portable companion-style island with an animated JARVIS orb, mission state, plugin status, and chat form. It intentionally is **not** a native transparent notch/top-edge window: that requires separate macOS/Windows platform applications and is not claimed here. On Termux, open the localhost URL in the device browser.

## Plugins, modes, and integrations

The registry includes Terminal/Termux, Desktop UI, Discord, Browser, and Gamer extension points. Only the terminal interface is ready; the others are intentionally **PLANNED** until a dedicated adapter, least-privilege permissions, credentials supplied by the user, tests, and approval are implemented. Gamer mode is a presentation mode, not game automation. Say `modo humor` or `modo gamer` during `jarvis chat`; personality never changes security policy.

When you say `JARVIS, desenvolva ...` in chat with NVIDIA configured, JARVIS creates a candidate, tests it in sandbox, and asks whether it may release the verified candidate to the next integration step. Saying yes records Approval Gate approval only; it does not silently modify production or connect an external app.

## Architecture and safety

`core` coordinates missions but has no NVIDIA HTTP code. `intelligence` supplies the abstract provider and NIM implementation. `memory` stores working, episodic, semantic, procedural, project, preference and mission-history records. `security` is authoritative over tools; `sandbox` rejects traversal and production/security targets. `verification` performs required-file, syntax, and pytest checks. Candidate changes require `ApprovalGate.approve()` before any future integration layer may apply them.

`development` provides an autonomous candidate workflow: it asks the configured provider for a structured plan and file proposals, validates their schema, writes them only through sandbox controls, runs deterministic verification, and requests structured repairs for at most five iterations. A verified candidate becomes **WAITING** for explicit approval; it does not modify production. `research` provides a source-bearing interface and explicitly raises a configuration error instead of inventing sources when no provider is attached.

## Autonomous development boundaries

Autonomy means the agent can decide the *steps* of an authorized candidate-development mission, including planning, writing candidate files, testing and bounded repair. It does **not** mean authority to execute arbitrary shell commands, alter production, change security policy, access credentials, remove audit records, or bypass `APPROVE`. The live NVIDIA provider is required to produce autonomous plans; without provider configuration, a development run fails visibly rather than pretending to have developed anything.

## Tests

```sh
python -m pytest
python -m jarvis.cli doctor
```

The doctor makes a live provider request only when both NVIDIA environment values are supplied; it never prints the API key.

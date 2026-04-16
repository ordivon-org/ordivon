# Hermes Runtime

Hermes is the active project-scoped agent runtime for this machine.

## Canonical Paths

- project: `/home/dev/projects/hermes-runtime`
- state: `/home/dev/state/hermes`
- config: `/home/dev/state/hermes/config.yaml`
- env: `/home/dev/state/hermes/.env`

## Operating Rules

- Hermes is not a global installer-managed runtime
- start Hermes from the project directory
- keep mutable state in `/home/dev/state/hermes`
- do not reintroduce `~/.hermes` as the active runtime model

## Standard Commands

```bash
cd /home/dev/projects/hermes-runtime
nix develop .
./bin/hermes-runtime
```

```bash
cd /home/dev/projects/hermes-runtime
nix develop . -c ./bin/hermes-runtime status
```

```bash
cd /home/dev/projects/hermes-runtime
nix develop . -c ./bin/hermes-runtime doctor
```

## Model Position

- default provider: `openai-codex`
- default model: `openai/gpt-5.4`
- configured fallback provider: `gemini`
- configured fallback model: `gemini-3.1-pro-preview`

## Relevant Skills

Useful upstream Hermes skills already present in the runtime:

- `autonomous-ai-agents/hermes-agent`
- `note-taking/obsidian`
- `research/llm-wiki`

## Role In This System

- Hermes executes work
- Hermes reads and writes markdown files
- Hermes maintains tool and workflow documentation
- Hermes should only promote high-value repeated procedures into skills after the wiki version is stable

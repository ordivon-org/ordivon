# Workflows Docs

Use this directory for durable workflow descriptions such as daily brief generation, portfolio review, asset analysis, and postmortem handling.

Each workflow doc should describe:

- trigger
- required context
- participating skills and tools
- governance checkpoints
- state writes
- knowledge writes

Current operational workflows also include repository maintenance flows:

- [Status Sync Workflow](./status-sync-workflow.md)
  - required after every completed module so that state docs stay aligned with code

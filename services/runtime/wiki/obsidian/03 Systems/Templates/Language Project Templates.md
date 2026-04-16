# Language Project Templates

This note records the standard local project templates for common languages on this machine.

Policy source:

- `[[99 Rules/Machine Policy v2]]`

Local template repository:

- `/home/dev/projects/templates/dev-templates`

## Why Local Templates

The machine uses the official Nix flake template mechanism, but the language-specific templates are maintained locally so the team controls:

- runtime versions
- project entry rules
- README expectations
- auditability

This avoids depending on a third-party GitHub template repo as a moving baseline.

## Standard Usage

```bash
mkdir -p /home/dev/projects/<project-name>
cd /home/dev/projects/<project-name>
nix flake init -t path:/home/dev/projects/templates/dev-templates#<template-name>
direnv allow
```

## Available Templates

### Python

Template:

- `python-uv`

Use when:

- the project is primarily Python
- dependencies should be managed in a project-local `.venv`

### Node + TypeScript

Template:

- `node-ts`

Use when:

- the project is primarily TypeScript or Node
- dependencies should stay in local `node_modules`

### Rust

Template:

- `rust`

Use when:

- the project is primarily Rust
- the standard cargo toolchain is sufficient

### Go

Template:

- `go`

Use when:

- the project is primarily Go
- the standard Go + `gopls` workflow is sufficient

### Java

Template:

- `java`

Use when:

- the project is primarily Java
- a standard JDK + Maven workflow is sufficient

### Shell

Template:

- `shell`

Use when:

- the project is mostly shell automation
- the repo does not need a heavier language runtime

### Python + TypeScript

Template:

- `python-ts`

Use when:

- the project has both a Python runtime and a TypeScript frontend or tooling layer

## Hard Rules

- do not install project runtimes globally
- do not bypass `flake.nix`
- do not bypass `.envrc`
- do not rewrite README onboarding to require global installs
- if a template must deviate, record it as an exception

## Review Rule

Whenever a template changes:

1. update the template files
2. update this note if behavior changed
3. record the reason if the change introduces an exception

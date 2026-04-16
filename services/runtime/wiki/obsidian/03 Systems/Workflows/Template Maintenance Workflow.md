# Template Maintenance Workflow

This workflow defines how local project templates are changed, reviewed, and validated.

## Purpose

Use this workflow when:

- adding a new language template
- changing runtime versions in a template
- changing README onboarding in a template
- changing project entry behavior

## Template Source

Local template repository:

- `/home/dev/projects/templates/dev-templates`

Policy source:

- `[[99 Rules/Machine Policy v2]]`

## Change Sequence

### 1. Confirm the layer boundary

Before editing a template, confirm:

- project runtimes stay in `flake.nix`
- `.envrc` stays minimal
- README does not require global installs
- no shell startup file is used as a workaround

### 2. Edit the template

Change only the template that needs the update.

Examples:

- `python-uv`
- `node-ts`
- `rust`
- `go`
- `java`
- `shell`
- `python-ts`

### 3. Validate template registry

Run:

```bash
cd /home/dev/projects/templates/dev-templates
nix flake show --all-systems
```

### 4. Validate generated usage

At minimum, check:

- `flake.nix` exists
- `.envrc` exists
- `README.md` exists
- declared runtime tools match the template intent

### 5. Update template documentation

If behavior changed, update:

- `[[03 Systems/Templates/Language Project Templates]]`
- `[[03 Systems/Workflows/Project Bootstrap Workflow]]` if needed

### 6. Record exceptions if required

If a template needs a rule deviation, create an exception record first.

Use:

- `[[03 Systems/Templates/Exception Record Template]]`

## Review Checklist

- no global runtime install step added
- no undocumented exception introduced
- README still starts with `direnv allow`
- template remains aligned with machine policy

## Rule

If a template change cannot be explained in one sentence against machine policy, do not merge it into the local template repository.

# Web App

This app is managed through the repo `pnpm` workspace.

## Supported Package Manager

Use `pnpm` only.

- Start dev server from the repo root:

```bash
pnpm dev:web
```

- Or run the app directly:

```bash
pnpm --dir apps/web dev
```

- Build the app:

```bash
pnpm build:web
```

or

```bash
pnpm --dir apps/web build
```

Do not use `npm`, `yarn`, or `bun` for this workspace.

# PPT Master provider realization

Workstation owns the node-local production realization of the external PPT Master authoring provider. Artifact remains the consuming-domain owner for route selection, source/material semantics, provider-lock verification, PPTX inspection, PowerPoint target checks, visual/accessibility gates and delivery acceptance.

## Desired state

`ansible/ppt-master-provider.yml` pins the upstream source to exact commit `7879bbc811f86ed9e43df0053169d885cff942c7` from `https://github.com/hugohe3/ppt-master.git`.

The immutable release lives at `/opt/ordivon/external/ppt-master/7879bbc811f86ed9e43df0053169d885cff942c7`. The consumer-facing locator is `/opt/ordivon/external/ppt-master/current`.

The provider environment is created from the provider-owned `requirements.txt` with upstream `uv` and is exposed at the Artifact-compatible path `current/.venv-exp/bin/python`.

The stable locator is promoted only after the exact Git commit is observed, tracked source is clean, the provider Python and both Artifact-consumed entrypoints are regular files, and both entrypoint CLIs import successfully under the realized environment.

## Apply

```bash
ansible-playbook -i ansible/inventory.ini ansible/ppt-master-provider.yml --syntax-check
ansible-playbook -i ansible/inventory.ini ansible/ppt-master-provider.yml
```

The playbook deliberately refuses destructive takeover when `current` exists as a non-symlink. A future provider upgrade should use a new versioned release root, prove its health, and only then move the stable symlink.

## Boundary

This playbook does not create an Ordivon package manager, provider registry, daemon or semantic wrapper. Workstation owns the mature host desired-state mechanics only: Git materialization, Python environment realization, stable locator promotion and bounded health evidence. Artifact continues to fail closed on its own provider lock and to decide whether any generated presentation is semantically acceptable.

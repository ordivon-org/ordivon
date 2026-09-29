# Social Fabric commitment policy R3

This directory is an OPA reference profile, not a new Ordivon policy language.

The policy evaluates explicit set membership and blocker predicates for one R2
candidate. It never counts votes, ranks candidates, grants execution, or creates
EffectAuthority. The caller must preserve the R2 standing boundary and use the
result only for SF41/SF42 shadow projection.

A satisfied OPA decision means only: the named candidate meets this explicit
policy profile at this bounded cut.

Run:

```bash
opa test policies/social-fabric-commitment-r3 -v
```

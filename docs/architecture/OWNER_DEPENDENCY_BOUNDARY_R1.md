# Ordivon owner dependency boundary R1

Date: 2026-09-21
Status: IMPLEMENTED — bounded literal-seam guard

## Property

Source co-location in the modular monorepo does not grant one owner permission to consume another owner's implementation internals.

The R1 guard is deliberately narrow. It evaluates explicit cross-owner path literals in active tracked source/config files and requires each occurrence to match one exact declared seam with a documented contract or boundary.

This is repository-boundary enforcement. It is not a universal dependency graph, capability registry, or domain authority.

## Current admitted seam classes

| Consumer | Producer | Kind | Boundary |
| --- | --- | --- | --- |
| Harness | Security | PUBLIC_OWNER_LOCATOR | Accepted canonical Security subtree locator; Security revision stays subtree-scoped |
| Web | Security | PUBLIC_SOURCE_CONTRACT | Only the Agent Request Verifier and Agent Admission public contract paths |
| Media | Artifact | READ_ONLY_OWNER_PROJECTION | Disposable Creative Index reads Artifact delivery/acceptance projections |
| Skills | Next | OPERATOR_SOURCE_BINDING | Temporary filesystem-to-MCP bridge over operator-configured source roots |
| Workstation | Distribution | ACCEPTANCE_EVIDENCE_BINDING | n8n acceptance consumes one Distribution evidence input |
| Workstation | Game / Media | TEST_ONLY_ENVIRONMENT_BINDING | Host toolchain consequence tests only |

Test and E2E variants are declared separately. A production source file cannot inherit permission merely because the same owner pair already has a test seam.

## Explicit non-edges

The following Next trees are navigation or knowledge projections rather than executable dependency edges:

- meta/next/authorities/
- meta/next/knowledge/
- meta/next/domains/

Historical docs, evidence, planning, research, experiments, fixtures, and retained artifacts are also excluded from active-source dependency truth.

## Falsification

Executable unit checks prove:

1. Web may reference the exact Security public verifier contract.
2. The same file may not substitute a Security internal source path.
3. Another Web file does not gain permission merely because Web to Security is an admitted pair.
4. Next metadata/navigation references do not become runtime dependency edges.

## Current measured standing

At the R1 implementation fence the checker inspected 1,844 active tracked files and found 20 cross-owner literal references covered by 16 narrow seam declarations.

No undeclared active literal seam remained.

## Scope limit

R1 detects explicit owner-root literals. It does not claim complete discovery of dynamically constructed paths, package-manager dependencies, protocol calls, generated code, or runtime network edges.

Language-native module/import enforcement is added only if a real current dependency class requires it. Co-location alone is not a reason to create a cross-language dependency framework.

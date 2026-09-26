# Capability Packages

Capability Packages are **task-local working sets**, not Ordivon subsystems, services, repositories, or mandatory dependency graphs.

A package exists only to answer five operational questions for a recurring class of real work:

1. Which mature external knowledge, standards, methods, and professional practices govern this kind of work?
2. Which mature tools, services, Skills, and providers are appropriate implementations?
3. Which of those capabilities are already available locally or through connected providers?
4. What is actually missing for the current real task?
5. What evidence will show that the real task succeeded?

## Package census loop

`real workload -> mature ecosystem census -> local capability census -> concrete gap -> activate/install only what is needed -> execute -> verify in reality`

Do **not** create a new framework, lifecycle specification, ontology, or orchestration layer merely because a package has many activities. External standards and domain practice remain authoritative.

A package may compose other packages. Composition does not create permanent dependencies. For example, a game task may temporarily use Engineering, Artifact, Media, Security, Network and Distribution without Game owning any of them.

## Package card contract

Each package card should remain small and record only:

- outcome scope;
- mature external knowledge owners;
- mature implementation/provider choices;
- currently observed local capabilities;
- task-triggered gaps;
- one or more real acceptance workloads;
- current standing and last census date.

Do not record hypothetical missing tools as installation debt. A capability is a gap only when a real workload needs it and the existing environment cannot satisfy the requirement adequately.

## Inventory standing labels

Package cards may use small local inventory labels such as `READY_FOR_REAL_WORK`, `TASK_GAP`, `BLOCKED`, or `NEXT_CENSUS`. These labels describe only the state of this capability census:

- `READY_FOR_REAL_WORK`: enough currently known capability exists to start ordinary real workloads;
- `TASK_GAP`: a current workload has exposed a concrete missing capability;
- `BLOCKED`: that workload cannot proceed safely or correctly with currently available mature options;
- `NEXT_CENSUS`: the package has not yet received the current census treatment.

They are not domain verdicts, conformance levels, certification, completion states, or a cross-domain Ordivon acceptance ontology. Real task success remains owned by the applicable domain/native validators and evidence.

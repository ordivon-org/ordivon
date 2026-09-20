# Artifact E2E — Electronic Design / KiCad PCB R1

## Decision

Artifact now admits one deliberately narrow **electronic-design** shadow profile: `eda-kicad-pcb-gerber-r1`.

This is not an Ordivon EDA engine. KiCad remains the native PCB authoring, DRC and manufacturing-export authority. Artifact binds exact source bytes, an exact mechanical object contract, exact KiCad tool identity, native DRC evidence, board statistics, and selected Gerber/Excellon outputs.

## R1 executable chain

```text
exact .kicad_pcb bytes
  -> exact request-bound board contract
  -> KiCad 10.0.x native error-severity DRC
  -> KiCad native board statistics
  -> contract comparison
  -> selected Gerber layer export + .gbrjob
  -> Excellon drill export + report
  -> digest-bound Artifact verification result
```

A positive probe produced zero error-severity DRC violations and non-empty F.Cu/B.Cu/Edge.Cuts Gerber plus Excellon output. A destructive negative moved two PTH pads on different nets into overlap; KiCad returned exit code 5 with four error violations including net shorting and solder-mask bridges. A positive-only smoke would not be sufficient.

## Boundaries

PASS does **not** establish schematic parity, circuit correctness, signal/power integrity, EMC, manufacturing yield, BOM/sourcing correctness, safety, regulatory compliance, or product fitness. Those belong to EDA/domain-specific authorities and later profiles.

A second independent R1 slice now covers `eda-spice-transient-measure-r1`. `ngspice 47` remains the parser/simulator authority; Artifact requires successful batch transient execution, a request-bound minimum data-row floor and explicit numeric ranges for named native `.measure` results. The bounded RC fixture produced 453 data rows with `vmax=0.717983` and `vend=0.264563`; a malformed element failed with exit 1, and a deliberately too-tight numeric contract fails independently even when simulation itself succeeds.

Schematic ERC, KiCad schematic↔PCB parity, IPC-2581/ODB++, richer SPICE analyses/models, HDL/FPGA and production test remain separate slices.

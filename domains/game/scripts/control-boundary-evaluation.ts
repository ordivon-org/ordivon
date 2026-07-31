import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

import { runControlBoundaryEvaluation } from "../src/evaluation/control-boundary.ts";

const output = resolve(process.argv[2] ?? "docs/M5-R1-CONTROL-BOUNDARY-EVALUATION.json");
const report = await runControlBoundaryEvaluation();
mkdirSync(dirname(output), { recursive: true });
writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);

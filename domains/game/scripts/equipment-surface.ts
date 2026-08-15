import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";

export type GameEquipmentOperation =
  | "level.topology.author"
  | "sprite.source.author"
  | "vector.asset.author"
  | "gpu.frame.inspect";

type Spec = {
  equipmentId: string;
  executable?: string;
  source: "isolated" | "managed";
  authority: string;
  admission: string;
  role: "production" | "specialist" | "diagnostic";
};

const SPECS: Record<GameEquipmentOperation, Spec> = {
  "level.topology.author": {
    equipmentId: "game-tiled-e1", executable: "tiled", source: "isolated", role: "production",
    authority: "Tiled edits candidate geometry; Game-owned topology/parser/reducer remain authoritative.",
    admission: "Accept only committed TMJ bytes that pass Game spatial-layout validation and product tests.",
  },
  "sprite.source.author": {
    equipmentId: "game-aseprite-e1", source: "managed", role: "production",
    authority: "Aseprite owns editable sprite/project bytes; Game owns frame/tag meaning consumed by Station Zero.",
    admission: "Accept only committed .aseprite/export metadata whose exact tags/frames pass Game expression-asset validation.",
  },
  "vector.asset.author": {
    equipmentId: "game-inkscape-e1", executable: "inkscape", source: "isolated", role: "specialist",
    authority: "Vector output is expression material and never owns gameplay state or topology.",
    admission: "Inspect/export the exact artifact and admit it only through the owning Game/Studio asset workflow.",
  },
  "gpu.frame.inspect": {
    equipmentId: "game-renderdoc-e1", executable: "renderdoccmd", source: "isolated", role: "diagnostic",
    authority: "RenderDoc capture/decode is observation evidence, not renderer or gameplay truth.",
    admission: "Use only for an exact owned Game rendering workload; retain capture identity and interpret findings in Game.",
  },
};

export function gameEquipmentCatalog() {
  return {
    schemaVersion: 1,
    kind: "ordivon.game-development-equipment-surface",
    operations: Object.entries(SPECS).map(([operation, spec]) => ({ operation, ...spec })),
    workstationOwnsPhysicalBinding: true,
    runtimeOwnsPhysicalExecution: true,
    gameOwnsDomainMeaning: true,
    gameplayAuthorityGranted: false,
    mcpRequired: false,
  };
}

function bindingCommand(spec: Spec): string[] {
  if (spec.source === "managed") return ["managed", "--equipment-id", spec.equipmentId];
  return ["isolated", "--equipment-id", spec.equipmentId, "--executable", spec.executable!];
}

export function resolveGameEquipment(operation: GameEquipmentOperation, sourceEnv: NodeJS.ProcessEnv = process.env) {
  const spec = SPECS[operation];
  if (!spec) throw new Error(`unsupported Game equipment operation: ${operation}`);
  const tool = sourceEnv.ORDIVON_EQUIPMENT_BINDING || "/root/tools/bin/equipment-binding";
  if (!existsSync(tool)) {
    return { schemaVersion: 1, kind: "ordivon.game-equipment-resolution", operation, state: "UNRESOLVED", reason: "Workstation EquipmentBinding is unavailable", spec };
  }
  try {
    const contractArgs = sourceEnv.ORDIVON_WORKSTATION_CONTRACT ? ["--contract", sourceEnv.ORDIVON_WORKSTATION_CONTRACT] : [];
    const output = execFileSync(tool, [...contractArgs, ...bindingCommand(spec)], { encoding: "utf8", timeout: 15000 });
    const binding = JSON.parse(output);
    if (binding?.kind !== "ordivon.workstation-equipment-binding" || binding?.state !== "AVAILABLE") throw new Error("invalid Workstation equipment binding");
    if (binding?.equipmentId !== spec.equipmentId) throw new Error("Workstation equipment identity mismatch");
    return {
      schemaVersion: 1,
      kind: "ordivon.game-equipment-resolution",
      operation,
      state: "AVAILABLE",
      role: spec.role,
      authority: spec.authority,
      admission: spec.admission,
      binding,
      gameplayAuthorityGranted: false,
    };
  } catch (error) {
    return { schemaVersion: 1, kind: "ordivon.game-equipment-resolution", operation, state: "UNAVAILABLE", reason: error instanceof Error ? error.message : String(error), spec };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const operation = process.argv[2] as GameEquipmentOperation | undefined;
  if (!operation) process.stdout.write(`${JSON.stringify(gameEquipmentCatalog(), null, 2)}\n`);
  else process.stdout.write(`${JSON.stringify(resolveGameEquipment(operation), null, 2)}\n`);
}

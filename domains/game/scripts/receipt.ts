import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { sha256 } from "../src/digest.ts";
import { compileProviderContext, FixtureProvider, admitProviderDecision } from "../src/provider.ts";
import { GameStore } from "../src/storage.ts";

const directory = mkdtempSync(join(tmpdir(), "ordivon-game-receipt-"));
const dbPath = join(directory, "world.sqlite3");

try {
  const first = new GameStore(dbPath);
  const initial = first.loadState();
  const context = compileProviderContext(initial);
  const provider = new FixtureProvider();
  const decision = await provider.decide(context);
  const candidate = admitProviderDecision(context, decision);
  if (!candidate) {
    throw new Error("provider did not return an admitted candidate");
  }

  const startedAt = performance.now();
  const applied = first.apply({
    kind: candidate.kind,
    commandId: "receipt-restore-power",
    actorId: candidate.actorId,
    targetId: candidate.targetId,
    expectedRevision: candidate.expectedRevision,
  });
  const applyMs = performance.now() - startedAt;
  first.close();

  const reopened = new GameStore(dbPath);
  const recovered = reopened.loadState();
  const replayStartedAt = performance.now();
  const replay = reopened.replay();
  const replayMs = performance.now() - replayStartedAt;
  reopened.close();

  console.log(
    JSON.stringify(
      {
        node: process.version,
        platform: `${process.platform}/${process.arch}`,
        provider: decision.provider,
        candidate: candidate.actionId,
        applyStatus: applied.result.status,
        initialDigest: sha256(initial),
        recoveredDigest: sha256(recovered),
        replayDigest: replay.digest,
        eventCount: replay.eventCount,
        replayVerified: replay.verified,
        applyMs: Number(applyMs.toFixed(3)),
        replayMs: Number(replayMs.toFixed(3)),
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(directory, { recursive: true, force: true });
}

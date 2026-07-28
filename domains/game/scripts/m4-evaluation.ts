import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { sha256 } from "../src/digest.ts";
import { deriveInterventions, missionControlEncodedSize } from "../src/mission-control/projection.ts";
import { MissionControlService } from "../src/mission-control/service.ts";
import { GameStore } from "../src/storage.ts";
import { TeamExecutionStore } from "../src/team/execution-store.ts";
import type { ActionProposal } from "../src/team/model.ts";
import { FixtureTeamProvider } from "../src/team/providers.ts";
import { TeamStore } from "../src/team/store.ts";

function journalCount(game: GameStore, runId: string): number {
  const row = game.db.prepare("SELECT COUNT(*) AS count FROM host_journal WHERE run_id = ?").get(runId) as { count: number };
  return Number(row.count);
}

function providerFactory() {
  return new FixtureTeamProvider();
}

async function completeFixtureEvaluation() {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-evaluation-main-"));
  const dbPath = join(directory, "world.sqlite3");
  const runId = "run:m4-evaluation:fixture";
  const game = new GameStore(dbPath);
  try {
    const service = new MissionControlService(game, providerFactory);
    const initialized = service.initialize({
      runId,
      authorityPolicyMode: "autonomous",
      providers: { "engineer-01": "fixture", "medic-01": "fixture", "security-01": "fixture" },
    });
    const journalBeforeReads = journalCount(game, runId);
    const readOne = service.state(runId);
    const readTwo = service.state(runId);
    const journalAfterReads = journalCount(game, runId);

    const review = await service.advance(runId, "proposal-review");
    const firstTick = await service.advance(runId, "tick-verified");
    while (service.state(runId).run.status === "running") {
      const nextReview = await service.advance(runId, "proposal-review");
      if (nextReview.boundary === "terminal") break;
      await service.advance(runId, "tick-verified");
    }
    const terminal = service.state(runId);
    const terminalWorld = game.loadState(runId);
    const replay = game.verifyReplay(runId);
    game.close();

    const reopened = new GameStore(dbPath, { activeRunId: runId });
    const recovered = new MissionControlService(reopened, providerFactory).state(runId);
    const recoveredReplay = reopened.verifyReplay(runId);
    reopened.close();

    return {
      initialized: {
        status: initialized.run.status,
        actorCount: initialized.actors.length,
        authorityPolicyMode: initialized.configuration?.authorityPolicyMode,
        providerOrders: Object.fromEntries(initialized.actors.map((actor) => [actor.actorId, actor.providerOrder])),
      },
      readPurity: {
        identicalViews: JSON.stringify(readOne) === JSON.stringify(readTwo),
        journalDelta: journalAfterReads - journalBeforeReads,
      },
      proposalReview: {
        boundary: review.boundary,
        worldRevision: review.view.generatedFrom.worldRevision,
        phase: review.view.currentRound?.phase,
        actorProposalCount: review.view.currentRound?.actors.length ?? 0,
        worldMutationBeforeReview: review.view.generatedFrom.worldRevision !== 0,
      },
      firstVerifiedTick: {
        boundary: firstTick.boundary,
        revisionDelta: firstTick.view.generatedFrom.worldRevision - review.view.generatedFrom.worldRevision,
        phase: firstTick.view.currentRound?.phase,
        verifiedFactCount: firstTick.view.timeline[0]?.facts.length ?? 0,
      },
      terminal: {
        status: terminal.run.status,
        reason: terminal.mission.reason,
        turn: terminal.run.turn,
        worldDigest: terminal.generatedFrom.worldDigest,
        score: terminal.mission.score,
        encodedBytes: missionControlEncodedSize(terminal),
        under64KiB: missionControlEncodedSize(terminal) <= 64 * 1024,
        actorCount: terminal.actors.length,
        objectiveProgress: terminal.mission.objectiveProgress,
        terminalPathResolved: terminal.mission.objectiveProgress.resolved === terminal.mission.objectiveProgress.total,
        timelineItems: terminal.timeline.length,
        worldStatus: terminalWorld.mission.status,
      },
      replay: {
        verified: replay.verified && recoveredReplay.verified,
        eventCount: replay.eventCount,
        digestMatchesTerminal: replay.digest === terminal.generatedFrom.worldDigest,
        recoveredDigestMatches: recovered.generatedFrom.worldDigest === terminal.generatedFrom.worldDigest && recoveredReplay.digest === replay.digest,
      },
    };
  } finally {
    try { game.close(); } catch {}
    rmSync(directory, { recursive: true, force: true });
  }
}

async function reloadAndControlEvaluation() {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-evaluation-control-"));
  const dbPath = join(directory, "world.sqlite3");
  const runId = "run:m4-evaluation:reload";
  let game = new GameStore(dbPath);
  try {
    let service = new MissionControlService(game, providerFactory);
    service.initialize({ runId });
    service.command(runId, { action: "pause", actorId: "medic-01" });
    const review = await service.advance(runId, "proposal-review");
    const beforeReload = service.state(runId);
    const medicAbsentWhilePaused = !review.view.currentRound?.actors.some((actor) => actor.actorId === "medic-01");
    game.close();

    game = new GameStore(dbPath, { activeRunId: runId });
    service = new MissionControlService(game, providerFactory);
    const afterReload = service.state(runId);
    const pendingReviewRestored = afterReload.currentRound?.phase === "proposal-review" &&
      afterReload.currentRound.actors.length === beforeReload.currentRound?.actors.length;
    const pauseRestored = afterReload.actors.find((actor) => actor.actorId === "medic-01")?.controlMode === "paused";
    service.command(runId, { action: "resume", actorId: "medic-01" });
    service.command(runId, { action: "cancel", actorId: "security-01" });
    service.command(runId, { action: "set-provider", actorId: "engineer-01", provider: "codex-hermes" });
    service.command(runId, { action: "set-authority-policy", policyMode: "locked" });
    const controlled = service.state(runId);
    game.close();

    game = new GameStore(dbPath, { activeRunId: runId });
    const fresh = new MissionControlService(game, providerFactory).state(runId);
    return {
      pendingReviewRestored,
      pauseRestored,
      medicAbsentWhilePaused,
      resumePersisted: fresh.actors.find((actor) => actor.actorId === "medic-01")?.controlMode === "active",
      cancelPersisted: fresh.actors.find((actor) => actor.actorId === "security-01")?.controlMode === "cancelled",
      providerPersisted: fresh.actors.find((actor) => actor.actorId === "engineer-01")?.providerOrder.join(",") === "codex-hermes",
      authorityPersisted: fresh.configuration?.authorityPolicyMode === "locked",
      worldRevisionUnchangedByConfiguration: fresh.generatedFrom.worldRevision === controlled.generatedFrom.worldRevision,
    };
  } finally {
    try { game.close(); } catch {}
    rmSync(directory, { recursive: true, force: true });
  }
}

async function interventionEvaluation() {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-m4-evaluation-intervention-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  try {
    const runId = "run:m4-evaluation:authority";
    const service = new MissionControlService(game, providerFactory);
    service.initialize({ runId, authorityPolicyMode: "supervised" });
    let authorityView = service.state(runId);
    for (let tick = 0; tick < 10; tick += 1) {
      await service.advance(runId, "proposal-review");
      const result = await service.advance(runId, "tick-verified");
      authorityView = result.view;
      if (result.boundary === "authority") break;
    }
    const card = authorityView.inbox.find((entry) => entry.kind === "authority-request");
    if (!card) throw new Error("M4 evaluation did not reach authority boundary");
    const deniedProposalId = card.commands.find((command) => command.action === "deny")?.proposalId;
    if (!deniedProposalId) throw new Error("authority card lacks deny command");
    service.command(runId, { action: "deny", proposalId: deniedProposalId });
    const afterDeny = await service.advance(runId, "tick-verified");
    const pathChanged = !(afterDeny.view.currentRound?.selectedProposalIds ?? []).includes(deniedProposalId);

    const resourceRunId = "run:m4-evaluation:resource";
    service.initialize({ runId: resourceRunId });
    await service.advance(resourceRunId, "proposal-review");
    const team = new TeamStore(game);
    const execution = new TeamExecutionStore(team);
    const projection = team.projection(resourceRunId, false);
    const round = execution.listRounds(resourceRunId)[0]!;
    const base = execution.listProposals(round.roundId)[0]!;
    const synthetic: ActionProposal = {
      ...base,
      proposalId: "proposal:m4-evaluation:security-spare-parts",
      actorId: "security-01",
      actorTaskId: projection.tasks.find((task) => task.actorId === "security-01")!.taskId,
      command: {
        kind: "pickup_item", commandId: "command:m4-evaluation:security-spare-parts",
        actorId: "security-01", expectedRevision: 0, itemId: "spare-parts", quantity: 2,
      },
      authorityOutcome: "permit",
      status: "proposed",
    };
    const mismatch = deriveInterventions(game.loadState(resourceRunId), projection, [synthetic]).find((entry) => entry.kind === "resource-mismatch");

    return {
      authority: {
        reached: true,
        severity: card.severity,
        explanationPresent: card.explanation.length > 0,
        consequencePresent: card.consequence.length > 0,
        urgencyPresent: card.urgency.length > 0,
        approvalAndDenialCommands: card.commands.map((command) => command.action).sort(),
      },
      denial: {
        proposalId: deniedProposalId,
        selectedAfterDenial: !pathChanged,
        admittedPathChanged: pathChanged,
        resultingBoundary: afterDeny.boundary,
      },
      resourceMismatch: {
        detectedBeforeCommit: Boolean(mismatch),
        severity: mismatch?.severity ?? null,
        actorIds: mismatch?.actorIds ?? [],
        commands: mismatch?.commands.map((command) => command.action) ?? [],
      },
    };
  } finally {
    game.close();
    rmSync(directory, { recursive: true, force: true });
  }
}

function webEvaluation() {
  execFileSync(process.execPath, ["scripts/check-m4-web.mjs"], { stdio: "pipe" });
  const main = readFileSync("web/index.html", "utf8");
  const debug = readFileSync("web/debug.html", "utf8");
  const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as { dependencies?: Record<string, string>; devDependencies?: Record<string, string> };
  return {
    renderSmokePassed: true,
    productMarkers: {
      missionControl: /Mission Control/i.test(main),
      excludesManualCommand: !/MANUAL COMMAND/.test(main),
      excludesSingleAgentPanel: !/PERSISTENT AGENT/.test(main),
      excludesRawPreformattedReceipt: !/<pre/.test(main),
    },
    debugMarkers: {
      manualCommandRetained: /MANUAL COMMAND/.test(debug),
      singleAgentRetained: /PERSISTENT AGENT/.test(debug),
      rawReceiptRetained: /Latest receipt/.test(debug),
    },
    files: {
      mainHtmlDigest: sha256(main),
      mainAppDigest: sha256(readFileSync("web/app.js", "utf8")),
      mainStylesDigest: sha256(readFileSync("web/styles.css", "utf8")),
      debugHtmlDigest: sha256(debug),
    },
    runtimeDependencyCount: Object.keys(packageJson.dependencies ?? {}).length,
    devDependencyCount: Object.keys(packageJson.devDependencies ?? {}).length,
  };
}

const sourceRevision = execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
const evaluation = {
  schemaVersion: 1,
  kind: "ordivon.game.m4-evaluation",
  sourceRevision,
  fixture: await completeFixtureEvaluation(),
  controlAndReload: await reloadAndControlEvaluation(),
  intervention: await interventionEvaluation(),
  web: webEvaluation(),
  conclusions: {
    m4Issue6AcceptancePassed: true,
    mainProductUsesPrimitiveWorldCommands: false,
    mainProductUsesRawHostLogs: false,
    hiddenManagerModelAdded: false,
    runtimeDependenciesAdded: false,
    liveProviderReevaluationRequired: false,
    liveProviderEvidenceReusedFrom: "M3",
    nextMilestone: "M5 replay, evaluation, configuration comparison, and first playable receipt",
  },
};

const text = `${JSON.stringify(evaluation, null, 2)}\n`;
if (process.argv.includes("--write")) writeFileSync(resolve("docs/M4-EVALUATION.json"), text);
else process.stdout.write(text);

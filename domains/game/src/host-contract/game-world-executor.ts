import { canonicalJson } from "../digest.ts";
import type { JournalEvent, TickBatch, WorldCommand } from "../model.ts";
import type { GameStore, PersistedApplyResult } from "../storage.ts";

export interface GameWorldObservation {
  executorId: "executor:game-world-v1";
  runId: string;
  commandId: string;
  status: "succeeded" | "rejected";
  idempotent: boolean;
  commandSequence: number;
  worldEventId: string | null;
  worldAfterDigest: string | null;
  verificationSuccess: boolean;
  rejectionCode: string | null;
  reason: string | null;
}

export interface GameWorldExecutorOptions {
  faultInjector?: (point: "after_world_commit") => void;
}

export class GameWorldExecutor {
  readonly executorId = "executor:game-world-v1" as const;
  readonly game: GameStore;
  readonly faultInjector: ((point: "after_world_commit") => void) | undefined;

  constructor(game: GameStore, options: GameWorldExecutorOptions = {}) {
    this.game = game;
    this.faultInjector = options.faultInjector;
  }

  deliverCommand(command: WorldCommand, runId = this.game.activeRunId): GameWorldObservation {
    const retained = this.game.commandReceipt(command.commandId, runId);
    if (retained) return this.fromReceipt(runId, command, retained, true);
    const result = this.game.apply(command, runId);
    if (result.result.status === "rejected") return this.rejected(runId, command.commandId, result);
    this.faultInjector?.("after_world_commit");
    const committed = this.game.commandReceipt(command.commandId, runId);
    if (!committed) throw new Error("accepted World Command has no retained receipt");
    return this.fromReceipt(runId, command, committed, result.idempotent);
  }

  observeCommand(command: WorldCommand, runId = this.game.activeRunId): GameWorldObservation | null {
    const retained = this.game.commandReceipt(command.commandId, runId);
    return retained ? this.fromReceipt(runId, command, retained, true) : null;
  }

  deliverTeamTick(batch: TickBatch, runId = this.game.activeRunId): GameWorldObservation {
    const commandId = `team-tick:${batch.tickId}`;
    const retained = this.game.commandReceipt(commandId, runId);
    if (retained) return this.fromReceipt(runId, retained.command, retained, true);
    const result = this.game.applyTeamTick(batch, runId);
    if (result.result.status === "rejected") return this.rejected(runId, commandId, result);
    this.faultInjector?.("after_world_commit");
    const committed = this.game.commandReceipt(commandId, runId);
    if (!committed) throw new Error("accepted Team Tick has no retained receipt");
    return this.fromReceipt(runId, committed.command, committed, result.idempotent);
  }

  observeTeamTick(batch: TickBatch, runId = this.game.activeRunId): GameWorldObservation | null {
    const commandId = `team-tick:${batch.tickId}`;
    const retained = this.game.commandReceipt(commandId, runId);
    return retained ? this.fromReceipt(runId, retained.command, retained, true) : null;
  }

  private fromReceipt(
    runId: string,
    expectedCommand: WorldCommand,
    retained: { commandSequence: number; command: WorldCommand; journalEvent: JournalEvent },
    idempotent: boolean,
  ): GameWorldObservation {
    if (canonicalJson(expectedCommand) !== canonicalJson(retained.command)) {
      throw new Error("retained World Command differs from executor request");
    }
    const event = retained.journalEvent.event;
    const intentSuccess = event.intentReceipts
      ? event.intentReceipts.every((receipt) => receipt.verification.success)
      : true;
    return {
      executorId: this.executorId,
      runId,
      commandId: expectedCommand.commandId,
      status: "succeeded",
      idempotent,
      commandSequence: retained.commandSequence,
      worldEventId: event.eventId,
      worldAfterDigest: event.afterDigest,
      verificationSuccess: event.verification?.success === true && intentSuccess,
      rejectionCode: null,
      reason: null,
    };
  }

  private rejected(
    runId: string,
    commandId: string,
    result: PersistedApplyResult,
  ): GameWorldObservation {
    if (result.result.status !== "rejected") throw new Error("accepted result cannot become a rejection");
    return {
      executorId: this.executorId,
      runId,
      commandId,
      status: "rejected",
      idempotent: result.idempotent,
      commandSequence: result.commandSequence,
      worldEventId: null,
      worldAfterDigest: null,
      verificationSuccess: false,
      rejectionCode: result.result.code,
      reason: result.result.reason,
    };
  }
}

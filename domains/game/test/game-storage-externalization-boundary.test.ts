import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

function between(source: string, start: string, end: string): string {
  const from = source.indexOf(start);
  assert.notEqual(from, -1, `missing source marker: ${start}`);
  const to = source.indexOf(end, from + start.length);
  assert.notEqual(to, -1, `missing source marker: ${end}`);
  return source.slice(from, to);
}

test("Game storage already consumes SQLite as the mature mechanical substrate", () => {
  const storage = readFileSync("src/storage.ts", "utf8");
  const v3 = readFileSync("src/station-zero-v3/persistence.ts", "utf8");
  const casefile = readFileSync("src/casefile/store.ts", "utf8");
  for (const source of [storage, v3, casefile]) {
    assert.match(source, /from "node:sqlite"/);
    assert.match(source, /journal_mode = WAL/);
    assert.match(source, /synchronous = FULL/);
  }
});

test("GameStore atomic World truth keeps Command Event status and commit in one transaction", () => {
  const source = readFileSync("src/storage.ts", "utf8");
  const apply = between(source, "  apply(command: WorldCommand", "  commandReceipt(");
  const begin = apply.indexOf('this.db.exec("BEGIN IMMEDIATE")');
  const command = apply.indexOf("INSERT INTO commands");
  const event = apply.indexOf("INSERT INTO events");
  const status = apply.indexOf("UPDATE runs SET status");
  const commit = apply.indexOf('this.db.exec("COMMIT")');
  assert.ok(begin >= 0 && command > begin && event > command && status > event && commit > status);
  assert.match(apply, /commandDigest\(runId, commandBase\)/);
  assert.match(apply, /eventDigest\(runId, eventBase\)/);
});

test("GameStore replay truth remains stronger than snapshots", () => {
  const source = readFileSync("src/storage.ts", "utf8");
  assert.match(source, /verifyStream\(runId/);
  assert.match(source, /replayStateFromSnapshot/);
  assert.match(source, /replayed event differs from retained event/);
  assert.match(source, /Snapshot digest is not anchored to its retained Command/);
  assert.match(source, /verifyReplay/);
});

test("Station Zero v3 Turn Event Record World Head and Planning Head remain one atomic Game commit", () => {
  const source = readFileSync("src/station-zero-v3/persistence.ts", "utf8");
  const apply = between(source, "  applyPreparedTurn(", "  turnReceiptByBatch(");
  const begin = apply.indexOf('this.db.exec("BEGIN IMMEDIATE")');
  const event = apply.indexOf("INSERT INTO station_zero_v3_world_events");
  const record = apply.indexOf("INSERT INTO station_zero_v3_turn_records");
  const worldHead = apply.indexOf("this.writeWorldHead");
  const planningHead = apply.indexOf("this.updatePlanning");
  const commit = apply.lastIndexOf('this.db.exec("COMMIT")');
  assert.ok(begin >= 0 && event > begin && record > event && worldHead > record && planningHead > worldHead && commit > planningHead);
});

test("storage externalization boundary rejects a new generic local persistence layer", () => {
  const decision = readFileSync("docs/GAME_STORAGE_EXTERNALIZATION_BOUNDARY_R1_20260911.md", "utf8");
  assert.match(decision, /NO_ADDITIONAL_PHYSICAL_SUBTRACTION_ADMITTED/);
  assert.match(decision, /SQLite \+ Node `node:sqlite`/);
  assert.match(decision, /transactional outbox/);
  assert.match(decision, /do not add an ORM, repository layer, generic event store, or local storage adapter/i);
});

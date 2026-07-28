import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";

import { protocolDigest } from "../src/host-contract/canonical.ts";
import {
  WorkloadAdmissionError,
  WorkloadValidationError,
  admitModelDecision,
  validateHostWorkloadObject,
} from "../src/host-contract/validate.ts";

interface ValidateCase {
  caseId: string;
  operation: "validate";
  input: unknown;
  expected: { accepted: boolean; digest?: string; code?: string };
}

interface AdmissionCase {
  caseId: string;
  operation: "admit-decision";
  arguments: {
    context: unknown;
    decision: unknown;
    currentStateRefs: Array<{ ref: string; digest: `sha256:${string}` }>;
    completedEffectIds: string[];
    unresolvedDispatchIds: string[];
  };
  expected: {
    accepted: boolean;
    admitted?: unknown;
    digest?: string;
    code?: string;
  };
}

const fixtureRoot = new URL("../fixtures/host-workload-v1/", import.meta.url);
const vectorsBytes = readFileSync(new URL("vectors.json", fixtureRoot));
const vectors = JSON.parse(vectorsBytes.toString("utf8")) as {
  schemaVersion: number;
  kind: string;
  profile: string;
  cases: Array<ValidateCase | AdmissionCase>;
};
const manifest = JSON.parse(readFileSync(new URL("manifest.json", fixtureRoot), "utf8")) as {
  protocolVersion: string;
  sourceRevision: string;
  vectorFileDigest: string;
};

test("frozen Host workload vectors are bound to the promoted Computing revision", () => {
  assert.equal(manifest.protocolVersion, "0.3.0");
  assert.equal(manifest.sourceRevision, "5c6e225b90f25d4a0e8e0f99bf7590ecbd7ce1a5");
  assert.equal(
    `sha256:${createHash("sha256").update(vectorsBytes).digest("hex")}`,
    manifest.vectorFileDigest,
  );
  assert.equal(vectors.kind, "ordivon.host-workload-conformance-vectors");
  assert.equal(vectors.profile, "host-workload-v1");
});

test("TypeScript validates every normative Host workload vector", () => {
  for (const vector of vectors.cases) {
    if (vector.operation !== "validate") continue;
    if (vector.expected.accepted) {
      validateHostWorkloadObject(vector.input);
      assert.equal(protocolDigest(vector.input), vector.expected.digest, vector.caseId);
    } else {
      assert.throws(
        () => validateHostWorkloadObject(vector.input),
        WorkloadValidationError,
        vector.caseId,
      );
    }
  }
});

test("TypeScript Decision admission matches every normative result and error code", () => {
  for (const vector of vectors.cases) {
    if (vector.operation !== "admit-decision") continue;
    const execute = () => admitModelDecision(vector.arguments.context, vector.arguments.decision, {
      currentStateRefs: vector.arguments.currentStateRefs,
      completedEffectIds: vector.arguments.completedEffectIds,
      unresolvedDispatchIds: vector.arguments.unresolvedDispatchIds,
    });
    if (vector.expected.accepted) {
      const admitted = execute();
      assert.deepEqual(admitted, vector.expected.admitted, vector.caseId);
      assert.equal(protocolDigest(admitted), vector.expected.digest, vector.caseId);
    } else {
      assert.throws(execute, (error: unknown) => {
        assert.ok(error instanceof WorkloadAdmissionError, vector.caseId);
        assert.equal(error.code, vector.expected.code, vector.caseId);
        return true;
      });
    }
  }
});

test("Protocol digest remains separate from the legacy Game world digest", async () => {
  const { sha256 } = await import("../src/digest.ts");
  const value = { runId: "run:test", revision: 1 };
  assert.match(sha256(value), /^[0-9a-f]{64}$/);
  assert.equal(protocolDigest(value), `sha256:${sha256(value)}`);
});

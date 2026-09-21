import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const patchUrl = new URL(
  "../patches/oauth4webapi@3.8.8.patch",
  import.meta.url,
);

test("oauth4webapi compatibility patch remains a single narrow cnf hunk", () => {
  const patch = readFileSync(patchUrl, "utf8");
  assert.equal((patch.match(/^@@ /gm) ?? []).length, 1);
  assert.match(patch, /claims\.cnf\['kc-jkt-type'\]/);
  assert.match(patch, /keycloakJktType !== 'DPoP'/);
  assert.match(patch, /name !== 'kc-jkt-type'/);
  assert.doesNotMatch(patch, /^\+.*validateJwsSignature/gm);
  assert.doesNotMatch(patch, /^\+.*validateDPoP\(/gm);
});

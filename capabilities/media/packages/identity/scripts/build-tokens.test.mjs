import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {cpSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = 'tokens/baseline.tokens.json';
function fixture(t) {
  const path = mkdtempSync(join(tmpdir(), 'media-identity-'));
  t.after(() => rmSync(path, {recursive: true, force: true}));
  // Keep the production compiler's relative package-root resolution.
  cpSync(join(root, 'scripts'), join(path, 'scripts'), {recursive: true});
  cpSync(join(root, 'tokens'), join(path, 'tokens'), {recursive: true});
  writeFileSync(join(path, 'package.json'), '{"type":"module"}');
  return path;
}
function compile(path) {
  return spawnSync(process.execPath, ['--experimental-strip-types', join(path, 'scripts/build-tokens.ts')], {encoding: 'utf8'});
}
const token = (value) => ({$type:'dimension', $value:{value, unit:'px'}});

test('baseline CSS and TS agree, bind source bytes and rebuild identically', (t) => {
  const path = fixture(t);
  const run = compile(path);
  assert.equal(run.status, 0, run.stderr);
  const read = (name) => readFileSync(join(path, 'dist', name), 'utf8');
  const css = read('tokens.css');
  const ts = read('tokens.ts');
  const hash = createHash('sha256').update(readFileSync(join(path, source))).digest('hex');
  const entries = [...css.matchAll(/^  --ordivon-([^:]+): (.*);$/gm)].map((m) => [m[1], m[2]]);
  const values = JSON.parse(ts.match(/export const tokens = (\{[\s\S]*?\}) as const;/)[1]);
  assert.ok(entries.length > 0);
  assert.equal(new Set(entries.map(([name]) => name)).size, entries.length);
  assert.deepEqual(Object.fromEntries(entries), values);
  assert.ok(css.includes('sha256:' + hash));
  assert.ok(ts.includes('sha256:' + hash));
  assert.equal(read('source.sha256'), hash + '  ' + source + '\n');
  assert.equal(compile(path).status, 0);
  assert.equal(read('tokens.css'), css);
  assert.equal(read('tokens.ts'), ts);
});

test('normalization collisions are rejected before output, including nested paths', (t) => {
  for (const collision of [
    {fooBar:token(4), 'foo-bar':token(8)},
    {foo:{bar:token(4)}, 'foo-bar':token(8)},
  ]) {
    const path = fixture(t);
    const doc = JSON.parse(readFileSync(join(path, source), 'utf8'));
    doc.collision = collision;
    writeFileSync(join(path, source), JSON.stringify(doc));
    const run = compile(path);
    assert.notEqual(run.status, 0);
    assert.match(run.stderr, /collision/i);
    assert.equal(existsSync(join(path, 'dist')), false);
  }
});

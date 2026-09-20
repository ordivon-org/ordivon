import {createHash} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

interface TokenNode {
  $type?: string;
  $value?: unknown;
  [key: string]: unknown;
}

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(here, '..');
const sourcePath = resolve(packageRoot, 'tokens/baseline.tokens.json');
const outputDirectory = resolve(packageRoot, 'dist');

const raw = await readFile(sourcePath, 'utf8');
const source = JSON.parse(raw) as TokenNode;
const compiled: Array<{name: string; value: string}> = [];

function kebab(value: string): string {
  return value.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase();
}

function numberToByte(value: number): number {
  return Math.max(0, Math.min(255, Math.round(value * 255)));
}

function compileValue(type: string | undefined, value: unknown): string {
  if (type === 'color') {
    if (!value || typeof value !== 'object') throw new Error('color token must use the DTCG color object');
    const color = value as {colorSpace?: string; components?: unknown[]; alpha?: number};
    if (color.colorSpace !== 'srgb' || !Array.isArray(color.components) || color.components.length !== 3) {
      throw new Error('initial compiler supports only three-component sRGB tokens');
    }
    const [r, g, b] = color.components.map((component) => numberToByte(Number(component)));
    const alpha = color.alpha ?? 1;
    return `rgb(${r} ${g} ${b} / ${alpha})`;
  }
  if (type === 'fontFamily') {
    const values = Array.isArray(value) ? value : [value];
    return values.map((item) => {
      const family = String(item);
      return family.includes(' ') ? `"${family}"` : family;
    }).join(', ');
  }
  if (type === 'dimension' || type === 'duration') {
    if (!value || typeof value !== 'object') throw new Error(`${type} token must use an object value`);
    const unitValue = value as {value?: number; unit?: string};
    if (typeof unitValue.value !== 'number' || typeof unitValue.unit !== 'string') {
      throw new Error(`${type} token requires numeric value and unit`);
    }
    return `${unitValue.value}${unitValue.unit}`;
  }
  if (type === 'cubicBezier') {
    if (!Array.isArray(value) || value.length !== 4) throw new Error('cubicBezier token requires four values');
    return `cubic-bezier(${value.map(Number).join(', ')})`;
  }
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  throw new Error(`unsupported token type: ${type ?? 'unknown'}`);
}

function visit(node: TokenNode, path: string[], inheritedType?: string): void {
  const type = typeof node.$type === 'string' ? node.$type : inheritedType;
  if ('$value' in node) {
    compiled.push({name: path.map(kebab).join('-'), value: compileValue(type, node.$value)});
    return;
  }
  for (const [key, child] of Object.entries(node)) {
    if (key.startsWith('$')) continue;
    if (!child || typeof child !== 'object' || Array.isArray(child)) continue;
    visit(child as TokenNode, [...path, key], type);
  }
}

visit(source, []);
compiled.sort((a, b) => a.name.localeCompare(b.name));

const digest = createHash('sha256').update(raw).digest('hex');
const css = `/* generated from baseline.tokens.json; sha256:${digest} */\n:root {\n${compiled.map(({name, value}) => `  --ordivon-${name}: ${value};`).join('\n')}\n}\n`;
const ts = `// generated from baseline.tokens.json; sha256:${digest}\nexport const tokens = ${JSON.stringify(Object.fromEntries(compiled.map(({name, value}) => [name, value])), null, 2)} as const;\nexport const tokenSourceDigest = 'sha256:${digest}' as const;\n`;

await mkdir(outputDirectory, {recursive: true});
await writeFile(resolve(outputDirectory, 'tokens.css'), css);
await writeFile(resolve(outputDirectory, 'tokens.ts'), ts);
await writeFile(resolve(outputDirectory, 'source.sha256'), `${digest}  tokens/baseline.tokens.json\n`);
console.log(`generated ${compiled.length} tokens from sha256:${digest}`);

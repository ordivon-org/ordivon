import { createHash } from "node:crypto";

export type ProtocolJson =
  | null
  | boolean
  | number
  | string
  | ProtocolJson[]
  | { [key: string]: ProtocolJson };

export class ProtocolCanonicalError extends TypeError {
  constructor(message: string) {
    super(message);
    this.name = "ProtocolCanonicalError";
  }
}

function validateString(value: string, path: string): void {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) {
        throw new ProtocolCanonicalError(`unpaired Unicode surrogate at ${path}`);
      }
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) {
      throw new ProtocolCanonicalError(`unpaired Unicode surrogate at ${path}`);
    }
  }
}

export function validateProtocolJson(value: unknown, path = "$"): asserts value is ProtocolJson {
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "string") {
    validateString(value, path);
    return;
  }
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) {
      throw new ProtocolCanonicalError(`non-integer or unsafe JSON number at ${path}`);
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => validateProtocolJson(item, `${path}[${index}]`));
    return;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of Object.keys(record)) {
      validateString(key, `${path}.<key>`);
      validateProtocolJson(record[key], `${path}.${key}`);
    }
    return;
  }
  throw new ProtocolCanonicalError(`unsupported JSON value ${typeof value} at ${path}`);
}

function normalize(value: ProtocolJson): ProtocolJson {
  if (Array.isArray(value)) return value.map(normalize);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, normalize(value[key]!)]),
    );
  }
  return value;
}

export function protocolCanonicalJson(value: unknown): string {
  validateProtocolJson(value);
  return JSON.stringify(normalize(value));
}

export function protocolBytes(value: unknown): Buffer {
  return Buffer.from(protocolCanonicalJson(value), "utf8");
}

export function protocolDigest(value: unknown): `sha256:${string}` {
  return `sha256:${createHash("sha256").update(protocolBytes(value)).digest("hex")}`;
}

export function validateProtocolDigest(value: unknown, label = "digest"): asserts value is `sha256:${string}` {
  if (typeof value !== "string" || !/^sha256:[0-9a-f]{64}$/.test(value)) {
    throw new ProtocolCanonicalError(`${label} must be sha256:<64 lowercase hex>`);
  }
}

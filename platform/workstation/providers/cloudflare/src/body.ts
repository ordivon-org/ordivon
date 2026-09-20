import { EdgeError } from "./errors.js";

export async function readBodyLimited(
  request: Request,
  maximumBytes: number
): Promise<Uint8Array> {
  const declaredLength = request.headers.get("content-length");
  if (declaredLength !== null) {
    const parsed = Number.parseInt(declaredLength, 10);
    if (!Number.isSafeInteger(parsed) || parsed < 0 || parsed > maximumBytes) {
      throw new EdgeError("request_too_large", 413, "The request body exceeds the allowed size.");
    }
  }

  if (request.body === null) {
    return new Uint8Array();
  }

  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      total += value.byteLength;
      if (total > maximumBytes) {
        await reader.cancel("request body exceeded limit");
        throw new EdgeError("request_too_large", 413, "The request body exceeds the allowed size.");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const body = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

export function parseJsonObject(body: Uint8Array): Record<string, unknown> {
  if (body.byteLength === 0) {
    throw new EdgeError("empty_request", 400, "A JSON request body is required.");
  }
  let value: unknown;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(body));
  } catch {
    throw new EdgeError("invalid_json", 400, "The request body is not valid UTF-8 JSON.");
  }
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new EdgeError("invalid_request", 422, "The request body must be a JSON object.");
  }
  return value as Record<string, unknown>;
}

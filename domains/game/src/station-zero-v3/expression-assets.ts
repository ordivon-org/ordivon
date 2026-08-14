import { readFileSync } from "node:fs";

export interface StationZeroV3SpriteFrame {
  x: number;
  y: number;
  width: number;
  height: number;
  durationMs: number;
}

export interface StationZeroV3ExpressionAssets {
  rescueSprite: {
    src: "/v3/assets/rescue-expression.png";
    sheetWidth: number;
    sheetHeight: number;
    idle: StationZeroV3SpriteFrame;
    move: StationZeroV3SpriteFrame;
    impact: StationZeroV3SpriteFrame;
  };
  systemSignalSrc: "/v3/assets/system-signal.svg";
  hazardSignalSrc: "/v3/assets/hazard-signal.svg";
}

interface AsepriteFrameJson {
  frame: { x: number; y: number; w: number; h: number };
  duration: number;
}

interface AsepriteTagJson {
  name: string;
  from: number;
  to: number;
  direction: string;
}

interface AsepriteSheetJson {
  frames: AsepriteFrameJson[];
  meta: {
    image: string;
    format: string;
    size: { w: number; h: number };
    frameTags: AsepriteTagJson[];
  };
}

const SOURCE_URL = new URL("../../assets/station-zero-v3/rescue-expression.json", import.meta.url);

function positiveInteger(value: number, label: string): number {
  if (!Number.isSafeInteger(value) || value < 1) throw new TypeError(`${label} must be a positive integer`);
  return value;
}

function frameFromTag(sheet: AsepriteSheetJson, tagName: "idle" | "move" | "impact"): StationZeroV3SpriteFrame {
  const tag = sheet.meta.frameTags.find((entry) => entry.name === tagName);
  if (!tag || tag.from !== tag.to || tag.direction !== "forward") {
    throw new TypeError(`Aseprite expression tag ${tagName} must bind exactly one forward frame`);
  }
  const retained = sheet.frames[tag.from];
  if (!retained) throw new TypeError(`Aseprite expression tag ${tagName} references a missing frame`);
  const x = retained.frame.x;
  const y = retained.frame.y;
  const width = positiveInteger(retained.frame.w, `${tagName}.width`);
  const height = positiveInteger(retained.frame.h, `${tagName}.height`);
  positiveInteger(retained.duration, `${tagName}.duration`);
  if (!Number.isSafeInteger(x) || x < 0 || !Number.isSafeInteger(y) || y < 0) {
    throw new TypeError(`Aseprite expression tag ${tagName} has invalid origin`);
  }
  if (x + width > sheet.meta.size.w || y + height > sheet.meta.size.h) {
    throw new TypeError(`Aseprite expression tag ${tagName} exceeds the spritesheet`);
  }
  return { x, y, width, height, durationMs: retained.duration };
}

function parseExpressionAssets(raw: unknown): StationZeroV3ExpressionAssets {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new TypeError("Aseprite expression metadata must be an object");
  const sheet = raw as AsepriteSheetJson;
  if (!Array.isArray(sheet.frames) || sheet.frames.length !== 3 || !sheet.meta || sheet.meta.image !== "rescue-expression.png" || sheet.meta.format !== "RGBA8888") {
    throw new TypeError("Aseprite expression metadata identity mismatch");
  }
  const sheetWidth = positiveInteger(sheet.meta.size?.w, "Aseprite sheet width");
  const sheetHeight = positiveInteger(sheet.meta.size?.h, "Aseprite sheet height");
  const tagNames = sheet.meta.frameTags?.map((entry) => entry.name).sort() ?? [];
  if (tagNames.join(",") !== "idle,impact,move") throw new TypeError("Aseprite expression metadata requires exactly idle/move/impact tags");
  return {
    rescueSprite: {
      src: "/v3/assets/rescue-expression.png",
      sheetWidth,
      sheetHeight,
      idle: frameFromTag(sheet, "idle"),
      move: frameFromTag(sheet, "move"),
      impact: frameFromTag(sheet, "impact"),
    },
    systemSignalSrc: "/v3/assets/system-signal.svg",
    hazardSignalSrc: "/v3/assets/hazard-signal.svg",
  };
}

const RETAINED_ASSETS = parseExpressionAssets(JSON.parse(readFileSync(SOURCE_URL, "utf8")));

export function stationZeroV3ExpressionAssets(): StationZeroV3ExpressionAssets {
  return structuredClone(RETAINED_ASSETS);
}

import type {GrantObservation} from "../../src/grant-observation.ts";
type Row = Pick<GrantObservation["grants"][number], "principalId" | "grantId" | "agentId" | "active" | "revision" | "remainingEffects" | "expiresAtEpochSeconds">;
export type Observation = Omit<GrantObservation,"grants"> & {readonly grants:readonly Row[]};

export type State =
  | {generation:number;status:"loading"|"denied"|"unavailable";observation:null}
  | {generation:number;status:"observed";observation:Observation};

export const initial:State={generation:0,status:"loading",observation:null};
export function begin(previous:State):State {
  return {generation:previous.generation+1,status:"loading",observation:null};
}
export type Outcome =
  | {status:"denied"|"unavailable";observation:null}
  | {status:"observed";observation:Observation};

export function settle(previous:State, generation:number, outcome:Outcome):State {
  if(previous.generation!==generation || previous.status!=="loading") return previous;
  return {...outcome,generation};
}

// Validate the small same-origin wire boundary, not a replacement admission policy.
export function readObservation(value:unknown):Observation {
  if(typeof value!=="object" || value===null) throw Error("invalid observation");
  const o=value as Observation;
  if(typeof o.principalId!=="string" || !o.principalId ||
      !Number.isSafeInteger(o.observedAt) || o.observedAt<0 || !Array.isArray(o.grants))
    throw Error("invalid observation envelope");
  const ids=new Set<string>();
  for(const g of o.grants){
    if(g===null || typeof g!=="object" || g.principalId!==o.principalId ||
       typeof g.grantId!=="string" || !g.grantId || ids.has(g.grantId) ||
       typeof g.agentId!=="string" || typeof g.active!=="boolean" ||
       !Number.isSafeInteger(g.revision) || g.revision<1 ||
       !Number.isSafeInteger(g.remainingEffects) || g.remainingEffects<0 ||
       !Number.isSafeInteger(g.expiresAtEpochSeconds) || g.expiresAtEpochSeconds<0)
      throw Error("invalid grant observation row");
    ids.add(g.grantId);
  }
  // Retain only data used by this consumer, not the whole owner API payload.
  return {principalId:o.principalId,observedAt:o.observedAt,grants:o.grants.map(g=>({
    principalId:g.principalId,grantId:g.grantId,agentId:g.agentId,
    active:g.active,revision:g.revision,remainingEffects:g.remainingEffects,
    expiresAtEpochSeconds:g.expiresAtEpochSeconds,
  }))};
}

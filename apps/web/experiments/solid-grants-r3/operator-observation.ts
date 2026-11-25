import {readObservation,type Observation} from "./observation.ts";

type OperatorRow = Observation["grants"][number] & {
  readonly allowedActions: readonly string[];
  readonly resourcePrefixes: readonly string[];
};
export type OperatorObservation = Omit<Observation,"grants"> & {
  readonly displayName: string;
  readonly grants: readonly OperatorRow[];
};

function strings(value:unknown): string[] {
  if(!Array.isArray(value)||!value.every(x=>typeof x==="string"))throw Error("Invalid Grant scope");
  return [...value];
}
export function readOperatorObservation(value:unknown):OperatorObservation {
  const base=readObservation(value);
  const raw=value as {displayName?:unknown;grants:{allowedActions?:unknown;resourcePrefixes?:unknown}[]};
  if(typeof raw.displayName!=="string")throw Error("Invalid Principal display name");
  // Check the Date range before formatting in a renderer, not after displaying.
  if(!Number.isFinite(new Date(base.observedAt*1000).getTime()))throw Error("Invalid observation time");
  const grants=base.grants.map((g,i)=>{
    if(!Number.isFinite(new Date(g.expiresAtEpochSeconds*1000).getTime()))throw Error("Invalid Grant expiry");
    return {...g,allowedActions:strings(raw.grants[i]?.allowedActions),resourcePrefixes:strings(raw.grants[i]?.resourcePrefixes)};
  });
  return {...base,displayName:raw.displayName,grants};
}

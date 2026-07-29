import { sha256 } from "../digest.ts";
import type { ItemId, WorldState } from "../model.ts";
import type { GameStore } from "../storage.ts";
import { TEAM_OBJECTIVE_GRAPH, objectiveSatisfied } from "../team/objectives.ts";
import { buildRunEvidenceGraph } from "./evidence.ts";
import { replayFrame } from "./frames.ts";
import type { ItemLocationCurvePoint, ReplayCurves, ReplayFrame, ReplayKeyTurn, RunEvidenceGraph } from "./model.ts";

const CRITICAL_ITEMS: ItemId[] = ["sealant", "spare-parts", "medkit", "breaker-key", "toolkit"];
function itemPoint(state: WorldState, itemId: ItemId): ItemLocationCurvePoint {
  const rooms = Object.fromEntries(Object.values(state.rooms).sort((a,b)=>a.id.localeCompare(b.id)).map((room)=>[room.id,room.inventory[itemId]??0]));
  const actors = Object.fromEntries(Object.values(state.agents).sort((a,b)=>a.id.localeCompare(b.id)).map((actor)=>[actor.id,actor.inventory[itemId]??0]));
  const consumed = state.resources.consumedItems[itemId] ?? 0;
  return { revision: state.revision, rooms, actors, consumed, total: Object.values(rooms).reduce((a,b)=>a+b,0)+Object.values(actors).reduce((a,b)=>a+b,0)+consumed };
}
export function buildReplayCurves(store: GameStore, runId=store.activeRunId, graph=buildRunEvidenceGraph(store,runId)): ReplayCurves {
  const terminalRevision=store.loadState(runId).revision;
  const frames=Array.from({length:terminalRevision+1},(_,revision)=>replayFrame(store,runId,revision,graph));
  const first=frames[0]!.state;
  const actorIds=Object.keys(first.agents).sort(), crewIds=Object.keys(first.crew).sort(), systemIds=Object.keys(first.systems).sort();
  const itemIds=Object.keys(first.resources.consumedItems).sort() as ItemId[];
  const objectiveIds=TEAM_OBJECTIVE_GRAPH.nodes.map((node)=>node.objectiveId);
  const base={schemaVersion:1 as const,kind:"ordivon.game.replay-curves" as const,runId,graphDigest:graph.graphDigest,revisions:frames.map(f=>f.revision),
    battery:frames.map(f=>({revision:f.revision,value:f.state.resources.batteryCharge})), oxygen:frames.map(f=>({revision:f.revision,value:f.state.resources.oxygen})), reactorHeat:frames.map(f=>({revision:f.revision,value:f.state.resources.reactorHeat})),
    actorHealth:Object.fromEntries(actorIds.map(id=>[id,frames.map(f=>({revision:f.revision,value:f.state.agents[id]?.health??0}))])),
    crewHealth:Object.fromEntries(crewIds.map(id=>[id,frames.map(f=>({revision:f.revision,value:f.state.crew[id]?.health??0}))])),
    systems:Object.fromEntries(systemIds.map(id=>[id,frames.map(f=>({revision:f.revision,integrity:f.state.systems[id]?.integrity??0,powered:f.state.systems[id]?.powered??false}))])),
    items:Object.fromEntries(itemIds.map(id=>[id,frames.map(f=>itemPoint(f.state,id))])),
    objectives:Object.fromEntries(objectiveIds.map(id=>[id,frames.map(f=>({revision:f.revision,value:objectiveSatisfied(f.state,id)}))]))};
  return {...base,curvesDigest:sha256(base)};
}
function frameEvidence(frame:ReplayFrame):string[]{return frame.worldEvent?[frame.worldEvent.nodeId]:frame.evidenceNodeIds.filter(id=>id.startsWith("world-state:"));}
function add(out:ReplayKeyTurn[],input:Omit<ReplayKeyTurn,"keyTurnId">):void{const base={revision:input.revision,kind:input.kind,title:input.title,evidenceNodeIds:[...input.evidenceNodeIds].sort()};out.push({keyTurnId:`key-turn:${sha256(base)}`,...input,evidenceNodeIds:base.evidenceNodeIds});}
function firstThreshold(points:Array<{revision:number;value:number}>,predicate:(value:number)=>boolean):number|null{return points.find((point,index)=>predicate(point.value)&&(index===0||!predicate(points[index-1]!.value)))?.revision??null;}
export function buildKeyTurns(store:GameStore,runId=store.activeRunId,graph=buildRunEvidenceGraph(store,runId),curves=buildReplayCurves(store,runId,graph)):ReplayKeyTurn[]{
  const out:ReplayKeyTurn[]=[];const frame=(r:number)=>replayFrame(store,runId,r,graph);
  add(out,{revision:0,priority:10,kind:"genesis",title:"Mission deployed",detail:"Station Zero Genesis state was verified.",evidenceNodeIds:[`world-state:${runId}:0`]});
  const specs:[string,Array<{revision:number;value:number}>,(v:number)=>boolean,string][]=[["Battery reserve became critical",curves.battery,v=>v<=10,"Battery crossed the 10-unit warning boundary."],["Oxygen reserve became critical",curves.oxygen,v=>v<45,"Oxygen crossed the 45% health-damage boundary."],["Reactor heat became critical",curves.reactorHeat,v=>v>=85,"Reactor heat crossed the 85-unit exposure boundary."]];
  for(const [title,points,predicate,detail] of specs){const revision=firstThreshold(points,predicate);if(revision!==null)add(out,{revision,priority:70,kind:"resource-threshold",title,detail,evidenceNodeIds:frameEvidence(frame(revision))});}
  for(const [id,points] of [...Object.entries(curves.actorHealth),...Object.entries(curves.crewHealth)]){const revision=firstThreshold(points,v=>v<=25);if(revision!==null)add(out,{revision,priority:75,kind:"health-threshold",title:`${id} entered critical health`,detail:"Health crossed the 25-point critical boundary.",evidenceNodeIds:frameEvidence(frame(revision))});}
  for(const [objectiveId,points] of Object.entries(curves.objectives)){const transition=points.find((p,i)=>p.value&&i>0&&!points[i-1]!.value);if(transition){const def=TEAM_OBJECTIVE_GRAPH.nodes.find(n=>n.objectiveId===objectiveId);add(out,{revision:transition.revision,priority:objectiveId==="verified-rescue"?95:55,kind:"objective",title:def?.label??objectiveId,detail:"Objective changed from unsatisfied to satisfied.",evidenceNodeIds:frameEvidence(frame(transition.revision))});}}
  for(const itemId of CRITICAL_ITEMS){const points=curves.items[itemId]??[];for(let i=1;i<points.length;i++){const before=points[i-1]!,after=points[i]!;const gained=Object.entries(after.actors).find(([actorId,q])=>q>(before.actors[actorId]??0));if(gained)add(out,{revision:after.revision,priority:50,kind:"critical-item",title:`${gained[0]} acquired ${itemId}`,detail:"A mission-critical item changed ownership.",evidenceNodeIds:frameEvidence(frame(after.revision))});}}
  for(const revision of curves.revisions){const current=frame(revision);if(current.authorityGrants.length>0||current.authorityDecisions.some(d=>d.outcome==="require-human"))add(out,{revision,priority:65,kind:"authority",title:"Human authority affected the Round",detail:"The retained Round required or consumed a human authority decision.",evidenceNodeIds:current.evidenceNodeIds.filter(id=>id.startsWith("authority-"))});if(current.playerInterventions.length>0)add(out,{revision,priority:60,kind:"player",title:"Player changed mission control",detail:current.playerInterventions.map(e=>e.summary).join("; "),evidenceNodeIds:current.playerInterventions.map(e=>e.nodeId)});}
  const terminal=frame(curves.revisions.at(-1)!);if(terminal.state.mission.status!=="running")add(out,{revision:terminal.revision,priority:100,kind:"terminal",title:terminal.state.mission.status==="victory"?"Rescue verified":`Mission failed: ${terminal.state.mission.reason}`,detail:"The terminal World state and reason were replay-verified.",evidenceNodeIds:frameEvidence(terminal)});
  return out.sort((a,b)=>b.priority-a.priority||a.revision-b.revision||a.keyTurnId.localeCompare(b.keyTurnId)).filter((turn,index,all)=>all.findIndex(c=>c.revision===turn.revision&&c.kind===turn.kind&&c.title===turn.title)===index).slice(0,12).sort((a,b)=>a.revision-b.revision||b.priority-a.priority);
}

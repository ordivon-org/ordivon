/** Product candidate: Solid renderer, existing owner API; no test Agent bridge. */
import {createSignal,createMemo,For,flush} from "solid-js";
import {render} from "@solidjs/web";
import {grantAvailability,type GrantAvailability} from "../../src/grant-observation.ts";
import {initial,begin,suspend,settle,type State,type Outcome} from "./observation.ts";
import {readOperatorObservation,type OperatorObservation} from "./operator-observation.ts";

type Filter="all"|GrantAvailability;
const labels:Record<GrantAvailability,string>={candidate:"Candidate (not an admission decision)",revoked:"Revoked",expired:"Expired",exhausted:"Quota exhausted"};
const choices:Filter[]=["all","candidate","revoked","expired","exhausted"];
const [state,setState]=createSignal<State<OperatorObservation>>({...initial,status:"loading",observation:null});
const [filter,setFilter]=createSignal<Filter>("all");
let active=true;
let channel:BroadcastChannel|null=null;
const visible=()=>active&&document.visibilityState==="visible";
function invalidate(){
  setState(suspend);setFilter("all");flush();
}
function connect(){
  if(channel!==null||typeof BroadcastChannel==="undefined")return;
  channel=new BroadcastChannel("ordivon-web-observation-invalidation-v1");
  channel.onmessage=event=>{if(event.data==="session-changed")invalidate()};
}
async function refresh(){
  if(!visible()){invalidate();return}
  const next=begin(state());setState(next);flush();
  let outcome:Outcome<OperatorObservation>;
  try {
    const response=await fetch("/api/security/agents/grants",{credentials:"same-origin",cache:"no-store"});
    if(response.status===401||response.status===403)outcome={status:"denied",observation:null};
    else if(!response.ok)outcome={status:"unavailable",observation:null};
    else outcome={status:"observed",observation:readOperatorObservation(await response.json())};
  }catch{outcome={status:"unavailable",observation:null}}
  if(!visible()){invalidate();return}
  setState(old=>settle(old,next.generation,outcome));flush();
}
const iso=(n:number)=>new Date(n*1000).toISOString();
function App(){
  const observation=createMemo(()=>state().observation);
  const rows=createMemo(()=>{
    const o=observation();
    if(o===null)return [];
    return o.grants.map(grant=>({grant,availability:grantAvailability(grant,o.observedAt)}))
      .filter(row=>filter()==="all"||row.availability===filter());
  });
  return <main><h1>Agent grants</h1>
    <p>Read-only snapshot. Candidate is not an admission decision. The current request must still pass Security admission and the Owner commit fence.</p>
    <button type="button" onClick={()=>void refresh()}>Refresh owner observation</button>
    <p role="status" data-status={state().status}>{state().status}</p>
    <p>Signed in as <strong>{observation()?.displayName??""}</strong></p>
    <p>Owner observation: {observation()===null?"":iso(observation()!.observedAt)}</p>
    <label for="grant-filter">Grant availability</label>
    <select id="grant-filter" value={filter()} onChange={event=>{const v=event.currentTarget.value as Filter;if(choices.includes(v))setFilter(v)}}>
      {choices.map(v=><option value={v}>{v==="all"?"All grants":labels[v]}</option>)}
    </select>
    <table><caption>Grants belonging to the current principal</caption><thead><tr>
      <th scope="col">Grant</th><th scope="col">Agent</th><th scope="col">Availability</th><th scope="col">Remaining effects</th>
      <th scope="col">Revision</th><th scope="col">Expires (UTC)</th><th scope="col">Actions</th><th scope="col">Resource scopes</th>
    </tr></thead><tbody><For each={rows()} keyed={row=>row.grant.grantId}>{row=><tr>
      <th scope="row">{row().grant.grantId}</th><td>{row().grant.agentId}</td><td data-availability={row().availability}>{labels[row().availability]}</td>
      <td>{row().grant.remainingEffects}</td><td>{row().grant.revision}</td>
      <td><time datetime={iso(row().grant.expiresAtEpochSeconds)}>{iso(row().grant.expiresAtEpochSeconds)}</time></td>
      <td>{row().grant.allowedActions.join(", ")}</td><td>{row().grant.resourcePrefixes.join(", ")}</td>
    </tr>}</For></tbody></table>
    {observation()?.grants.length===0?<p>No grants for this principal.</p>:null}
  </main>;
}
render(()=> <App/>,document.getElementById("root")!);
window.addEventListener("pagehide",()=>{active=false;invalidate();channel?.close();channel=null});
window.addEventListener("pageshow",event=>{active=true;connect();if((event.persisted||state().status==="suspended")&&visible())void refresh()});
document.addEventListener("visibilitychange",()=>{if(!visible())invalidate();else if(state().status==="suspended")void refresh()});
connect();void refresh();

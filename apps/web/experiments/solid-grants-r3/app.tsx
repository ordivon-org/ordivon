import {createSignal,createMemo,For,flush} from "solid-js";
import {render} from "@solidjs/web";
import {createAgent} from "@ui-sdk/solid/agent";
import {Select,SelectContent,SelectItem,SelectLabel,SelectTrigger,SelectValue} from "@ui-sdk/solid/select";
import "@ui-sdk/core/web.css";
import {grantAvailability,type GrantAvailability} from "../../src/grant-observation.ts";
import {initial,begin,suspend,settle,readObservation,type Outcome} from "./observation.ts";

type Filter="all"|GrantAvailability;
const items=[{value:"all",label:"All grants"},{value:"candidate",label:"Candidate"},{value:"revoked",label:"Revoked"},{value:"expired",label:"Expired"},{value:"exhausted",label:"Quota exhausted"}];
const bridge=createAgent({allow:step=>step.action==="setValue"&&items.some(item=>item.value===step.args[0])});
const [state,setState]=createSignal(initial);
const [filter,setFilter]=createSignal<Filter>("all");
const [logoutStatus,setLogoutStatus]=createSignal<"idle"|"requesting"|"confirmed"|"unknown">("idle");
const sessionChannelName="ordivon-web-observation-invalidation-v1";
let sessionChannel:BroadcastChannel|null=null;
function connectSessionHints(){
  if(sessionChannel!==null||typeof BroadcastChannel==="undefined")return;
  sessionChannel=new BroadcastChannel(sessionChannelName);
  // Untrusted same-origin hint: it can clear the projection, never grant authority.
  sessionChannel.onmessage=event=>{
    if(event.data==="session-changed")invalidate();
  };
}
function disconnectSessionHints(){
  sessionChannel?.close();sessionChannel=null;
}
let pageActive=true;
const visible=()=>pageActive&&document.visibilityState==="visible";
function invalidate(){
  setState(old=>suspend(old));setFilter("all");flush();
}
async function refresh(){
  if(!visible()||logoutStatus()==="requesting"){invalidate();return;}
  setLogoutStatus("idle");
  const next=begin(state());setState(next);flush();
  let outcome:Outcome;
  try {
    const response=await fetch("/api/security/agents/grants",{credentials:"same-origin",cache:"no-store"});
    if(response.status===401||response.status===403) outcome={status:"denied",observation:null};
    else if(!response.ok) outcome={status:"unavailable",observation:null};
    else outcome={status:"observed",observation:readObservation(await response.json())};
  } catch {
    outcome={status:"unavailable",observation:null};
  }
  if(!visible()||logoutStatus()==="requesting"){invalidate();return;}
  setState(old=>settle(old,next.generation,outcome));flush();
}
// Human-only session control. No UI SDK mutation or browser-held authority.
async function logout(){
  if(logoutStatus()==="requesting")return;
  setLogoutStatus("requesting");invalidate();
  let confirmed=false;
  try {
    const csrf=await fetch("/api/session/csrf",{credentials:"same-origin",cache:"no-store"});
    if(!csrf.ok)throw Error("CSRF unavailable");
    const token:unknown=(await csrf.json()).token;
    if(typeof token!=="string"||!token)throw Error("Invalid CSRF response");
    const response=await fetch("/api/session/logout",{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"x-csrf-token":token}});
    confirmed=response.ok&&(await response.json()).revoked===true;
  } catch {
    // Response loss cannot distinguish uncommitted from committed logout.
    // Do not retry or claim success.
  } finally {
    invalidate();
    setLogoutStatus(confirmed?"confirmed":"unknown");flush();
    // Ambiguous completion may also invalidate projections, without claiming
    // revocation or sending identity, tokens, grants or other owner data.
    sessionChannel?.postMessage("session-changed");
  }
}
function App(){
 const rows=createMemo(()=>{
   const current=state();
   if(current.status!=="observed")return [];
   return current.observation.grants
     .map(grant=>({grant,availability:grantAvailability(grant,current.observation.observedAt)}))
     .filter(row=>filter()==="all"||row.availability===filter());
 });
 return <main><h1>Agent grants — research prototype</h1>
 <p>Candidate is not an admission decision. Read-only owner observation.</p>
 <button type="button" disabled={logoutStatus()==="requesting"} onClick={()=>void refresh()}>Refresh owner observation</button>
 <button type="button" disabled={logoutStatus()==="requesting"} onClick={()=>void logout()}>Sign out</button>
 <p role="status" data-logout={logoutStatus()}>{logoutStatus()==="confirmed"?"Session logout confirmed.":logoutStatus()==="unknown"?"Logout not confirmed. Refresh to verify current session.":logoutStatus()==="requesting"?"Signing out…":""}</p>
 <p role="status" data-status={state().status}>{state().status} {state().observation?.observedAt}</p>
 <Select items={items} value={filter()} onValueChange={value=>{if(items.some(x=>x.value===value))setFilter(value as Filter)}}>
 <SelectLabel>Grant availability</SelectLabel><SelectTrigger data-testid="filter"><SelectValue/></SelectTrigger>
 <SelectContent>{items.map(item=><SelectItem value={item.value}>{item.label}</SelectItem>)}</SelectContent>
 </Select>
 <table><caption>Current owner grants</caption><thead><tr><th>Grant</th><th>Agent</th><th>Availability</th><th>Remaining effects</th></tr></thead>
 <tbody><For each={rows()} keyed={row=>row.grant.grantId}>{row=><tr><th scope="row">{row().grant.grantId}</th><td>{row().grant.agentId}</td><td>{row().availability}</td><td>{row().grant.remainingEffects}</td></tr>}</For></tbody></table>
 </main>;
}
render(()=> <App/>,document.getElementById("root")!);
// Test harness only. No WebMCP registration, network agent or mutation capability.
Object.assign(window,{probe:{bridge,refresh}});
window.addEventListener("pagehide",()=>{
  pageActive=false;invalidate();disconnectSessionHints();
});
window.addEventListener("pageshow",event=>{
  pageActive=true;connectSessionHints();
  // The initial pageshow must not start a duplicate GET. A restored page
  // cannot trust the browser's retained DOM or the old request generation.
  if(event.persisted||state().status==="suspended"){
    if(visible())void refresh();
  }
});
document.addEventListener("visibilitychange",()=>{
  if(!visible())invalidate();
  else if(state().status==="suspended")void refresh();
});
connectSessionHints();
void refresh();

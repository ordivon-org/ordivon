import {createSignal,For,flush} from "solid-js";
import {render} from "@solidjs/web";
import {makeRows,update,type Row} from "../data";
function App(){
 const [rows,setRows]=createSignal<Row[]>([]);
 Object.assign(window,{mountRows:(n:number)=>{setRows(makeRows(n));flush()},changeRow:(i:number)=>{setRows(old=>update(old,i));flush()}});
 return <table><caption>Owner grant projection fixture</caption><thead><tr><th>Grant</th><th>Agent</th><th>Availability</th><th>Quota</th><th>Revision</th></tr></thead><tbody><For each={rows()} keyed={r=>r.id}>{row=><tr data-id={row().id}><th scope="row">{row().id}</th><td>{row().agent}</td><td>{row().availability}</td><td data-quota>{row().quota}</td><td data-revision>{row().revision}</td></tr>}</For></tbody></table>;
}
render(()=> <App/>,document.getElementById("root")!);

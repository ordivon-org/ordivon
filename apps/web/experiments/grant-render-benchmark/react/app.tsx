import {useState,useEffect,memo} from "react";
import {createRoot} from "react-dom/client";
import {flushSync} from "react-dom";
import {makeRows,update,type Row} from "../data";
declare const BENCH_MEMO:boolean;
function GrantRow({row}:{row:Row}){
 return <tr data-id={row.id}><th scope="row">{row.id}</th><td>{row.agent}</td><td>{row.availability}</td><td data-quota>{row.quota}</td><td data-revision>{row.revision}</td></tr>;
}
const DisplayRow=BENCH_MEMO?memo(GrantRow):GrantRow;
function App(){
 const [rows,setRows]=useState<Row[]>([]);
 useEffect(()=>{Object.assign(window,{mountRows:(n:number)=>flushSync(()=>setRows(makeRows(n))),changeRow:(i:number)=>flushSync(()=>setRows(old=>update(old,i)))})},[]);
 return <table><caption>Owner grant projection fixture</caption><thead><tr><th>Grant</th><th>Agent</th><th>Availability</th><th>Quota</th><th>Revision</th></tr></thead><tbody>{rows.map(row=><DisplayRow key={row.id} row={row}/>)}</tbody></table>;
}
const root=createRoot(document.getElementById("root")!);
flushSync(()=>root.render(<App/>));

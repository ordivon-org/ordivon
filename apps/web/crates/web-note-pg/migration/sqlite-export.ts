// Offline source snapshot exporter. Caller opens and owns a read-only SQLite
// connection; this operation never mutates business state. Exact storage
// classes, original TEXT bytes and BLOB bytes are observed, not coerced.
import type { DatabaseSync } from "node:sqlite";
type Cell = { kind: "null" } | {kind:"text"|"blob"; value:number[]} | {kind:"integer";value:number};
type Snapshot = Record<string,{columns:string[];rows:Cell[][]}>;
const ident=(name:string)=>'"'+name.replaceAll('"','""')+'"';
export function exportOwnerSnapshot(db:DatabaseSync):Snapshot{
  if(db.isTransaction) throw new Error("source transaction must be idle");
  db.exec("BEGIN");
  try{
    const enc=db.prepare("PRAGMA encoding").get();
    if(enc?.encoding!=="UTF-8")throw new Error("unsupported source encoding");
    const tables=db.prepare("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT GLOB 'sqlite_*' ORDER BY name COLLATE BINARY").all();
    const out:Snapshot=Object.create(null);
    for(const {name} of tables){
      if(typeof name!=="string")throw new Error("invalid table identity");
      const info=db.prepare("SELECT name,pk,hidden FROM pragma_table_xinfo(?) ORDER BY cid").all(name);
      if(info.length===0||info.some(c=>typeof c.name!=="string"||c.hidden!==0)||info[0]?.pk!==1||info.slice(1).some(c=>c.pk!==0))throw new Error("unsupported source table shape");
      const columns=info.map(c=>String(c.name));
      const select=columns.flatMap((c,i)=>{
        const q=ident(c);
        return ["typeof("+q+") AS k"+i,"CASE WHEN typeof("+q+") IN ('text','blob') THEN hex(CAST("+q+" AS BLOB)) ELSE CAST("+q+" AS TEXT) END AS v"+i];
      }).join(",");
      const rows=db.prepare("SELECT "+select+" FROM "+ident(name)+" ORDER BY "+ident(columns[0]!)+" COLLATE BINARY").all().map(r=>columns.map((c,i):Cell=>{
        const k=r["k"+i],v=r["v"+i];
        if(k==="null")return {kind:"null"};
        if(typeof v!=="string")throw new Error("source representation mismatch: "+name+"."+c);
        if(k==="integer"){
          const n=BigInt(v);
          if(n>BigInt(Number.MAX_SAFE_INTEGER)||n<BigInt(Number.MIN_SAFE_INTEGER))throw new Error("source integer outside JS exact range: "+name+"."+c);
          return {kind:"integer",value:Number(n)};
        }
        if(k==="text"||k==="blob"){
          if(!/^(?:[0-9A-F]{2})*$/.test(v))throw new Error("invalid source byte projection");
          return {kind:k,value:[...Buffer.from(v,"hex")]};
        }
        throw new Error("unsupported SQLite storage class: "+name+"."+c+" "+String(k));
      }));
      out[name]={columns,rows};
    }
    db.exec("ROLLBACK");
    return out;
  }catch(e){
    if(db.isTransaction)db.exec("ROLLBACK");
    throw e;
  }
}

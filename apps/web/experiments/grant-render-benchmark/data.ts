export type Row={id:string;agent:string;availability:string;quota:number;revision:number};
export const makeRows=(n:number):Row[]=>Array.from({length:n},(_,i)=>({id:"grant:"+i,agent:"agent:"+i,availability:"Candidate",quota:8,revision:1}));
export const update=(rows:Row[],i:number)=>rows.map((r,j)=>i===j?{...r,quota:r.quota-1,revision:r.revision+1}:r);

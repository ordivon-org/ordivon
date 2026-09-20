import type {CSSProperties} from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import '@ordivon/identity/tokens.css';
import evidence from '../../../research/expression/experiments/a33-station-zero-affect-evidence.json';

const mono: CSSProperties = {fontFamily:'var(--ordivon-font-mono)',letterSpacing:'0.09em',textTransform:'uppercase'};
const serif: CSSProperties = {fontFamily:'var(--ordivon-font-serif)'};

function ramp(frame:number,a:number,b:number){return interpolate(frame,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});}
function pulse(frame:number,period=72){return .5+.5*Math.sin((frame/period)*Math.PI*2);}

function Contact({name,role,x,y,delay}:{name:string;role:string;x:number;y:number;delay:number}){
  const frame=useCurrentFrame();
  const a=ramp(frame,delay,delay+24);
  return <div style={{position:'absolute',left:x,top:y,opacity:a,transform:`translateY(${(1-a)*10}px)`,display:'flex',gap:11,alignItems:'center'}}>
    <span style={{width:9,height:9,borderRadius:999,background:'var(--ordivon-color-accent)',boxShadow:'0 0 18px color-mix(in srgb, var(--ordivon-color-accent) 65%, transparent)'}}/>
    <div><strong style={{display:'block',fontSize:18,fontWeight:530}}>{name}</strong><span style={{...mono,fontSize:11,color:'var(--ordivon-color-muted)'}}>{role} · confirmed</span></div>
  </div>;
}

function Room({label,x,y,w,h,delay}:{label:string;x:number;y:number;w:number;h:number;delay:number}){
  const frame=useCurrentFrame();
  const a=ramp(frame,delay,delay+28);
  return <div style={{position:'absolute',left:x,top:y,width:w,height:h,border:'1px solid color-mix(in srgb, var(--ordivon-color-paper) 22%, transparent)',opacity:a,background:'color-mix(in srgb, var(--ordivon-color-paper) 1.5%, transparent)'}}>
    <span style={{position:'absolute',left:12,top:10,...mono,fontSize:11,color:'var(--ordivon-color-muted)'}}>{label}</span>
  </div>;
}

export function GameStationZeroAffectExpression(){
  const frame=useCurrentFrame();
  const mapIn=ramp(frame,12,72);
  const reportIn=ramp(frame,100,132);
  const objectiveIn=ramp(frame,170,210);
  const edgePulse=reportIn*(.08+.11*pulse(frame,96));
  const telemetry=evidence.publicTelemetry;
  const contacts=evidence.playerVisible.confirmedActors;

  return <AbsoluteFill style={{background:'var(--ordivon-color-ink)',color:'var(--ordivon-color-paper)',fontFamily:'var(--ordivon-font-sans)',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,boxShadow:`inset 0 0 0 1px color-mix(in srgb, var(--ordivon-color-accent) ${Math.round(edgePulse*100)}%, transparent)`,pointerEvents:'none'}}/>
    <div style={{position:'absolute',left:-160,bottom:-210,width:900,height:780,borderRadius:'50%',background:'radial-gradient(circle, color-mix(in srgb, var(--ordivon-color-accent) 10%, transparent) 0%, transparent 68%)',opacity:mapIn}}/>

    <header style={{position:'absolute',left:78,right:78,top:62,display:'flex',justifyContent:'space-between',alignItems:'baseline'}}>
      <p style={{...mono,margin:0,fontSize:15,color:'var(--ordivon-color-accent-soft)'}}>A3-3 · Station Zero</p>
      <p style={{...mono,margin:0,fontSize:12,color:'var(--ordivon-color-muted)'}}>unregistered v3 target · Turn 0 · Rescue knowledge envelope</p>
    </header>

    <div style={{position:'absolute',left:78,top:150,width:600}}>
      <h1 style={{...serif,margin:0,fontSize:72,lineHeight:.91,letterSpacing:'-.055em',fontWeight:450}}>Your map ends<br/><em style={{fontWeight:420,color:'var(--ordivon-color-accent-soft)'}}>before the station does.</em></h1>
    </div>

    <div style={{position:'absolute',left:82,bottom:80,width:720,height:520,opacity:mapIn}}>
      <Room label='COMMAND CENTER' x={0} y={235} w={260} h={150} delay={20}/>
      <Room label='POWER JUNCTION' x={275} y={170} w={210} h={118} delay={42}/>
      <Room label='MEDICAL BAY' x={300} y={320} w={220} h={130} delay={58}/>
      <div style={{position:'absolute',left:246,top:260,width:42,height:1,background:'var(--ordivon-color-line-strong)'}}/>
      <div style={{position:'absolute',left:260,top:329,width:54,height:1,background:'var(--ordivon-color-line-strong)',transform:'rotate(25deg)',transformOrigin:'left'}}/>
      <Contact name={contacts[0]?.name ?? 'Engineer Imani'} role='engineer' x={34} y={315} delay={52}/>
      <Contact name={contacts[1]?.name ?? 'Medic Reyes'} role='medic' x={34} y={355} delay={62}/>
      <Contact name={contacts[2]?.name ?? 'Security Chen'} role='security' x={34} y={255} delay={72}/>
      <div style={{position:'absolute',left:0,bottom:0,...mono,fontSize:11,color:'var(--ordivon-color-muted)'}}>3 discovered rooms · 3 confirmed specialists · 0 known hazards</div>
    </div>

    <div style={{position:'absolute',left:420,right:92,top:330,height:150,opacity:reportIn,borderBlock:'1px solid color-mix(in srgb, var(--ordivon-color-paper) 9%, transparent)',display:'grid',placeItems:'center',textAlign:'center'}}>
      <div>
        <p style={{...mono,margin:0,fontSize:12,color:'var(--ordivon-color-muted)'}}>unlocalized report · received</p>
        <strong style={{display:'block',marginTop:10,fontSize:28,fontWeight:520}}>unknown-life-signs</strong>
        <p style={{margin:'8px 0 0',fontSize:15,color:'var(--ordivon-color-muted)'}}>No position or bearing exists in Rescue knowledge.</p>
      </div>
      <span style={{position:'absolute',left:'8%',right:'8%',bottom:20,height:1,background:'linear-gradient(90deg, transparent, var(--ordivon-color-paper-soft), transparent)',opacity:.24+.2*pulse(frame,96)}}/>
    </div>

    <div style={{position:'absolute',right:92,bottom:82,width:560,display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:14,opacity:ramp(frame,78,118)}}>
      {[
        ['O₂',String(telemetry.oxygen)],
        ['HEAT',String(telemetry.reactorHeat)],
        ['ALERT',String(telemetry.alertLevel)],
        ['BATTERY',`${telemetry.batteryCharge}/${telemetry.batteryInitial}`],
      ].map(([label,value])=><div key={label} style={{borderTop:'1px solid var(--ordivon-color-line-strong)',paddingTop:10}}><span style={{...mono,fontSize:10,color:'var(--ordivon-color-muted)'}}>{label}</span><strong style={{display:'block',marginTop:7,fontSize:27,fontWeight:500}}>{value}</strong></div>)}
    </div>

    <div style={{position:'absolute',left:790,bottom:82,width:430,opacity:objectiveIn,borderLeft:'1px solid var(--ordivon-color-accent)',paddingLeft:20}}>
      <p style={{...mono,margin:0,fontSize:11,color:'var(--ordivon-color-accent-soft)'}}>mandatory rescue</p>
      <p style={{...serif,margin:'9px 0 0',fontSize:29,lineHeight:1.08,fontStyle:'italic'}}>Extract two civilians.<br/>Bring at least one Specialist home.</p>
    </div>
  </AbsoluteFill>;
}

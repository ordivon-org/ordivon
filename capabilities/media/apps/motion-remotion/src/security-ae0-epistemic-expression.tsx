import type {CSSProperties, ReactNode} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import '@ordivon/identity/tokens.css';
import evidence from '../../../research/expression/experiments/a32-security-ae0-evidence.json';

const mono: CSSProperties = {fontFamily:'var(--ordivon-font-mono)',letterSpacing:'0.09em',textTransform:'uppercase'};
const sans: CSSProperties = {fontFamily:'var(--ordivon-font-sans)'};
const serif: CSSProperties = {fontFamily:'var(--ordivon-font-serif)'};

function ramp(frame:number, a:number, b:number){return interpolate(frame,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});}
function fadeWindow(frame:number, enter:[number,number], exit?:[number,number]){
  const i=ramp(frame,enter[0],enter[1]);
  if(!exit)return i;
  return i*(1-ramp(frame,exit[0],exit[1]));
}
function short(value:string, head=14, tail=7){return value.length<=head+tail+1?value:`${value.slice(0,head)}…${value.slice(-tail)}`;}
function Eyebrow({children,color='var(--ordivon-color-muted)'}:{children:ReactNode;color?:string}){
  return <p style={{...mono,margin:0,fontSize:15,color}}>{children}</p>;
}
function World({side,truth,claimOpacity}:{side:'healthy'|'compromised';truth:boolean;claimOpacity:number}){
  const color=truth?'var(--ordivon-color-signal)':'var(--ordivon-color-success)';
  return <div style={{width:690,padding:28,border:'1px solid color-mix(in srgb, var(--ordivon-color-paper) 16%, transparent)',background:'var(--ordivon-color-ink-soft)'}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline'}}>
      <Eyebrow color={color}>private world · {side}</Eyebrow>
      <strong style={{...mono,fontSize:14,color}}>truth: compromised = {String(truth)}</strong>
    </div>
    <div style={{marginTop:48,display:'grid',gridTemplateColumns:'1fr 1fr',gap:22,alignItems:'end'}}>
      <div><Eyebrow>Deceiver privately sees</Eyebrow><strong style={{display:'block',marginTop:12,fontSize:38,color}}>service = {truth?'compromised':'healthy'}</strong></div>
      <div style={{opacity:claimOpacity,borderTop:'1px solid var(--ordivon-color-signal)',paddingTop:18}}><Eyebrow color='var(--ordivon-color-signal)'>published claim</Eyebrow><strong style={{display:'block',marginTop:10,fontSize:33}}>“compromised = true”</strong></div>
    </div>
  </div>;
}

export function SecurityAe0EpistemicExpression(){
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const privateWorlds=fadeWindow(frame,[0,16],[60,82]);
  const claims=ramp(frame,22,40);
  const mask=ramp(frame,58,88);
  const defender=spring({frame:frame-78,fps,config:{damping:20,stiffness:110}});
  const inspect=ramp(frame,126,148);
  const receipt=ramp(frame,150,168)*(1-ramp(frame,184,194));
  const split=ramp(frame,184,210);
  const outcome=ramp(frame,216,246);
  const claim=evidence.preInspection.receiverVisibleClaim;
  const digest=short(evidence.preInspection.contextDigest,18,8);
  const request=short(evidence.preInspection.inspectionRequestDigest,18,8);

  return <AbsoluteFill style={{background:'var(--ordivon-color-ink)',color:'var(--ordivon-color-paper)',...sans,padding:'72px 88px 70px',overflow:'hidden'}}>
    <header style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',position:'relative',zIndex:10}}>
      <Eyebrow color='var(--ordivon-color-accent)'>A3-2 · adversarial epistemics</Eyebrow>
      <Eyebrow>Security AE0 · evidence-bound</Eyebrow>
    </header>

    <div style={{position:'relative',flex:1,marginTop:28}}>
      <div style={{position:'absolute',inset:'26px 0 auto',display:'flex',gap:32,justifyContent:'space-between',opacity:privateWorlds,transform:`translateY(${(1-privateWorlds)*20}px)`}}>
        <World side='healthy' truth={false} claimOpacity={claims}/>
        <World side='compromised' truth={true} claimOpacity={claims}/>
        <div style={{position:'absolute',left:'50%',top:-24,transform:'translateX(-50%)',padding:'7px 12px',background:'var(--ordivon-color-ink)',border:'1px solid var(--ordivon-color-line-strong)',textAlign:'center'}}><Eyebrow>audience temporarily sees private truth</Eyebrow><p style={{margin:'5px 0 0',fontSize:13,color:'var(--ordivon-color-muted)'}}>parallel experimental worlds · not probability weights</p></div>
      </div>

      <div style={{position:'absolute',left:`${50-50*mask}%`,right:`${50-50*mask}%`,top:0,height:420,background:'color-mix(in srgb, var(--ordivon-color-ink) 97%, transparent)',borderBlock:mask>.2?'1px solid var(--ordivon-color-line-strong)':'1px solid transparent',opacity:mask,zIndex:3,display:'grid',placeItems:'center'}}>
        <div style={{opacity:ramp(frame,68,88),textAlign:'center'}}>
          <Eyebrow>Defender information boundary</Eyebrow>
          <p style={{...serif,margin:'12px 0 0',fontSize:38,fontStyle:'italic'}}>Private truth is not admitted evidence.</p>
        </div>
      </div>

      <div style={{position:'absolute',left:'50%',top:82,width:840,transform:`translateX(-50%) scale(${.94+.06*defender})`,opacity:defender,zIndex:5}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}>
          <Eyebrow>Defender / admitted evidence</Eyebrow>
          <span style={{...mono,fontSize:15,color:'var(--ordivon-color-accent-soft)',border:'1px solid color-mix(in srgb, var(--ordivon-color-accent) 45%, transparent)',padding:'8px 12px'}}>truth: UNKNOWN</span>
        </div>
        <div style={{border:'1px solid var(--ordivon-color-line-strong)',background:'var(--ordivon-color-ink-soft)',padding:'30px 34px'}}>
          <div style={{display:'grid',gridTemplateColumns:'1fr auto',gap:28,alignItems:'end'}}>
            <div><Eyebrow>communicated claim</Eyebrow><h1 style={{margin:'12px 0 0',fontSize:58,lineHeight:.94,letterSpacing:'-.055em',fontWeight:520}}>“Service compromised.”</h1></div>
            <div style={{textAlign:'right'}}><Eyebrow>message</Eyebrow><code style={{display:'block',marginTop:9,fontFamily:'var(--ordivon-font-mono)',fontSize:16,color:'var(--ordivon-color-paper-soft)'}}>{claim.messageId}</code></div>
          </div>
          <div style={{display:'flex',justifyContent:'space-between',gap:24,marginTop:28,paddingTop:20,borderTop:'1px solid var(--ordivon-color-line)'}}>
            <code style={{fontFamily:'var(--ordivon-font-mono)',fontSize:15,color:'var(--ordivon-color-muted)'}}>context {digest}</code>
            <span style={{fontSize:18,color:'var(--ordivon-color-paper-soft)'}}>same admissible evidence in both hidden worlds</span>
          </div>
        </div>
      </div>

      <div style={{position:'absolute',left:'50%',top:475,transform:'translateX(-50%)',width:840,opacity:inspect,zIndex:6,textAlign:'center'}}>
        <div style={{height:52,width:1,background:'var(--ordivon-color-accent)',margin:'0 auto 12px',transformOrigin:'top',transform:`scaleY(${inspect})`}}/>
        <Eyebrow color='var(--ordivon-color-accent-soft)'>Agent-chosen information acquisition</Eyebrow>
        <strong style={{display:'block',marginTop:9,fontSize:34}}>INSPECT</strong>
        <code style={{display:'block',marginTop:9,fontFamily:'var(--ordivon-font-mono)',fontSize:14,color:'var(--ordivon-color-muted)'}}>{request}</code>
      </div>

      <div style={{position:'absolute',left:'50%',bottom:128,transform:'translateX(-50%)',width:700,padding:'16px 22px',border:'1px solid var(--ordivon-color-line-strong)',background:'var(--ordivon-color-ink-soft)',opacity:receipt,zIndex:7,textAlign:'center'}}>
        <Eyebrow>inspection execution receipt</Eyebrow>
        <p style={{margin:'8px 0 0',fontSize:24}}>effect executed <span style={{color:'var(--ordivon-color-signal)'}}>≠ world truth</span></p>
      </div>

      <div style={{position:'absolute',left:0,right:0,bottom:2,height:276,opacity:split,zIndex:8,display:'grid',gridTemplateColumns:'1fr 1fr',gap:30}}>
        <div style={{borderTop:'1px solid var(--ordivon-color-success)',padding:'20px 26px',background:'linear-gradient(180deg,color-mix(in srgb, var(--ordivon-color-success) 9%, transparent),transparent)'}}>
          <Eyebrow color='var(--ordivon-color-success)'>world-truth · healthy</Eyebrow>
          <strong style={{display:'block',marginTop:12,fontSize:34}}>compromised = false</strong>
          <div style={{opacity:outcome,marginTop:32}}><Eyebrow>consequence</Eyebrow><p style={{...serif,margin:'8px 0 0',fontSize:50,fontStyle:'italic'}}>Hold.</p><p style={{margin:'5px 0 0',color:'var(--ordivon-color-muted)'}}>No quarantine.</p></div>
        </div>
        <div style={{borderTop:'1px solid var(--ordivon-color-signal)',padding:'20px 26px',background:'linear-gradient(180deg,color-mix(in srgb, var(--ordivon-color-signal) 9%, transparent),transparent)'}}>
          <Eyebrow color='var(--ordivon-color-signal)'>world-truth · compromised</Eyebrow>
          <strong style={{display:'block',marginTop:12,fontSize:34}}>compromised = true</strong>
          <div style={{opacity:outcome,marginTop:32}}><Eyebrow>consequence</Eyebrow><p style={{...serif,margin:'8px 0 0',fontSize:50,fontStyle:'italic'}}>Quarantine.</p><p style={{margin:'5px 0 0',color:'var(--ordivon-color-muted)'}}>Only after truth arrives.</p></div>
        </div>
      </div>

      <div style={{position:'absolute',left:'50%',bottom:340,transform:'translateX(-50%)',opacity:ramp(frame,190,208),zIndex:9,textAlign:'center'}}>
        <Eyebrow color='var(--ordivon-color-accent-soft)'>authoritative reveal</Eyebrow>
        <p style={{...serif,margin:'7px 0 0',fontSize:31,fontStyle:'italic'}}>Now the worlds may diverge.</p>
      </div>
    </div>
  </AbsoluteFill>;
}

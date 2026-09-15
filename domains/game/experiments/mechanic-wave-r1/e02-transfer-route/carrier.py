#!/usr/bin/env python3
from __future__ import annotations
import copy,json
ROUTES={
 'route1': {'positions':(0,1,3,6), 'hazardAt':6, 'safeCueDistance':3, 'jumpWindowIndex':2},
 'route2': {'positions':(0,2,5,9,12), 'hazardAt':12, 'safeCueDistance':3, 'jumpWindowIndex':3},
}
ACTIONS=('wait','commit-jump')

def initial(route): return {'route':route,'index':0,'attempt':1,'status':'ONGOING','jumped':False}
def observe(state):
    r=ROUTES[state['route']]; pos=r['positions'][state['index']]; return {'position':pos,'distanceToHazard':r['hazardAt']-pos,'status':state['status']}
def step(state,action):
    if state['status']!='ONGOING': raise ValueError('terminal')
    if action not in ACTIONS: raise ValueError(action)
    s=copy.deepcopy(state); r=ROUTES[s['route']]
    if action=='commit-jump':
        s['jumped']=True; s['status']='WIN' if s['index']==r['jumpWindowIndex'] else 'LOSS'; return s
    s['index']+=1
    if s['index']>=len(r['positions']): s['status']='LOSS'; s['index']=len(r['positions'])-1
    return s

def retry(state): return {'route':state['route'],'index':0,'attempt':state['attempt']+1,'status':'ONGOING','jumped':False}
def world_authority(route): return {'route':route,'routeDefinition':ROUTES[route],'actions':ACTIONS,'knowledgeFlags':[],'inventory':[]}

def run(route,policy):
    s=initial(route); trace=[]
    for _ in range(6):
        if s['status']!='ONGOING': break
        o=observe(s); a=policy(o,s); trace.append({'obs':o,'action':a}); s=step(s,a)
    return {'status':s['status'],'trace':trace,'final':s}

def policy_uninformed(obs,state): return 'commit-jump' if state['index']==0 else 'wait'
def policy_timing_insensitive(obs,state): return 'commit-jump' if state['index']==1 else 'wait'
def policy_transfer(obs,state): return 'commit-jump' if obs['distanceToHazard']==3 else 'wait'

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser(); ap.add_argument('route',choices=ROUTES); ap.add_argument('policy',choices=['uninformed','timing-insensitive','transfer']); a=ap.parse_args(); p={'uninformed':policy_uninformed,'timing-insensitive':policy_timing_insensitive,'transfer':policy_transfer}[a.policy]; print(json.dumps(run(a.route,p),sort_keys=True,indent=2))

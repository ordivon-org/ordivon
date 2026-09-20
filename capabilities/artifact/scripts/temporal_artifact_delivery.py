#!/usr/bin/env python3
"""Temporal durable execution for Artifact Build & Delivery E2E."""
from __future__ import annotations

import concurrent.futures
from datetime import timedelta
from pathlib import Path
from typing import Any

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from artifact_delivery_temporal_support import ReceiptFencedArtifactExecutor
PREPARE_ACTIVITY='ordivon.artifact.prepare'; BUILD_ACTIVITY='ordivon.artifact.build'; VERIFY_ACTIVITY='ordivon.artifact.verify'; TRUST_ACTIVITY='ordivon.artifact.verify-trust'; PACKAGE_ACTIVITY='ordivon.artifact.package'; ARTIFACT_DELIVERY_WORKFLOW='ordivon.artifact.delivery'; TRUST_MATERIAL_SIGNAL='ordivon.artifact.submit-trust-material'; STATUS_QUERY='ordivon.artifact.status'
RECEIPT_FENCED_RETRY=RetryPolicy(initial_interval=timedelta(seconds=1),backoff_coefficient=2.0,maximum_interval=timedelta(seconds=15),maximum_attempts=3)
class ArtifactDeliveryActivities:
    def __init__(self,*,state_root:Path)->None: self.executor=ReceiptFencedArtifactExecutor(state_root)
    @activity.defn(name=PREPARE_ACTIVITY)
    def prepare(self,value:dict[str,Any])->dict[str,Any]: return self.executor.prepare(value)
    @activity.defn(name=BUILD_ACTIVITY)
    def build(self,value:dict[str,Any])->dict[str,Any]: return self.executor.build(value)
    @activity.defn(name=VERIFY_ACTIVITY)
    def verify(self,value:dict[str,Any])->dict[str,Any]: return self.executor.verify(value)
    @activity.defn(name=TRUST_ACTIVITY)
    def verify_trust(self,value:dict[str,Any])->dict[str,Any]: return self.executor.verify_trust(value)
    @activity.defn(name=PACKAGE_ACTIVITY)
    def package(self,value:dict[str,Any])->dict[str,Any]: return self.executor.package(value)
@workflow.defn(name=ARTIFACT_DELIVERY_WORKFLOW)
class ArtifactDeliveryWorkflow:
    def __init__(self)->None: self._phase='CREATED'; self._trust_material:dict[str,Any]|None=None; self._public_state:dict[str,Any]={}
    @workflow.signal(name=TRUST_MATERIAL_SIGNAL)
    async def submit_trust_material(self,value:dict[str,Any])->None: self._trust_material=value
    @workflow.query(name=STATUS_QUERY)
    def status(self)->dict[str,Any]: return {'phase':self._phase,'trustMaterialReceived':self._trust_material is not None,**self._public_state}
    async def _activity(self,name:str,value:dict[str,Any],minutes:int=5)->dict[str,Any]:
        return await workflow.execute_activity(name,value,result_type=dict,start_to_close_timeout=timedelta(minutes=minutes),retry_policy=RECEIPT_FENCED_RETRY)
    @workflow.run
    async def run(self,value:dict[str,Any])->dict[str,Any]:
        request=value.get('request')
        if not isinstance(request,dict) or not isinstance(request.get('path'),str) or not isinstance(request.get('sha256'),str): raise ValueError('workflow input requires request.path and request.sha256')
        local=bool(value.get('allowLocalUnsignedDevelopment',False)); initial=value.get('initialTrustMaterial')
        if initial is not None and not isinstance(initial,dict): raise ValueError('initialTrustMaterial must be an object')
        wid=workflow.info().workflow_id
        self._phase='PREPARE'; prepared=await self._activity(PREPARE_ACTIVITY,{'operationId':f'{wid}/prepare','request':request}); profile=prepared['metadata']['profile']; self._public_state['profile']=profile
        self._phase='BUILD'; built=await self._activity(BUILD_ACTIVITY,{'operationId':f'{wid}/build','request':request}); artifact=built['roles']['artifact']; self._public_state['artifact']=artifact
        self._phase='VERIFY'; verified=await self._activity(VERIFY_ACTIVITY,{'operationId':f'{wid}/verify','profile':profile,'artifact':artifact}); verify_report=verified['roles']['verifyReport']; gate_vsas={role.split(':',1)[1]:fact for role,fact in verified['roles'].items() if role.startswith('gateVsa:')}; self._public_state['verifyReport']=verify_report; self._public_state['gateVsas']=gate_vsas
        trust_result=None; trust_material=None
        if not local:
            trust_material=initial if isinstance(initial,dict) else None
            if trust_material is None:
                self._phase='WAIT_TRUST_MATERIAL'; await workflow.wait_condition(lambda:self._trust_material is not None); trust_material=self._trust_material
            self._phase='VERIFY_TRUST'; trust_result=await self._activity(TRUST_ACTIVITY,{'operationId':f'{wid}/trust','profile':profile,'artifact':artifact,'gateVsas':gate_vsas,'trustMaterial':trust_material})
        self._phase='PACKAGE'; package_input={'operationId':f'{wid}/package','profile':profile,'artifact':artifact,'verifyReport':verify_report,'allowLocalUnsignedDevelopment':local}
        if trust_material is not None: package_input['trustMaterial']=trust_material
        packaged=await self._activity(PACKAGE_ACTIVITY,package_input); self._phase='COMPLETE'
        return {'schemaVersion':1,'kind':'artifact-delivery-temporal-workflow-result','workflowId':wid,'status':'PASS','allowLocalUnsignedDevelopment':local,'prepare':prepared,'build':built,'verify':verified,'trust':trust_result,'package':packaged,'releaseReady':bool(packaged.get('metadata',{}).get('releaseReady')),'trustStanding':packaged.get('metadata',{}).get('trustStanding')}
async def run_worker(*,temporal_address:str,namespace:str,task_queue:str,state_root:Path)->None:
    client=await Client.connect(temporal_address,namespace=namespace); activities=ArtifactDeliveryActivities(state_root=state_root)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        worker=Worker(client,task_queue=task_queue,workflows=[ArtifactDeliveryWorkflow],activities=[activities.prepare,activities.build,activities.verify,activities.verify_trust,activities.package],activity_executor=executor); await worker.run()

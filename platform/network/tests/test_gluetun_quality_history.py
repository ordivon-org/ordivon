"""Consumer-probe backed VPN history and no-false-standby counterexamples."""
from datetime import datetime,timedelta,timezone
import importlib.util
from pathlib import Path
import sys

DIR=Path(__file__).resolve().parents[1]/"providers/gluetun"
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location("vpn_history",DIR/"quality_history.py")
history=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=history
spec.loader.exec_module(history)

def t(h=0):return datetime(2026,11,13,15,0,tzinfo=timezone.utc)+timedelta(hours=h)

def seg(country="Japan",end_h=0):
    return history.Segment(t(end_h)-timedelta(hours=2),t(end_h),country,"192.0.2.1")

def evidence(segment,now=t()):
    return history.qualify(segment, {j:[1.0]*32 for j in history.JOBS},
             {j:[.12]*32 for j in history.JOBS},now,{"Japan","Mexico"})

def test_endpoint_catalog_and_stable_session_requires_dwell():
    raw='{"surfshark":{"servers":[{"vpn":"wireguard","ips":["192.0.2.1"],"country":"Japan"},{"vpn":"wireguard","ips":["192.0.2.2"],"country":"Mexico"}]}}'
    m=history.endpoint_countries(raw)
    assert history.endpoint_hostnames(raw).get("192.0.2.1")==""  # fixture does not claim a hostname
    assert m["192.0.2.1"]=="Japan"
    rawlog=("\n".join([
     "2026-11-13T12:00:00Z INFO [wireguard] Connecting to 192.0.2.1:51820",
     "2026-11-13T12:01:00Z INFO [wireguard] Connecting to 192.0.2.2:51820",
     "2026-11-13T14:00:00Z INFO [wireguard] Connecting to 192.0.2.1:51820",
    ]))
    result=history.segments(rawlog,m,t())
    assert len(result)==2 and result[0].country=="Mexico"
    assert result[0].minutes==119.0

def test_history_does_not_promote_hot_backup():
    e=evidence(seg(),t())
    assert e["standing"]=="RECENT_HISTORICAL_CONSUMER_SUCCESS"
    assert e["qualifiedNowStandby"] is False
    assert e["consumers"][0]["medianMs"]==120
    assert evidence(seg(end_h=-30),t())["standing"]=="STALE_HISTORICAL_SUCCESS"

def test_country_forbidden_and_missing_evidence():
    assert evidence(seg("Hong Kong"),t())["standing"]=="REJECTED_NOT_ALLOWED"
    res=history.qualify(seg(),{j:[1.0]*5 for j in history.JOBS},
        {j:[.1]*5 for j in history.JOBS},t(),{"Japan"})
    assert res["standing"]=="UNKNOWN_INSUFFICIENT_CONSUMER_EVIDENCE"
    x={j:[1.0]*33+[0.0] for j in history.JOBS}
    y=history.qualify(seg(),x,{j:[.1]*34 for j in history.JOBS},t(),{"Japan"})
    assert y["standing"]=="RECENT_HISTORICAL_CONSUMER_SUCCESS"
    x={j:[1.0]*32+[0.0,0.0] for j in history.JOBS}
    y=history.qualify(seg(),x,{j:[.1]*32 for j in history.JOBS},t(),{"Japan"})
    assert y["standing"]=="OBSERVED_CONSUMER_DEGRADED"

def test_only_true_failures_and_reachable_underlay_allow_trial():
    row=evidence(seg(),t())
    opts={"now":t(),"evidence":[row],"last_switch":None}
    assert history.decision(active_healthy=True,underlay_reachable=True,**opts)["decision"]=="HOLD_WORKING_ACTIVE"
    assert history.decision(active_healthy=None,underlay_reachable=True,**opts)["decision"]=="HOLD_ACTIVE_HEALTH_UNKNOWN"
    for reach in (None,False):
        assert history.decision(active_healthy=False,underlay_reachable=reach,**opts)["decision"]=="HOLD_SHARED_UNDERLAY_OR_UNKNOWN"
    assert history.decision(active_healthy=False,underlay_reachable=True,
           now=t(),evidence=[row],last_switch=t()-timedelta(minutes=1))["decision"]=="HOLD_COOLDOWN"
    x=history.decision(active_healthy=False,underlay_reachable=True,**opts)
    assert x["decision"].startswith("TRIAL_ONLY_")
    assert x["trialCountry"]=="Japan" and x["certifiedHotStandbyCount"]==0
    assert history.decision(active_healthy=False,underlay_reachable=True,
           now=t(),evidence=[evidence(seg(end_h=-30),t())])["decision"]=="HOLD_NO_RECENT_EVIDENCE"

def test_do_not_retrial_the_same_bad_country():
    row=evidence(seg(),t())
    x=history.decision(active_healthy=False,underlay_reachable=True,
        now=t(),evidence=[row],current_country="Japan")
    assert x["decision"]=="HOLD_NO_RECENT_EVIDENCE"



def test_recent_failure_requires_three_observed_consecutive_zeros(monkeypatch):
    now=t()
    def fill(values):
        return [{"metric":{"job":job},
                 "values":[[now.timestamp()-180+i*60,str(v)] for i,v in enumerate(values)]}
                for job in history.JOBS]
    monkeypatch.setattr(history,"http_query",lambda metric,start,end:fill([0,0,0]))
    assert history.recent_failure_witness(now) is True
    monkeypatch.setattr(history,"http_query",lambda metric,start,end:fill([0,1,0]))
    assert history.recent_failure_witness(now) is False
    monkeypatch.setattr(history,"http_query",lambda metric,start,end:fill([0,0]))
    assert history.recent_failure_witness(now) is None


def test_sparse_query_never_becomes_success():
    start=t()-timedelta(hours=1)
    r=[{"metric":{"job":history.JOBS[0]},"values":[[start.timestamp()+10,"1"],[start.timestamp()+20,"NaN"]]}]
    assert history.parse_matrix(r,"probe_success",start,t())[history.JOBS[0]]==[1.0]

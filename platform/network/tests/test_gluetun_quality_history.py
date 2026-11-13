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
    monkeypatch.setattr(history,"http_raw_samples",lambda metric,now:fill([0,0,0]))
    assert history.recent_failure_witness(now) is True
    monkeypatch.setattr(history,"http_raw_samples",lambda metric,now:fill([0,1,0]))
    assert history.recent_failure_witness(now) is False
    monkeypatch.setattr(history,"http_raw_samples",lambda metric,now:fill([0,0]))
    assert history.recent_failure_witness(now) is None


def test_sparse_query_never_becomes_success():
    start=t()-timedelta(hours=1)
    r=[{"metric":{"job":history.JOBS[0]},"values":[[start.timestamp()+10,"1"],[start.timestamp()+20,"NaN"]]}]
    assert history.parse_matrix(r,"probe_success",start,t())[history.JOBS[0]]==[1.0]


def test_recovery_candidates_are_distinct_countries_sorted_by_real_consumer_quality():
    base={
        "standing":"RECENT_HISTORICAL_CONSUMER_SUCCESS",
        "worstConsumerSuccessRatio":.99,"lastObservedHoursAgo":2,
    }
    rows=[
        dict(base,catalogCountry="Japan",catalogHostname="jp-tok.one",medianOfConsumerP90Ms=800),
        dict(base,catalogCountry="Japan",catalogHostname="jp-tok.two",medianOfConsumerP90Ms=820),
        dict(base,catalogCountry="Mexico",catalogHostname="mx-qro.one",medianOfConsumerP90Ms=1200),
        dict(base,catalogCountry="Croatia",catalogHostname="hr-zag.one",medianOfConsumerP90Ms=1800),
    ]
    x=history.decision(active_healthy=False,underlay_reachable=True,now=t(),
                       current_country="Croatia",evidence=rows)
    assert x["trialCountries"]==["Japan","Mexico"]
    assert x["trialCountry"]=="Japan"


def test_last_three_samples_must_be_fresh_and_distinct(monkeypatch):
    now=t()
    def rows(stamps,values=(0,0,0),duplicate=False):
        r=[{"metric":{"job":job,"instance":"unique-"+job},
            "values":[[stamp,str(value)] for stamp,value in zip(stamps,values)]}
            for job in history.JOBS]
        return r + ([r[0]] if duplicate else [])
    fresh=[now.timestamp()-120,now.timestamp()-60,now.timestamp()]
    monkeypatch.setattr(history,"http_raw_samples",lambda *a:rows(fresh))
    assert history.recent_failure_witness(now) is True
    monkeypatch.setattr(history,"http_raw_samples",lambda *a:rows(fresh,values=(0,1,0)))
    assert history.recent_failure_witness(now) is False
    monkeypatch.setattr(history,"http_raw_samples",lambda *a:rows([now.timestamp()-370,now.timestamp()-310,now.timestamp()-250]))
    assert history.recent_failure_witness(now) is None
    monkeypatch.setattr(history,"http_raw_samples",lambda *a:rows([now.timestamp()-120]*3))
    assert history.recent_failure_witness(now) is None
    monkeypatch.setattr(history,"http_raw_samples",lambda *a:rows(fresh,duplicate=True))
    assert history.recent_failure_witness(now) is None


def test_bulk_history_uses_two_provider_queries_not_two_per_session(monkeypatch):
    # The historical decision must stay bounded even when 8 real sessions
    # are retained by the mature native journal / monitoring stack.
    now=t()
    segs=[history.Segment(now-timedelta(hours=n+1),
                          now-timedelta(hours=n), "Mexico", "192.0.2.2")
          for n in range(1,8)]
    queries=[]
    def query(metric,start,end):
        queries.append((metric,start,end))
        return []
    class Result:
        def __init__(self, stdout):
            self.stdout=stdout
    def run(args,**kwargs):
        if args[:2] == ["/usr/bin/podman","exec"]:
            return Result('{"surfshark":{"servers":[]}}')
        if args[0]=="/usr/bin/journalctl":
            return Result("")
        raise AssertionError("unexpected subprocess")
    monkeypatch.setattr(history.subprocess,"run",run)
    monkeypatch.setattr(history,"segments",lambda *args,**kwargs:segs)
    monkeypatch.setattr(history,"http_query",query)
    monkeypatch.setattr(history,"recent_failure_witness",lambda now:False)
    import observe_active
    monkeypatch.setattr(observe_active,"observe",lambda:{"standing":"UNKNOWN"})
    monkeypatch.setattr(history,"current_catalog_country",lambda catalog:None)
    x=history.observe(hours=48)
    assert x["recommended"]["decision"]=="HOLD_ACTIVE_HEALTH_UNKNOWN"
    assert [q[0] for q in queries]==["probe_success","probe_duration_seconds"]


def test_correlated_outage_can_try_allowed_history_even_without_kernel_endpoint(monkeypatch):
    import observe_active
    now=datetime.now(timezone.utc)
    seg=history.Segment(now-timedelta(hours=2),now-timedelta(hours=1),
                        "Mexico","192.0.2.99","mx-qro.example")
    class Result:
        def __init__(self,stdout):self.stdout=stdout
        returncode=0
    calls=[]
    def stub_run(args,**kw):
        calls.append(args[0])
        if args[:2]==["/usr/bin/podman","exec"]:
            return Result('{"surfshark":{"servers":[]}}')
        if args[0]=="/usr/bin/journalctl":return Result("")
        if args[0]=="/usr/bin/curl":return Result("200")
        raise AssertionError("unexpected subprocess")
    monkeypatch.setattr(history.subprocess,"run",stub_run)
    monkeypatch.setattr(history,"segments",lambda *args,**kw:[seg])
    monkeypatch.setattr(history,"http_query",lambda *args:[])
    monkeypatch.setattr(history,"qualify",lambda *args:{
        "catalogCountry":"Mexico","standing":"RECENT_HISTORICAL_CONSUMER_SUCCESS",
        "medianOfConsumerP90Ms":1200,"worstConsumerSuccessRatio":.99,
        "lastObservedHoursAgo":2})
    monkeypatch.setattr(history,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(history,"current_catalog_country",lambda catalog:None)
    monkeypatch.setattr(observe_active,"observe",
        lambda: (_ for _ in ()).throw(AssertionError("Do not resample 3 HTTPS failures")))
    x=history.observe(hours=24)
    assert x["active"]["catalogCountry"] is None
    assert x["recommended"]["trialCountry"]=="Mexico"
    assert x["active"]["threeLaneConsecutiveFailure"] is True
    assert "/usr/bin/curl" in calls


def test_raw_failure_gate_queries_one_prometheus_range_vector_not_replayed_steps(monkeypatch):
    from urllib.parse import urlsplit,parse_qs
    import io,json
    now=t()
    calls=[]
    class Wire:
        def __enter__(self):return io.BytesIO(json.dumps({"status":"success","data":{
          "resultType":"matrix","result":[{"metric":{"job":history.JOBS[0]},
          "values":[[now.timestamp()-90,"0"],[now.timestamp()-30,"0"]]}]}}).encode())
        def __exit__(self,*args):return False
    def fake_urlopen(url,timeout):
        calls.append(url)
        return Wire()
    monkeypatch.setattr(history,"urlopen",fake_urlopen)
    rows=history.http_raw_samples("probe_success",now)
    assert rows[0]["values"][-1][1]=="0"
    assert len(calls)==1
    parsed=urlsplit(calls[0])
    assert parsed.path.endswith("/api/v1/query")
    q=parse_qs(parsed.query)["query"][0]
    assert "probe_success{" in q and q.endswith("[7m]")
    assert "/query_range" not in calls[0]


def test_suspended_prometheus_scrape_with_previous_zero_is_unknown(monkeypatch):
    # PromQL query_range would evaluate the previous '0' at new step times.
    # The native range-vector returns only its ORIGINAL timestamp.
    now=t()
    frozen=now.timestamp()-240
    rows=[{"metric":{"job":job},
           "values":[[frozen-120,"0"],[frozen-60,"0"],[frozen,"0"]]}
          for job in history.JOBS]
    monkeypatch.setattr(history,"http_raw_samples",lambda *args:rows)
    assert history.recent_failure_witness(now) is None

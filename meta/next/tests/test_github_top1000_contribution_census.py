import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LESSONS = ROOT / 'catalogs/knowledge/lessons'
CENSUS = LESSONS / 'github-top1000-repository-census-r1.json'
CSV = LESSONS / 'github-top1000-repository-census-r1.csv'
FRONTIER = LESSONS / 'github-top1000-contribution-frontier-r1.json'
SUMMARY = LESSONS / 'github-top1000-contribution-census-r1.md'


def test_top1000_snapshot_is_complete_and_unique():
    payload = json.loads(CENSUS.read_text())
    rows = payload['rows']
    assert payload['snapshotDate'] == '2026-10-17'
    assert len(rows) == 1000
    assert [r['rank'] for r in rows] == list(range(1, 1001))
    assert len({r['repo'] for r in rows}) == 1000
    assert rows[0]['repo'] == 'codecrafters-io/build-your-own-x'
    assert rows[-1]['repo'] == 'microsoft/WSL'


def test_csv_projection_covers_all_repositories():
    with CSV.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1000
    assert len({r['repo'] for r in rows}) == 1000


def test_campaign_gate_is_conservative_and_accounted_for():
    rows = json.loads(CENSUS.read_text())['rows']
    counts = {}
    for row in rows:
        counts[row['campaign_gate']] = counts.get(row['campaign_gate'], 0) + 1
    assert counts == {
        'ELIGIBLE_SOFTWARE': 750,
        'EXCLUDE_MECHANICAL': 61,
        'EXCLUDE_NONSOFTWARE': 122,
        'REVIEW': 67,
    }
    for row in rows:
        if row['campaign_gate'] == 'ELIGIBLE_SOFTWARE':
            assert not row['archived']
            assert not row['disabled']
            assert row['has_issues']
            assert row['active_365d']
            assert row['open_issues_count'] > 0


def test_compact_frontier_preserves_enrichment_coverage_and_no_security_titles():
    payload = json.loads(FRONTIER.read_text())
    repos = payload['repositories']
    assert payload['coverage'] == {
        'community_profiles': 817,
        'issue_sample_repositories': 750,
        'sampled_open_issues': 8897,
    }
    assert len(repos) == 817
    assert len({r['repo'] for r in repos}) == 817
    assert sum(r['public_candidate_count'] for r in repos) == 3221
    assert sum(r['security_private_count'] for r in repos) == 1590
    assert all(len(r['top_public_candidates']) <= 2 for r in repos)


def test_summary_states_sampling_and_non_authority_boundaries():
    text = SUMMARY.read_text()
    assert '1000 unique repositories' in text
    assert '750/750' in text
    assert '8897' in text
    assert '3221' in text
    assert 'Security-signal issues removed from public queue: 1590' in text
    assert 'not a contribution-value verdict' in text
    assert 'not exhaustive' in text

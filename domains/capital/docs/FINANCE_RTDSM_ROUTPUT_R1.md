# Philadelphia Fed ROUTPUT: source-bound monthly vintages

## Real source evidence, 2026-11-24

Prior ALFRED public endpoint probes timed out. The Philadelphia Fed offers
a separate official Real-Time Data Set for Macroeconomists (RTDSM), with
monthly historical vintages of quarterly real GDP/GNP. These are not
latest-only reconstructed values. Official source page:
https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/routput

Source workbook (link on that page):
https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/real-time-data/data-files/xlsx/routputMvQd.xlsx?hash=B3AD0AED9E268AA077E8D9B8AAF2AC83&sc_lang=en

Provider documentation, general NIPA notes pp. 5 and 15:
https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/real-time-data/data-files/documentation/gen_doc_NIPA.pdf

Actual native Linux source retrieval: HTTPS 200, 700,496 bytes,
SHA-256 `ae854a7518bf3a0504e4c477344bd7ed98c4321326ed2b1952b69ffaa1a7adce`.
Two independently implemented readers (stdlib ZIP/XML probe and
python-calamine 0.9.1) read the corresponding cells; OpenPyXL 3.1.5
failed on this workbook's core datetime metadata in the current Python
3.15.1 environment. Reuse Calamine, not an invented production XLSX reader.
The decoded data matrix is 319 observation quarters by 733 vintage months.
The workbook is not redistributed in Git. The digest, URL and exact
coordinates below are the reproduction record; a future source download
may have changed bytes. Do not treat the HTTP observation now as an
independently signed historic publication receipt or licence grant.

Observed real GDP (billions of real USD, seasonal adjustment as declared by
provider):

| Vintage column | 2024:Q3 | 2024:Q4 |
|---|---:|---:|
| ROUTPUT25M1 | 23400.3 | #N/A |
| ROUTPUT25M2 | 23400.3 | 23530.9 |
| ROUTPUT25M3 | 23400.3 | 23536.3 |
| ROUTPUT25M4 | 23400.3 | 23542.3 |
| ROUTPUT25M10 | 23478.6 | 23586.5 |
| ROUTPUT26M11 | 23501.8 | 23641.8 |

The source's monthly labels identify a vintage month, not an exact
availability minute. Use an explicit conservative rule: the following
month's first day at 00:00 America/New_York. For a 2025-02-01 decision,
the eligible January vintage's 2024Q4 is UNKNOWN. For a 2025-03-01
decision, February vintage is eligible and 2024Q4 = 23530.9; same-vintage
Q3 = 23400.3, nonannualized quarter-on-quarter growth approximately
0.5581125%. A 2025-04-01 decision reads March's 23536.3, not the
latest 23641.8. This is conservative source-month resolution; it is not
an exact BEA first-release timestamp.

## Owner, composition and consumer

Markets owns bounded source bytes, SHA binding, matrix shape, vintage
selection, missing-cell semantics and same-vintage growth.
The existing Research `scripts/research/finance_liquidity_asof.py`
optionally consumes the result under `realOutput`, with
`--routput`, `--routput-sha256`, and optional `--routput-quarter YYYY:Qn`.
No separate service, time-series database, or new score. Other inputs
retain their existing qualification status; no implied common release
clock or capital permission. Without the optional flags, existing JSON
behavior is unchanged.

Use the existing command with already captured H41, DTS and SOFR files;
for the optional module, run from domains/capital with project PYTHONPATH:

```sh
PYTHONPATH=src uv run --locked --group research python scripts/research/finance_liquidity_asof.py \
  --h41 h41-20261119.html --dts dts.json --sofr sofr.csv \
  --routput routput.xlsx \
  --routput-sha256 ae854a7518bf3a0504e4c477344bd7ed98c4321326ed2b1952b69ffaa1a7adce \
  --routput-quarter 2024:Q4 --at 2025-03-01T00:00:00-05:00
```

Actual source verification (supply the exact downloaded workbook outside
the repo):

```sh
ORDIVON_FINANCE_ROUTPUT_XLSX=/path/to/routput.xlsx \
  uv run --locked --group test python -m pytest -q -m provider_qualification \
  tests/test_rtdsm_real_output.py tests/test_finance_liquidity_asof.py -k actual
```

## Invariants and limitations

- Current or future month is never admitted. Calendar boundaries are in
  New York; UTC and daylight-saving boundaries are tested.
- An explicitly requested missing cell in the selected vintage returns
  UNKNOWN, not zero or a value borrowed from an earlier or later vintage.
- Growth numerator and denominator use the same vintage because revisions
  can change base years or economic definitions; no across-vintage
  level-ratio is asserted. Parsed numeric cells are represented through
  Calamine's numerical values and Decimal, not a proof of arbitrary XLSX
  raw-decimal exactness.
- The selected vintage may be older than the desired decision; its month,
  eligibility bound and latest archive month are explicit.
- Future-column mutation tests and new Z3 month-index checks establish
  scoped no-forward-selection behavior. Python/date-parser refinement
  remains tested, not universally formally proved.
- GDP is macroeconomic context, not a dollar liquidity stock or proof of
  strategy edge. No broker, Paper Ledger, or real capital effect.

Actual source probe job: job-01a20bdd-a07b-726b-8c68-33b75e5d7c83.
Calamine independent readback: job-01a20bdf-0d86-759e-89d3-bf9cd1c52bc8.
Actual adapter verification: job-01a20be2-459b-722d-8185-75de85507ad9.

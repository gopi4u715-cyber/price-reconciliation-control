# Price Reconciliation Control: Yahoo Finance vs FRED

A reconciliation control that compares daily closing prices from two independent public sources, classifies every break, and surfaces the ones that need investigation.

**Live dashboard:** https://public.tableau.com/app/profile/gopinath.paila/viz/TableauPackagedWorkbook_17952685470370/Dashboard1

## Why I built it

At work I reconcile pricing and transaction data across systems. This project reproduces that workflow end to end on public data: match, tolerance, classify, triage, report.

## Data

| Item | Detail |
|---|---|
| Source A | Yahoo Finance (`yfinance`), unadjusted close |
| Source B | FRED (St. Louis Fed), public CSV, no API key |
| Instruments | S&P 500, Nasdaq, Dow Jones, VIX, US 10Y yield, EURUSD, GBPUSD, USDJPY |
| Period | Nov 2024 to Oct 2026 |
| Comparisons | 4,071 |

## Method

1. **Match** both sources on date and instrument with an outer join, so missing rows on either side are caught.
2. **Tolerances by asset class** (an initial flat 0.05% threshold flagged ~40% of rows, mostly FX, so I tuned it):
   - Indices and VIX: 0.05% match, 1% minor
   - FX: 0.5% match, 1% minor
   - US 10Y: compared in basis points (2 bps match, 5 bps minor)
3. **Classify** each row: Match, Minor break, Date shift (likely), Missing in A, Missing in B, Major break.
4. **Date shift check:** if a Yahoo price matches FRED's previous or next published value within tolerance, the row is labeled a likely date shift instead of a major break.

## Results

| Status | Rows | Share |
|---|---|---|
| Match | 3,674 | 90.3% |
| Minor break | 270 | 6.6% |
| Missing in B (FRED) | 61 | 1.5% |
| Date shift (likely) | 40 | 1.0% |
| Missing in A (Yahoo) | 21 | 0.5% |
| Major break | 5 | 0.1% |

Only 5 breaks needed real investigation:

| Date | Instrument | Yahoo | FRED | Diff % |
|---|---|---|---|---|
| 2026-02-06 | VIX | 20.3700 | 17.7600 | 14.70 |
| 2025-04-10 | EURUSD | 1.0952 | 1.1192 | 2.14 |
| 2025-04-10 | USDJPY | 147.3990 | 144.3400 | 2.12 |
| 2025-03-05 | EURUSD | 1.0627 | 1.0768 | 1.31 |
| 2025-04-03 | USDJPY | 147.8720 | 146.0400 | 1.25 |

## Findings

- Equity indices matched 100% across both sources.
- Most FX breaks are methodological: FRED publishes a noon New York rate, Yahoo a later close, so small daily gaps are expected.
- Flagged rows cluster in April 2025, a period of high market volatility.
- The VIX break on 2026-02-06 is the one that stands out, since both sources should carry the same official close.

## Limitations

- "Date shift" is a heuristic label, not a confirmed cause.
- The 82 missing rows are likely holiday calendar differences, but I have not verified each one.
- Public sources only; no vendor-grade reference data.

## Run it

```
pip install pandas yfinance requests
python recon.py       # downloads both sources, writes recon_results.csv
python classify.py    # applies tolerances, writes recon_classified.csv
```

Open `recon_classified.csv` in Tableau, or view the live dashboard linked above.

## Files

- `recon.py` pulls and matches the data
- `classify.py` applies tolerances and the date shift check
- `recon_classified.csv` final output

## Tools

Python (pandas, yfinance, requests), Tableau Public

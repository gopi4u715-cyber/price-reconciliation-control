import io, requests, pandas as pd, yfinance as yf

# (name, Yahoo ticker, FRED series)
pairs = [
    ("S&P 500",   "^GSPC",    "SP500"),
    ("Nasdaq",    "^IXIC",    "NASDAQCOM"),
    ("Dow Jones", "^DJI",     "DJIA"),
    ("VIX",       "^VIX",     "VIXCLS"),
    ("US 10Y",    "^TNX",     "DGS10"),
    ("EURUSD",    "EURUSD=X", "DEXUSEU"),
    ("GBPUSD",    "GBPUSD=X", "DEXUSUK"),
    ("USDJPY",    "JPY=X",    "DEXJPUS"),
]

rows_a, rows_b = [], []
for name, ytk, fred in pairs:
    # Source A: Yahoo
    y = yf.download(ytk, start="2024-11-01", end="2026-11-01",
                    auto_adjust=False, progress=False, threads=False)
    if y.empty:
        print("Yahoo empty for", ytk); continue
    close = y["Close"].squeeze()
    da = pd.DataFrame({"date": pd.to_datetime(close.index).tz_localize(None).normalize(),
                       "price_a": close.values})
    da["instrument"] = name
    rows_a.append(da)

    # Source B: FRED (no key needed)
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                     params={"id": fred}, timeout=30)
    if r.status_code != 200:
        print("FRED failed for", fred, r.status_code); continue
    f = pd.read_csv(io.StringIO(r.text))
    f.columns = ["date", "price_b"]
    f["date"] = pd.to_datetime(f["date"])
    f["price_b"] = pd.to_numeric(f["price_b"], errors="coerce")
    f = f.dropna()
    f = f[(f.date >= "2024-11-01") & (f.date < "2026-11-01")]
    f["instrument"] = name
    rows_b.append(f)

if not rows_a or not rows_b:
    raise SystemExit("Got no data from one source. Paste the messages above here.")

a = pd.concat(rows_a); b = pd.concat(rows_b)

m = a.merge(b, on=["date", "instrument"], how="outer", indicator=True)
m["diff_pct"] = (m.price_a - m.price_b).abs() / m.price_b * 100

def classify(r):
    if r["_merge"] == "left_only":  return "Missing in B"
    if r["_merge"] == "right_only": return "Missing in A"
    if r.diff_pct <= 0.05:          return "Match"
    if r.diff_pct <= 1:             return "Minor break"
    return "Major break"

m["status"] = m.apply(classify, axis=1)
m.to_csv("recon_results.csv", index=False)
print(m.status.value_counts())
print(m.groupby(["instrument", "status"]).size().unstack(fill_value=0))

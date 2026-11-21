import pandas as pd, numpy as np

m = pd.read_csv("recon_results.csv", parse_dates=["date"])

b = m.dropna(subset=["price_b"])[["instrument","date","price_b"]].sort_values(["instrument","date"])
b["prev_b"] = b.groupby("instrument")["price_b"].shift(1)
b["next_b"] = b.groupby("instrument")["price_b"].shift(-1)
m = m.merge(b[["instrument","date","prev_b","next_b"]], on=["instrument","date"], how="left")

def pct(x, y): return abs(x - y) / y * 100

m["shift_pct"] = np.fmin(pct(m.price_a, m.prev_b), pct(m.price_a, m.next_b))

FX = ["EURUSD", "GBPUSD", "USDJPY"]

def classify(r):
    if r["_merge"] == "left_only":  return "Missing in B"
    if r["_merge"] == "right_only": return "Missing in A"
    inst = r["instrument"]
    if inst == "US 10Y":
        d = abs(r.price_a - r.price_b) * 100
        tol_match, tol_minor = 2, 5
        shift_d = r.shift_pct * r.price_b
    elif inst in FX:
        d = r.diff_pct; tol_match, tol_minor = 0.5, 1.0; shift_d = r.shift_pct
    else:
        d = r.diff_pct; tol_match, tol_minor = 0.05, 1.0; shift_d = r.shift_pct
    if d <= tol_match: return "Match"
    if d <= tol_minor: return "Minor break"
    if pd.notna(shift_d) and shift_d <= tol_match: return "Date shift (likely)"
    return "Major break"

m["status"] = m.apply(classify, axis=1)
m.to_csv("recon_classified.csv", index=False)

print(m.status.value_counts())
print(m.groupby(["instrument","status"]).size().unstack(fill_value=0))
print(m[m.status == "Major break"].sort_values("diff_pct", ascending=False)
        [["date","instrument","price_a","price_b","diff_pct"]].head(10).to_string())

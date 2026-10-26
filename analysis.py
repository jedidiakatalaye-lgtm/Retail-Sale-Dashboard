"""Retail case study: cleaning -> revenue trends -> customer segments -> retention.

Dataset: UCI Online Retail (UK gift retailer, 1 Dec 2010 - 9 Dec 2011), CC BY 4.0.
Run:  python analysis.py
"""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAW = "data/online-retail-dataset.csv"
FIG, RES = pathlib.Path("figures"), pathlib.Path("results")
FIG.mkdir(exist_ok=True); RES.mkdir(exist_ok=True)
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130})
S = {}  # summary numbers written to results/summary.json

# ---------- 1. Load & clean (every step is counted) ----------
df = pd.read_csv(RAW, encoding="latin-1", dtype={"InvoiceNo": str, "StockCode": str})
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M")
df["Revenue"] = df["Quantity"] * df["UnitPrice"]
log = [("Raw rows", len(df))]

is_cancel = df["InvoiceNo"].str.startswith("C")
S["cancel_invoices"] = int(df.loc[is_cancel, "InvoiceNo"].nunique())
S["total_invoices"] = int(df["InvoiceNo"].nunique())
S["cancel_value"] = float(-df.loc[is_cancel, "Revenue"].sum())
df = df[~is_cancel]; log.append(("Remove cancellation invoices (start with 'C')", len(df)))

df = df[df["StockCode"].str.match(r"^\d{5}", na=False)]
log.append(("Remove non-product codes (postage, fees, manual, etc.)", len(df)))

df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
log.append(("Remove zero/negative quantity or price", len(df)))

df = df.drop_duplicates()
log.append(("Remove exact duplicate rows", len(df)))

S["revenue_clean"] = float(df["Revenue"].sum())
S["missing_customer_share_rev"] = float(df.loc[df["CustomerID"].isna(), "Revenue"].sum() / df["Revenue"].sum())
S["missing_customer_share_rows"] = float(df["CustomerID"].isna().mean())
pd.DataFrame(log, columns=["step", "rows_after"]).to_csv(RES / "cleaning_log.csv", index=False)
S["cancel_value_pct_of_rev"] = S["cancel_value"] / S["revenue_clean"]
S["cancel_invoice_share"] = S["cancel_invoices"] / S["total_invoices"]

# ---------- 2. Monthly revenue ----------
df["Month"] = df["InvoiceDate"].dt.to_period("M")
monthly = df.groupby("Month")["Revenue"].sum()
monthly.to_csv(RES / "monthly_revenue.csv")
S["peak_month"] = str(monthly.idxmax()); S["peak_month_rev"] = float(monthly.max())
S["sep_oct_avg"] = float(monthly[["2011-09", "2011-10"]].mean()) if False else float(monthly.loc[pd.Period("2011-09"):pd.Period("2011-10")].mean())
S["nov_2011"] = float(monthly.loc[pd.Period("2011-11")])
S["spring_avg"] = float(monthly.loc[pd.Period("2011-02"):pd.Period("2011-05")].mean())

fig, ax = plt.subplots(figsize=(8, 3.8))
colors = ["#c0c0c0" if str(m) == "2011-12" else "#2F6FDE" for m in monthly.index]
ax.bar(monthly.index.astype(str), monthly.values / 1e3, color=colors)
ax.set_ylabel("Revenue (GBP thousands)"); ax.set_title("Monthly revenue (Dec 2011 is a partial month, data ends 9 Dec)")
plt.xticks(rotation=45, ha="right"); plt.tight_layout(); plt.savefig(FIG / "monthly_revenue.png"); plt.close()

# ---------- 3. Countries ----------
ctry = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False)
S["uk_share"] = float(ctry["United Kingdom"] / ctry.sum())
non_uk = ctry.drop("United Kingdom").head(5)
S["top_non_uk"] = {k: float(v) for k, v in non_uk.items()}
ctry.to_csv(RES / "revenue_by_country.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.4))
ax.barh(non_uk.index[::-1], non_uk.values[::-1] / 1e3, color="#2F6FDE")
ax.set_xlabel("Revenue (GBP thousands)"); ax.set_title("Top 5 markets outside the UK")
plt.tight_layout(); plt.savefig(FIG / "top_non_uk_markets.png"); plt.close()

# ---------- 4. Customer value (known customers only) ----------
cust = df.dropna(subset=["CustomerID"]).copy()
cust["CustomerID"] = cust["CustomerID"].astype(int)
snapshot = cust["InvoiceDate"].max() + pd.Timedelta(days=1)
rfm = cust.groupby("CustomerID").agg(
    recency=("InvoiceDate", lambda s: (snapshot - s.max()).days),
    frequency=("InvoiceNo", "nunique"),
    monetary=("Revenue", "sum"))
S["customers"] = int(len(rfm))
S["repeat_rate"] = float((rfm["frequency"] > 1).mean())

srt = rfm["monetary"].sort_values(ascending=False)
top20 = srt.head(int(len(srt) * 0.2)).sum() / srt.sum()
S["top20_share"] = float(top20)
cum = srt.cumsum() / srt.sum()
fig, ax = plt.subplots(figsize=(5.5, 3.8))
ax.plot(np.arange(1, len(cum) + 1) / len(cum) * 100, cum.values * 100, color="#2F6FDE", lw=2)
ax.axvline(20, ls="--", color="grey"); ax.axhline(top20 * 100, ls="--", color="grey")
ax.set_xlabel("% of customers (highest spend first)"); ax.set_ylabel("% of revenue")
ax.set_title(f"Top 20% of customers = {top20*100:.0f}% of revenue")
plt.tight_layout(); plt.savefig(FIG / "revenue_concentration.png"); plt.close()

rfm["R"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
def segment(r):
    if r.R >= 4 and r.F >= 4: return "Champions"
    if r.R <= 2 and r.F >= 4: return "At risk (were frequent)"
    if r.R >= 4 and r.F <= 2: return "Recent, low frequency"
    return "Others"
rfm["segment"] = rfm.apply(segment, axis=1)
seg = rfm.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"))
seg["pct_customers"] = seg["customers"] / seg["customers"].sum() * 100
seg["pct_revenue"] = seg["revenue"] / seg["revenue"].sum() * 100
seg = seg.sort_values("revenue", ascending=False)
seg.round(1).to_csv(RES / "rfm_segments.csv")
S["segments"] = {k: {"pct_customers": round(v.pct_customers, 1), "pct_revenue": round(v.pct_revenue, 1),
                     "customers": int(v.customers)} for k, v in seg.iterrows()}
fig, ax = plt.subplots(figsize=(7, 3.6))
y = np.arange(len(seg)); ax.barh(y + 0.2, seg["pct_customers"], 0.4, label="% of customers", color="#b8c4d6")
ax.barh(y - 0.2, seg["pct_revenue"], 0.4, label="% of revenue", color="#2F6FDE")
ax.set_yticks(y); ax.set_yticklabels(seg.index); ax.invert_yaxis(); ax.legend(frameon=False)
ax.set_title("Customer segments (RFM)"); plt.tight_layout(); plt.savefig(FIG / "rfm_segments.png"); plt.close()

# ---------- 5. Cohort retention ----------
cust["order_month"] = cust["InvoiceDate"].dt.to_period("M")
cust["cohort"] = cust.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period("M")
cust["age"] = (cust["order_month"] - cust["cohort"]).apply(lambda x: x.n)
cohort = cust.groupby(["cohort", "age"])["CustomerID"].nunique().unstack(fill_value=0)
retention = cohort.div(cohort[0], axis=0) * 100
retention.round(1).to_csv(RES / "cohort_retention.csv")
# Data ends 9 Dec 2011, so cells in Dec 2011 are partial: exclude them from averages and the heatmap.
S["m1_retention_avg"] = float(retention[1].iloc[:-2].mean())
S["m3_retention_avg"] = float(retention[3].iloc[:-4].mean())
S["dec10_cohort_size"] = int(cohort.loc[pd.Period("2010-12"), 0])
S["dec10_m1"] = float(retention.loc[pd.Period("2010-12"), 1])
S["dec10_m11"] = float(retention.loc[pd.Period("2010-12"), 11])
fig, ax = plt.subplots(figsize=(8, 4.6))
data = np.ma.masked_invalid(retention.where(cohort > 0).values.astype(float))
grid = np.where(cohort.values == 0, np.nan, retention.values).astype(float)
for i, c in enumerate(retention.index):
    for j, a in enumerate(retention.columns):
        if c + a == pd.Period("2011-12"):
            grid[i, j] = np.nan
im = ax.imshow(grid, cmap="Blues", vmin=0, vmax=50, aspect="auto")
ax.set_xticks(range(retention.shape[1])); ax.set_yticks(range(retention.shape[0]))
ax.set_yticklabels(retention.index.astype(str)); ax.set_xlabel("Months since first purchase")
ax.set_title("Cohort retention (% of cohort still buying; partial Dec 2011 hidden)")
plt.colorbar(im, ax=ax, shrink=0.8); plt.tight_layout(); plt.savefig(FIG / "cohort_retention.png"); plt.close()

json.dump(S, open(RES / "summary.json", "w"), indent=2)
print(pd.DataFrame(log, columns=["step", "rows_after"]).to_string(index=False))
print(json.dumps(S, indent=2))

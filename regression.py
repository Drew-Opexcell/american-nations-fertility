"""Does regional culture predict county fertility net of the usual suspects?

Outcome: county GFR (births per 1,000 women 15-44, 2021-2024 pooled;
Census CO-EST births / CC-EST agesex denominators, all counties).
Predictors: Woodard nation dummies (ref = Yankeedom), religious adherence
rate (2020 US Religion Census, TOTRATE_2020 per 1,000 population), log median
household income 2022 (ERS), percent adults BA+ 2019-23 (ERS), RUCC 2023
urbanicity (metro dummy + continuum code).
WLS weighted by women 15-44; HC1 robust SEs and state-clustered SEs.
Robustness: same model on TFR for identified (100k+) counties.

Raw inputs live in repo .tmp/ (re-downloadable); run from there or pass --raw.
"""
import os

# Repo-relative paths. Override the raw-input directory with ANF_RAW if you
# keep the large downloads elsewhere; see fetch_data.py.
PROJ = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("ANF_RAW", os.path.join(PROJ, "raw"))
DATA = os.path.join(PROJ, "data")
import csv
import sys
from collections import defaultdict

import numpy as np
import pandas as pd


# --- fertility outcome: GFR per county ---
births = {}
for row in csv.DictReader(open(os.path.join(RAW, "co-est2024-alldata.csv"), encoding="latin-1")):
    if row["SUMLEV"] != "050":
        continue
    fips = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
    births[fips] = sum(int(row[f"BIRTHS{y}"]) for y in (2021, 2022, 2023, 2024))

women = defaultdict(int)
for row in csv.DictReader(open(os.path.join(RAW, "cc-est2024-agesex.csv"), encoding="latin-1")):
    if row["YEAR"] in ("3", "4", "5", "6"):
        women[row["STATE"].zfill(2) + row["COUNTY"].zfill(3)] += int(row["AGE1544_FEM"])

# --- nation assignment ---
nation = {}
for row in csv.DictReader(open(os.path.join(DATA, "county_nation.csv"), encoding="utf-8")):
    nation[row["county_fips"]] = row["nation"]

def nation_of(f):
    return "YANKEEDOM" if f.startswith("09") else nation.get(f)

# --- controls ---
adh = {}
rel = pd.read_excel(os.path.join(RAW, "rcms2020_fixed.xlsx"), sheet_name="Data",
                    usecols=["FIPS", "TOTRATE_2020"])
for _, r in rel.iterrows():
    if pd.notna(r["FIPS"]):
        adh[str(int(r["FIPS"])).zfill(5)] = r["TOTRATE_2020"]

edu = {}
for row in csv.DictReader(open(os.path.join(RAW, "ers_education.csv"), encoding="latin-1")):
    if row["Attribute"] == "Percent of adults with a bachelor's degree or higher, 2019-23":
        try:
            edu[str(int(row["FIPS Code"])).zfill(5)] = float(row["Value"])
        except ValueError:
            pass

inc = {}
for row in csv.DictReader(open(os.path.join(RAW, "ers_unemployment.csv"), encoding="latin-1")):
    if row["Attribute"] == "Median_Household_Income_2022":
        try:
            inc[str(int(row["FIPS_Code"])).zfill(5)] = float(row["Value"].replace(",", ""))
        except ValueError:
            pass

rucc = {}
for row in csv.DictReader(open(os.path.join(RAW, "rucc2023.csv"), encoding="latin-1")):
    if row["Attribute"] == "RUCC_2023":
        rucc[row["FIPS"].zfill(5)] = int(row["Value"])

# --- assemble ---
rows = []
for fips, b in births.items():
    nat = nation_of(fips)
    w = women.get(fips, 0)
    if not nat or nat == "NA" or w < 100:
        continue
    if fips not in adh or pd.isna(adh[fips]) or fips not in edu or fips not in inc or fips not in rucc:
        continue
    rows.append({
        "fips": fips, "state": fips[:2], "nation": nat,
        "gfr": b / w * 1000, "women": w / 4,
        "adherence": adh[fips], "log_income": np.log(inc[fips]),
        "pct_ba": edu[fips], "rucc": rucc[fips], "metro": 1 if rucc[fips] <= 3 else 0,
    })
df = pd.DataFrame(rows)
print(f"counties in model: {len(df)} (dropped {len(births) - len(df)})")

# TFR outcome for identified counties
tfr = pd.read_csv(os.path.join(DATA, "county_tfr_identified.csv"), dtype={"county_fips": str})
df = df.merge(tfr[["county_fips", "tfr_2021_2024"]], left_on="fips",
              right_on="county_fips", how="left")

NATIONS = ["GREATER APPALACHIA", "DEEP SOUTH", "THE MIDLANDS", "THE FAR WEST",
           "TIDEWATER", "EL NORTE", "THE LEFT COAST", "NEW FRANCE",
           "PART OF THE SPANISH CARIBBEAN"]  # ref = YANKEEDOM

def design(d, with_controls=True, with_nation=True):
    X, names = [np.ones(len(d))], ["const"]
    if with_controls:
        for c in ["adherence", "log_income", "pct_ba", "metro", "rucc"]:
            X.append(d[c].to_numpy(float))
            names.append(c)
    if with_nation:
        for n in NATIONS:
            X.append((d["nation"] == n).to_numpy(float))
            names.append(n)
    return np.column_stack(X), names

def wls(y, X, w, cluster=None):
    sw = np.sqrt(w)
    Xw, yw = X * sw[:, None], y * sw
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    resid = yw - Xw @ beta
    XtX_inv = np.linalg.inv(Xw.T @ Xw)
    if cluster is None:  # HC1
        meat = (Xw * (resid ** 2)[:, None]).T @ Xw
        dof = len(y) / (len(y) - X.shape[1])
        V = XtX_inv @ meat @ XtX_inv * dof
    else:
        meat = np.zeros((X.shape[1], X.shape[1]))
        for g in np.unique(cluster):
            m = cluster == g
            s = Xw[m].T @ resid[m]
            meat += np.outer(s, s)
        G = len(np.unique(cluster))
        dof = G / (G - 1) * (len(y) - 1) / (len(y) - X.shape[1])
        V = XtX_inv @ meat @ XtX_inv * dof
    se = np.sqrt(np.diag(V))
    ybar = np.average(y, weights=w)
    r2 = 1 - np.sum(w * (y - X @ beta) ** 2) / np.sum(w * (y - ybar) ** 2)
    return beta, se, r2

def run(d, ycol, label):
    d = d.dropna(subset=[ycol])
    y, w, cl = d[ycol].to_numpy(float), d["women"].to_numpy(float), d["state"].to_numpy()
    Xn, names_n = design(d, with_controls=False)   # Model 1: nations only (total gaps)
    Xc, _ = design(d, with_nation=False)           # Model 2: controls only
    X1, names = design(d)                          # Model 3: both (direct effect)
    beta_n, _, r2_n = wls(y, Xn, w)
    _, se_n_cl, _ = wls(y, Xn, w, cluster=cl)
    _, _, r2_0 = wls(y, Xc, w)
    beta, se_hc1, r2_1 = wls(y, X1, w)
    _, se_cl, _ = wls(y, X1, w, cluster=cl)
    print(f"\n=== {label} (n={len(d)}) ===")
    print(f"R2 nations only: {r2_n:.4f}   controls only: {r2_0:.4f}   both: {r2_1:.4f}   (nation adds {r2_1 - r2_0:.4f})")
    print(f"{'term':30s} {'raw gap':>9s} {'se':>7s}   {'adjusted':>9s} {'se':>7s}")
    for i, n in enumerate(names):
        j = names_n.index(n) if n in names_n else None
        raw = f"{beta_n[j]:9.3f} {se_n_cl[j]:7.3f}" if j is not None else " " * 17
        star = "*" if abs(beta[i]) > 1.96 * se_cl[i] else " "
        print(f"{n:30s} {raw}   {beta[i]:9.3f} {se_cl[i]:7.3f}{star}")
    raw_map = dict(zip(names_n, beta_n))
    raw_se_map = dict(zip(names_n, se_n_cl))
    return pd.DataFrame({"term": names, "coef": beta, "se_hc1": se_hc1,
                         "se_clustered": se_cl,
                         "raw_gap": [raw_map.get(n) for n in names],
                         "raw_se_clustered": [raw_se_map.get(n) for n in names],
                         "model": ycol, "n": len(d), "r2_nations_only": r2_n,
                         "r2_controls": r2_0, "r2_full": r2_1})

out = pd.concat([
    run(df, "gfr", "GFR, all counties, WLS by women 15-44"),
    run(df, "tfr_2021_2024", "TFR, identified counties only (robustness)"),
])
out.to_csv(os.path.join(DATA, "regression_coefficients.csv"), index=False)

df.to_csv(os.path.join(DATA, "regression_dataset.csv"), index=False)
print(f"\nwrote {DATA}/regression_dataset.csv")

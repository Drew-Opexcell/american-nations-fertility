"""Nation-level general fertility rates from complete county data.

Births: Census CO-EST2024 components file (BIRTHS2021-2024, vintage estimates,
every county, no suppression). Denominator: CC-EST2024 agesex file, female 15-44
per county (AGE1544_FEM), YEAR codes 3-6 = July 2021-2024 estimates.
Nation assignment: county_nation.csv derived from Urban Institute NCCS TRACTX
(Woodard region per tract, plurality by county; borders follow county lines).
GFR = births per 1,000 women 15-44, pooled 2021-2024.
"""
import os

# Repo-relative paths. Override the raw-input directory with ANF_RAW if you
# keep the large downloads elsewhere; see fetch_data.py.
PROJ = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("ANF_RAW", os.path.join(PROJ, "raw"))
DATA = os.path.join(PROJ, "data")
import csv
from collections import defaultdict

nation = {}
with open(os.path.join(DATA, "county_nation.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        nation[row["county_fips"]] = row["nation"]

births = defaultdict(int)
with open(os.path.join(RAW, "co-est2024-alldata.csv"), newline="", encoding="latin-1") as f:
    for row in csv.DictReader(f):
        if row["SUMLEV"] != "050":
            continue
        fips = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
        births[fips] = sum(int(row[f"BIRTHS{y}"]) for y in (2021, 2022, 2023, 2024))

women = defaultdict(int)
with open(os.path.join(RAW, "cc-est2024-agesex.csv"), newline="", encoding="latin-1") as f:
    for row in csv.DictReader(f):
        if row["YEAR"] not in ("3", "4", "5", "6"):
            continue
        fips = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
        women[fips] += int(row["AGE1544_FEM"])

agg = defaultdict(lambda: [0, 0, 0])
missing = 0
for fips, b in births.items():
    nat = nation.get(fips)
    if nat is None:
        missing += 1
        continue
    agg[nat][0] += b
    agg[nat][1] += women.get(fips, 0)
    agg[nat][2] += 1

print(f"counties with births but no nation: {missing}")
print(f"{'nation':32s} {'GFR':>6s} {'births/yr':>10s} {'counties':>9s}")
rows = []
for nat, (b, w, n) in agg.items():
    if w == 0:
        continue
    gfr = b / w * 1000  # person-years: births and women both pooled over 4 years
    rows.append((gfr, nat, b, n))
for gfr, nat, b, n in sorted(rows, reverse=True):
    print(f"{nat:32s} {gfr:6.1f} {b//4:10,d} {n:9,d}")

tb = sum(r[2] for r in rows)
tw = sum(agg[r[1]][1] for r in rows)
print(f"\n{'ALL CLASSIFIED':32s} {tb/tw*1000:6.1f} {tb//4:10,d}")

with open(os.path.join(DATA, "nation_gfr.csv"), "w", newline="", encoding="utf-8") as f:
    w2 = csv.writer(f)
    w2.writerow(["nation", "gfr_2021_2024", "births_per_year", "n_counties"])
    for gfr, nat, b, n in sorted(rows, reverse=True):
        w2.writerow([nat, round(gfr, 2), b // 4, n])
print("wrote nation_gfr.csv")

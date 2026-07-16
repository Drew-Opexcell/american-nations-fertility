"""Nation-level total fertility rates, 2021-2024 pooled.

Births: CDC WONDER natality (D66), county x Age of Mother 9, years 2021-2024.
Identified counties only (100k+ population); each state's small-county pool
arrives as an "Unidentified Counties" row and is allocated to nations in
proportion to age-specific female population of that state's non-identified
counties. Sensitivity: identified-only TFR reported alongside.

Denominators: CC-EST2024 agesex, YEAR codes 3-6 (July 2021-2024), female
5-year bins. TFR = 5 x sum of age-specific rates; births to mothers under 15
are rated against women 10-14, births 50+ folded into 45-49 (NCHS convention).

CT geography: WONDER reports births under the legacy county FIPS (09001...),
while Census 2024 reports population under the new planning regions (09110...).
The codes do not nest, so no county-level join exists. All of Connecticut is
Yankeedom, so both sides still aggregate correctly at the nation level (the
headline column). The identified-only sensitivity column cannot match them and
therefore EXCLUDES Connecticut from both numerator and denominator; counties
with no matching denominator are omitted from the county file rather than
written as zero.
AK, HI, and territories are excluded (no Woodard assignment in the crosswalk).
"""
import os

# Repo-relative paths. Override the raw-input directory with ANF_RAW if you
# keep the large downloads elsewhere; see fetch_data.py.
PROJ = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("ANF_RAW", os.path.join(PROJ, "raw"))
DATA = os.path.join(PROJ, "data")
import csv
from collections import defaultdict

AGES = ["15", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"]
DENOM_BIN = {"15": "AGE1014_FEM", "15-19": "AGE1519_FEM", "20-24": "AGE2024_FEM",
             "25-29": "AGE2529_FEM", "30-34": "AGE3034_FEM", "35-39": "AGE3539_FEM",
             "40-44": "AGE4044_FEM", "45-49": "AGE4549_FEM", "50+": None}

nation = {}
with open(os.path.join(DATA, "county_nation.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        nation[row["county_fips"]] = row["nation"]

def nation_of(fips):
    if fips.startswith("09"):
        return "YANKEEDOM"
    return nation.get(fips)

women = defaultdict(lambda: defaultdict(int))  # fips -> bin -> person-years
with open(os.path.join(RAW, "cc-est2024-agesex.csv"), newline="", encoding="latin-1") as f:
    for row in csv.DictReader(f):
        if row["YEAR"] not in ("3", "4", "5", "6"):
            continue
        fips = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
        for b in set(DENOM_BIN.values()):
            if b:
                women[fips][b] += int(row[b])

ident_births = defaultdict(lambda: defaultdict(int))   # fips -> age -> births
unident_births = defaultdict(lambda: defaultdict(int)) # state fips -> age -> births
suppressed = 0
with open(os.path.join(DATA, "wonder_county_age_2021_2024.txt"), encoding="utf-8") as f:
    rdr = csv.reader(f, delimiter="\t")
    header = next(rdr)
    for row in rdr:
        if len(row) < 6 or not row[2].strip('"'):
            break  # footnotes section
        cname, code, age, births = row[1].strip('"'), row[2].strip('"'), row[4].strip('"'), row[5].strip('"')
        if age not in AGES:
            continue
        if births in ("Suppressed", "Missing"):
            suppressed += 1
            continue
        b = int(births)
        if "Unidentified" in cname:
            unident_births[code[:2]][age] += b
        else:
            ident_births[code][age] += b

# nation x age births: identified counties directly. Connecticut's legacy county
# codes carry real births and aggregate correctly here, because every CT code
# maps to Yankeedom on both sides even though the county codes themselves differ.
nat_births = defaultdict(lambda: defaultdict(float))
nat_women = defaultdict(lambda: defaultdict(int))

for fips, ages in ident_births.items():
    nat = nation_of(fips)
    if not nat or nat == "NA":
        continue
    for a, b in ages.items():
        nat_births[nat][a] += b

# small-county allocation: per state, weight = age-specific women in
# non-identified counties by nation
for st, ages in unident_births.items():
    small = [f for f in women if f.startswith(st) and f not in ident_births]
    for a, b in ages.items():
        bin_ = DENOM_BIN[a] or "AGE4549_FEM"
        wsum = defaultdict(int)
        for f in small:
            nat = nation_of(f)
            if nat and nat != "NA":
                wsum[nat] += women[f][bin_]
        tot = sum(wsum.values())
        if tot == 0:
            continue
        for nat, wgt in wsum.items():
            nat_births[nat][a] += b * wgt / tot

# nation denominators: ALL counties (identified + small) per nation
for fips, bins in women.items():
    nat = nation_of(fips)
    if not nat or nat == "NA":
        continue
    for b, v in bins.items():
        nat_women[nat][b] += v

# Identified-only sensitivity. Connecticut has births under legacy county codes
# but population only under planning regions, so it has no denominator here and
# is dropped from BOTH sides rather than counted as free births.
unmatched = sorted(f for f in ident_births if not women.get(f))
if unmatched:
    print(f"identified-only: dropping {len(unmatched)} counties with no matching "
          f"denominator (CT legacy FIPS): {', '.join(unmatched)}")

nat_births_ident = defaultdict(lambda: defaultdict(float))
nat_women_ident = defaultdict(lambda: defaultdict(int))
for fips, ages in ident_births.items():
    nat = nation_of(fips)
    if not nat or nat == "NA" or not women.get(fips):
        continue
    for a, b in ages.items():
        nat_births_ident[nat][a] += b
    for b, v in women[fips].items():
        nat_women_ident[nat][b] += v

def tfr(births_by_age, women_by_bin):
    total = 0.0
    for a in AGES:
        b = births_by_age.get(a, 0)
        if a == "50+":
            continue  # folded below
        if a == "45-49":
            b += births_by_age.get("50+", 0)
        w = women_by_bin.get(DENOM_BIN[a], 0)
        if w:
            total += 5.0 * b / w
    return total

print(f"suppressed cells skipped: {suppressed}")
print(f"{'nation':32s} {'TFR':>6s} {'TFR ident-only':>15s}")
rows = []
for nat in nat_births:
    t_full = tfr(nat_births[nat], nat_women[nat])
    t_id = tfr(nat_births_ident[nat], nat_women_ident[nat])
    rows.append((t_full, t_id, nat))
for t_full, t_id, nat in sorted(rows, reverse=True):
    print(f"{nat:32s} {t_full:6.3f} {t_id:15.3f}")

with open(os.path.join(DATA, "nation_tfr.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nation", "tfr_2021_2024", "tfr_identified_only"])
    for t_full, t_id, nat in sorted(rows, reverse=True):
        w.writerow([nat, round(t_full, 3), round(t_id, 3)])

# county-level TFR for identified counties (regression/maps). Counties with no
# matching denominator (CT legacy FIPS) are omitted, never written as zero.
with open(os.path.join(DATA, "county_tfr_identified.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["county_fips", "nation", "tfr_2021_2024", "births_per_year"])
    for fips, ages in sorted(ident_births.items()):
        nat = nation_of(fips)
        if not nat or nat == "NA" or not women.get(fips):
            continue
        w.writerow([fips, nat, round(tfr(ages, women[fips]), 3), sum(ages.values()) // 4])
print("wrote nation_tfr.csv, county_tfr_identified.csv")

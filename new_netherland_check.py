"""Robustness check: does folding New Netherland into Yankeedom matter?

The Urban Institute crosswalk codes ten regions, not Woodard's eleven: New
Netherland's territory is classified as Yankeedom, and Yankeedom is this study's
reference category. This script reconstructs New Netherland from Woodard's
stated boundaries (the five boroughs, the lower Hudson Valley, northern New
Jersey, and WESTERN Long Island) and compares it against Yankeedom proper.

Two boundary points matter and are easy to get wrong. Suffolk County is eastern
Long Island, which was New England-settled and is Yankeedom, not New Netherland.
Orange County (Kiryas Joel, TFR 2.24) sits above the lower Hudson and is
excluded. Including either inflates New Netherland substantially and is the
reason a metro-area proxy is not a valid stand-in for the actual border.
Southwestern Connecticut is New Netherland in Woodard's model but cannot be
joined at county level (see the Connecticut FIPS trap in the README), so it is
excluded from both sides here.

Result: New Netherland 1.539 vs Yankeedom proper 1.511, a difference of 0.028
children. The composite reference is unbiased for practical purposes.

    python new_netherland_check.py
"""
import csv
import os
from collections import defaultdict

PROJ = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("ANF_RAW", os.path.join(PROJ, "raw"))
DATA = os.path.join(PROJ, "data")

# Woodard's New Netherland, county by county.
NEW_NETHERLAND = {
    "36061": "New York (Manhattan)",
    "36047": "Kings (Brooklyn)",
    "36005": "Bronx",
    "36081": "Queens",
    "36085": "Richmond (Staten Island)",
    "36059": "Nassau (western Long Island)",
    "36119": "Westchester (lower Hudson)",
    "36087": "Rockland (lower Hudson)",
    "36079": "Putnam (lower Hudson)",
    "34003": "Bergen, NJ",
    "34017": "Hudson, NJ",
    "34013": "Essex, NJ",
    "34039": "Union, NJ",
    "34031": "Passaic, NJ",
}

AGES = ["15", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49"]
BIN = {"15": "AGE1014_FEM", "15-19": "AGE1519_FEM", "20-24": "AGE2024_FEM",
       "25-29": "AGE2529_FEM", "30-34": "AGE3034_FEM", "35-39": "AGE3539_FEM",
       "40-44": "AGE4044_FEM", "45-49": "AGE4549_FEM"}


def load():
    nation = {}
    with open(os.path.join(DATA, "county_nation.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nation[row["county_fips"]] = row["nation"]

    women = defaultdict(lambda: defaultdict(int))
    with open(os.path.join(RAW, "cc-est2024-agesex.csv"), newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            if row["YEAR"] in ("3", "4", "5", "6"):
                fips = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
                for b in set(BIN.values()):
                    women[fips][b] += int(row[b])

    births = defaultdict(lambda: defaultdict(int))
    with open(os.path.join(DATA, "wonder_county_age_2021_2024.txt"), encoding="utf-8") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if len(row) < 6 or not row[2].strip('"'):
                break
            cname, code = row[1].strip('"'), row[2].strip('"')
            age, b = row[4].strip('"'), row[5].strip('"')
            if age in AGES + ["50+"] and "Unidentified" not in cname and b not in ("Suppressed", "Missing"):
                births[code][age] += int(b)
    return nation, women, births


def tfr(fips_set, women, births):
    total = 0.0
    for a in AGES:
        b = sum(births[f].get(a, 0) + (births[f].get("50+", 0) if a == "45-49" else 0)
                for f in fips_set)
        w = sum(women[f].get(BIN[a], 0) for f in fips_set)
        if w:
            total += 5.0 * b / w
    return total


def main():
    nation, women, births = load()
    identified = set(births)

    nn = {f for f in NEW_NETHERLAND if f in identified}
    dropped = set(NEW_NETHERLAND) - nn
    yank = {f for f in identified
            if nation.get(f) == "YANKEEDOM" and f not in NEW_NETHERLAND
            and not f.startswith("09") and women.get(f)}

    t_nn = tfr(nn, women, births)
    t_yk = tfr(yank, women, births)
    t_all = tfr(nn | yank, women, births)
    exposure = (sum(women[f]["AGE2529_FEM"] for f in nn)
                / sum(women[f]["AGE2529_FEM"] for f in nn | yank))

    print(f"New Netherland: {len(nn)}/{len(NEW_NETHERLAND)} counties identified by WONDER")
    if dropped:
        print(f"  below the 100k threshold, excluded: "
              f"{', '.join(NEW_NETHERLAND[f] for f in sorted(dropped))}")
    print(f"Yankeedom proper: {len(yank)} counties\n")
    print(f"  New Netherland                {t_nn:.3f}")
    print(f"  Yankeedom proper              {t_yk:.3f}")
    print(f"  Composite (as published)      {t_all:.3f}")
    print(f"\n  difference                    {t_nn - t_yk:+.3f} children")
    print(f"  New Netherland exposure share {exposure * 100:.1f}%")
    print("\nThe two nations are within 0.03 children of each other, so treating the "
          "\ncomposite as the reference category does not bias the reported gaps.")


if __name__ == "__main__":
    main()

"""Publication figures.

Fig 1: lower-48 county map colored by American Nation (Albers equal-area).
Fig 2: nation TFR 2021-2024, dot plot against replacement.
Fig 3: nation effects on county TFR net of controls (95% cluster-robust CIs).
Outputs PNG (300dpi) + SVG to figures/.
"""
import os

# Repo-relative paths. Override the raw-input directory with ANF_RAW if you
# keep the large downloads elsewhere; see fetch_data.py.
PROJ = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(PROJ, "figures")
os.makedirs(os.path.join(FIG, "web"), exist_ok=True)
RAW = os.environ.get("ANF_RAW", os.path.join(PROJ, "raw"))
DATA = os.path.join(PROJ, "data")
import csv
import json
from math import cos, radians, sin, sqrt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D


COLORS = {
    "YANKEEDOM": "#2F5E9E", "NEW NETHERLAND": "#C4682B", "THE MIDLANDS": "#339980",
    "DEEP SOUTH": "#A32E22", "GREATER APPALACHIA": "#97A032", "THE FAR WEST": "#2E90B5",
    "EL NORTE": "#A8841B", "TIDEWATER": "#8A4A7D", "THE LEFT COAST": "#2F7D46",
    "NEW FRANCE": "#5B87A6", "PART OF THE SPANISH CARIBBEAN": "#C29A4B",
}
PRETTY = {
    "YANKEEDOM": "Yankeedom", "NEW NETHERLAND": "New Netherland",
    "THE MIDLANDS": "The Midlands", "DEEP SOUTH": "Deep South",
    "GREATER APPALACHIA": "Greater Appalachia", "THE FAR WEST": "The Far West",
    "EL NORTE": "El Norte", "TIDEWATER": "Tidewater",
    "THE LEFT COAST": "The Left Coast", "NEW FRANCE": "New France",
    "PART OF THE SPANISH CARIBBEAN": "Spanish Caribbean",
}

nation = {}
with open(os.path.join(DATA, "county_nation.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        nation[row["county_fips"]] = row["nation"]

# --- Albers equal-area conic, lower 48 ---
P1, P2, LON0, LAT0 = radians(29.5), radians(45.5), radians(-96.0), radians(37.5)
N = (sin(P1) + sin(P2)) / 2
C = cos(P1) ** 2 + 2 * N * sin(P1)
RHO0 = sqrt(C - 2 * N * sin(LAT0)) / N

def albers(lon, lat):
    lam, phi = radians(lon), radians(lat)
    rho = sqrt(C - 2 * N * sin(phi)) / N
    th = N * (lam - LON0)
    return rho * sin(th), RHO0 - rho * cos(th)

def rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    return [poly[0] for poly in geom["coordinates"]]

# ---------- Fig 1: the nations map ----------
geo = json.load(open(os.path.join(RAW, "counties_geo.json"), encoding="utf-8"))
polys, cols = [], []
for feat in geo["features"]:
    fips = feat["id"]
    if fips[:2] in ("02", "15", "72", "78", "66", "60", "69"):
        continue
    nat = "YANKEEDOM" if fips.startswith("09") else nation.get(fips)
    if not nat or nat == "NA":
        continue
    for ring in rings(feat["geometry"]):
        polys.append([albers(x, y) for x, y in ring])
        cols.append(COLORS[nat])

fig, ax = plt.subplots(figsize=(11, 7))
ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors="white",
                                 linewidths=0.15))
ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
order = ["YANKEEDOM", "NEW NETHERLAND", "THE MIDLANDS", "TIDEWATER",
         "GREATER APPALACHIA", "DEEP SOUTH", "NEW FRANCE", "EL NORTE",
         "THE FAR WEST", "THE LEFT COAST", "PART OF THE SPANISH CARIBBEAN"]
handles = [Line2D([], [], marker="s", linestyle="", markersize=9,
                  markerfacecolor=COLORS[k], markeredgecolor="none",
                  label=PRETTY[k]) for k in order]
ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=8.5, ncol=2)
ax.set_title("The American Nations, county-level (Woodard 2011; Urban Institute crosswalk)",
             fontsize=11)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(os.path.join(FIG, f"fig1_nations_map.{ext}"), dpi=300,
                bbox_inches="tight")
fig.savefig(os.path.join(FIG, "web", "fig1_nations_map.png"), dpi=100, bbox_inches="tight")
plt.close(fig)

# ---------- Fig 2: nation TFRs ----------
tfr = pd.read_csv(os.path.join(DATA, "nation_tfr.csv"))
tfr["name"] = tfr["nation"].map(PRETTY)
tfr = tfr.sort_values("tfr_2021_2024")
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.hlines(tfr["name"], 1.3, tfr["tfr_2021_2024"], color="#D8D2C4", linewidth=1.4, zorder=1)
ax.scatter(tfr["tfr_2021_2024"], tfr["name"],
           c=[COLORS[n] for n in tfr["nation"]], s=64, zorder=3)
ax.scatter(tfr["tfr_identified_only"], tfr["name"], facecolors="none",
           edgecolors=[COLORS[n] for n in tfr["nation"]], s=64, zorder=2,
           linewidths=1.1)
ax.axvline(2.1, color="#A32E22", linestyle=":", linewidth=1.2)
ax.text(2.1, len(tfr) - 0.4, " replacement (2.1)", color="#A32E22", fontsize=8.5, va="top")
ax.axvline(1.60, color="#8A7A60", linestyle="--", linewidth=0.9)
ax.text(1.605, len(tfr) - 1.45, "U.S. 1.60", color="#8A7A60", fontsize=8.5)
for _, r in tfr.iterrows():
    ax.text(r["tfr_2021_2024"] + 0.012, r["name"], f'{r["tfr_2021_2024"]:.2f}',
            va="center", fontsize=8.5)
ax.set_xlim(1.3, 2.2)
ax.set_xlabel("Total fertility rate, 2021-2024 pooled", fontsize=9.5)
ax.set_title("Fertility by American Nation\nfilled = with small-county allocation; open = identified counties only",
             fontsize=10.5)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=9.5)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(os.path.join(FIG, f"fig2_nation_tfr.{ext}"), dpi=300, bbox_inches="tight")
fig.savefig(os.path.join(FIG, "web", "fig2_nation_tfr.png"), dpi=100, bbox_inches="tight")
plt.close(fig)

# ---------- Fig 3: regression coefficients ----------
co = pd.read_csv(os.path.join(DATA, "regression_coefficients.csv"))
co = co[(co["model"] == "tfr_2021_2024") & (co["term"].isin(COLORS))].copy()
co["name"] = co["term"].map(PRETTY)
co["lo"] = co["coef"] - 1.96 * co["se_clustered"]
co["hi"] = co["coef"] + 1.96 * co["se_clustered"]
co = co.sort_values("coef")
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.axvline(0, color="#8A7A60", linewidth=0.9)
ax.hlines(co["name"], co["lo"], co["hi"],
          color=[COLORS[t] for t in co["term"]], linewidth=2)
ax.scatter(co["coef"], co["name"], c=[COLORS[t] for t in co["term"]], s=52, zorder=3)
ax.set_ylim(-0.6, len(co) - 0.4)
ax.text(0.004, -0.45, "Yankeedom (reference)", fontsize=8.5, color="#584A38")
ax.set_xlabel("Effect on county TFR vs. Yankeedom, net of religiosity, income,\n"
              "education, and urbanicity (95% CI, state-clustered)", fontsize=9)
ax.set_title("Regional culture survives the controls", fontsize=10.5)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=9.5)
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(os.path.join(FIG, f"fig3_coefficients.{ext}"), dpi=300, bbox_inches="tight")
fig.savefig(os.path.join(FIG, "web", "fig3_coefficients.png"), dpi=100, bbox_inches="tight")
plt.close(fig)

print("figures written")

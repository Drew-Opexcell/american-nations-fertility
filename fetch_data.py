"""Download the raw public inputs into ./raw.

Everything here is free and public. Two files cannot be fetched programmatically
and must be downloaded by hand; this script tells you where to get them.

    python fetch_data.py
"""
import os
import urllib.request
import zipfile

RAW = os.environ.get("ANF_RAW", os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw"))
UA = {"User-Agent": "Mozilla/5.0 (research replication script)"}

FILES = {
    "TRACTX.csv":
        "https://nccsdata.s3.us-east-1.amazonaws.com/geo/xwalk/TRACTX.csv",
    "co-est2024-alldata.csv":
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
    "cc-est2024-agesex.csv":
        "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/asrh/cc-est2024-agesex-all.csv",
    "rucc2023.csv":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv",
    "ers_education.csv":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/48747/Education2023.csv",
    "ers_unemployment.csv":
        "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/48747/Unemployment2023.csv",
    "counties_geo.json":
        "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
}

MANUAL = {
    "rcms2020_county.xlsx": (
        "2020 U.S. Religion Census county file. OSF blocks scripted downloads; "
        "get it from https://www.thearda.com/data-archive?fid=RCMSCY20 (Downloads "
        "tab, 'Excel Data file') and save it here as rcms2020_county.xlsx."
    ),
    "wonder_county_age_2021_2024.txt": (
        "CDC WONDER natality. The API refuses county-grouped queries. Use "
        "https://wonder.cdc.gov/natality-current.html : Group by = County and "
        "'Age of Mother 9', years 2021-2024, tick 'Export Results', Send. "
        "A cached copy already ships in data/, so this is optional."
    ),
}


def patch_religion_census():
    """ARDA's xlsx carries a malformed `synchVertical` attribute that openpyxl
    rejects outright. Rewrite it to the spelling the parser expects."""
    src = os.path.join(RAW, "rcms2020_county.xlsx")
    dst = os.path.join(RAW, "rcms2020_fixed.xlsx")
    if not os.path.exists(src) or os.path.exists(dst):
        return
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            data = zin.read(item)
            if item.endswith(".xml"):
                data = data.replace(b"synchVertical", b"syncVertical")
                data = data.replace(b"synchHorizontal", b"syncHorizontal")
            zout.writestr(item, data)
    print("  patched -> rcms2020_fixed.xlsx")


def main():
    os.makedirs(RAW, exist_ok=True)
    for name, url in FILES.items():
        dest = os.path.join(RAW, name)
        if os.path.exists(dest):
            print(f"  have {name}")
            continue
        print(f"  fetching {name} ...")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())

    for name, note in MANUAL.items():
        if not os.path.exists(os.path.join(RAW, name)):
            print(f"\nMANUAL: {name}\n  {note}")

    patch_religion_census()
    print(f"\nraw inputs in {RAW}")


if __name__ == "__main__":
    main()

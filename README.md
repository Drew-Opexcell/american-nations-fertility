# Below Replacement, Unequally

Replication materials for *Below Replacement, Unequally: Settlement-Era Regional
Cultures and U.S. County Fertility.*

**Drew Patterson**, Independent Researcher
ORCID [0009-0005-9551-4948](https://orcid.org/0009-0005-9551-4948)

## Summary

The U.S. total fertility rate hit a record low of 1.60 in 2024. That national
figure hides a regional structure that is older than the country's
industrialization. This study maps county fertility onto the American Nations
model, a typology of settlement-era regional cultures (Woodard 2011) whose
borders follow county lines, and which has been applied to violence, health, and
political behavior but not, until now, to fertility.

Total fertility rate by nation, 2021-2024 pooled:

| Nation | TFR |
|---|---|
| New France | 1.77 |
| Greater Appalachia | 1.73 |
| The Midlands | 1.70 |
| Deep South | 1.70 |
| The Far West | 1.67 |
| Spanish Caribbean | 1.65 |
| Tidewater | 1.59 |
| El Norte | 1.55 |
| Yankeedom | 1.54 |
| The Left Coast | 1.42 |

Every nation is below replacement (2.1). Two findings stand out:

1. **Regional culture survives the usual controls.** Nation indicators add 11.0
   points of explained variance in county TFR (R² 0.353 to 0.463) beyond
   religious adherence, income, education, and urbanicity. Roughly a quarter of
   a child separates Greater Appalachia (+0.13 vs. Yankeedom) from the Left
   Coast (-0.11) net of composition, in a country whose entire 2007-2024
   fertility decline was about half a child.
2. **The ordering is historically legible.** The regions that led the
   antebellum fertility decline, Yankeedom and its Left Coast offshoot, sit at
   the floor of the contemporary distribution. The national rate (1.60) has
   converged on the level Yankeedom pioneered (1.54), while the regional
   ordering that region belonged to has not dissolved.

## Reproducing

All inputs are public and free. No proprietary dependencies; Python with
`pandas` and `numpy` only (`matplotlib` for figures).

| Script | Produces |
|---|---|
| `nation_gfr.py` | Complete-coverage general fertility rate per nation, all 3,098 classified counties |
| `nation_tfr.py` | Age-standardized TFR per nation (`data/nation_tfr.csv`) plus per-county TFRs |
| `regression.py` | Specification ladder, county models, coefficients (`data/regression_*.csv`) |
| `figures.py` | Figures 1-3 (PNG 300dpi + SVG) |

### Data sources

- **Births.** CDC WONDER Natality, county x mother's age, 2021-2024. The API
  refuses county-grouped queries; use the web form at
  `wonder.cdc.gov/natality-current.html`, set *Group by* = County and
  *Age of Mother 9*, select 2021-2024, check *Export Results*. A cached extract
  is included as `data/wonder_county_age_2021_2024.txt`.
- **Denominators.** Census Bureau Vintage 2024 county estimates
  (`cc-est2024-agesex-all.csv`, `co-est2024-alldata.csv`).
- **Cultural regions.** Urban Institute NCCS `TRACTX.csv` crosswalk, which codes
  each census tract with its American Nations region. Aggregated to counties in
  `data/county_nation.csv`.
- **Controls.** 2020 U.S. Religion Census county file (ARDA/OSF); USDA ERS
  county education and unemployment/income files; USDA ERS 2023 Rural-Urban
  Continuum Codes.

## Three data traps worth knowing about

These cost real time to find and are not documented anywhere obvious. If you
work with these sources, they will bite you too.

1. **Connecticut breaks every county join.** CDC WONDER reports Connecticut
   births under the legacy county FIPS (09001 Fairfield...), while Census 2024
   reports population under the new planning regions (09110 Capitol...). The
   codes do not nest, so a naive join silently produces ~35,000 births per year
   against a **zero denominator**. Because all of Connecticut is Yankeedom, both
   sides still aggregate correctly at the national level, but county-level work
   must drop it. This bug initially inflated Yankeedom's identified-county TFR
   to 1.60; the true figure is 1.52.
2. **The crosswalk has ten regions, not Woodard's eleven.** New Netherland is
   not coded separately; metropolitan New York and northern New Jersey are
   classified as Yankeedom. That is roughly **28 percent of the Yankeedom
   female population aged 15-44**, and Yankeedom is the reference category, so
   every coefficient is measured against a two-nation composite. Disclosed in
   the paper; splitting it out cleanly is unresolved (a NYC-CSA proxy is too
   broad, pulling in Fairfield and New Haven, which are genuinely Yankeedom,
   and it is dominated by the Hasidic counties of Rockland and Orange at TFR
   3.31 and 2.24).
3. **WONDER county coverage is 79.5 percent of births, not ~85.** It identifies
   578 counties with 2010 population above 100,000. County models here retain
   566 of them: eight Connecticut counties have no denominator, and four
   Alaska/Hawaii counties are unclassified by the crosswalk.

## Limitations

The design is ecological. Estimates describe places, not individuals, and cannot
decompose the residual into socialization, selective migration, unmeasured
composition, or genetic transmission (which gene-culture coevolution entangles
with the first two rather than separating from them). Adjudicating the genetic
channel would require mean polygenic scores by region, which do not exist for
these populations. Period TFR is also sensitive to tempo effects, though tempo
distortion would have to vary by nation to manufacture the cross-sectional
pattern reported here.

## Citation

> Patterson, Drew. 2026. "Below Replacement, Unequally: Settlement-Era Regional
> Cultures and U.S. County Fertility."

## License

Code: MIT. Derived data and text: CC BY 4.0. Underlying sources are public
domain (CDC, Census, USDA) or licensed by their respective providers
(Urban Institute NCCS, ARDA).

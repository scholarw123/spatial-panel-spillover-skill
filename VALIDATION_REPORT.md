# Public v0.4.0 release QA report (synthetic only)

- Test data were freshly generated with fixed seed `20260401`: **12 entirely fictional units × 6 periods = 72 records**.
- Unit tests: **10/10 pass**, covering Queen vs Rook shared-boundary rules, real-file adapter on artificial polygon geometry, artificial LISA map, KNN, normalization, graph isolates/components, distance-ring disjointness, Gaussian/economic inverse stability, Moran/LISA and eigenvalue-based rho bounds.
- End-to-end: `python scripts/smoke_test.py` passed; produced diagnostics / W matrices / ESDA / impacts / distance sensitivity / warnings without reading any private data.
- Synthetic demo output shape checked: 8 baseline W candidates, 4 normalizations, 6 economic inverse epsilon checks, 6 annual global/bivariate Moran observations, 72 LISA unit-years, 6 cumulative thresholds, 4 rings, 6 decay specifications.
- A disconnected cumulative W and a disconnected ring were **explicitly marked `diagnostic_only_disconnected` instead of silently treated as comparable SDM fits**.
- Synthetic polygon Queen/Rook and optional synthetic LISA map were tested with geopandas available in the build environment. In an installation without geopandas, the optional map test skips and the core runner remains available; real users must provide valid licensed boundary data.
- `requirements.txt` lists runtime dependencies; `geopandas` is optional for real boundary files/maps.
- The research protocol contains additional non-automated gate requirements (LM, LR/Wald, SAR/SEM comparisons). The v0.4 demonstration runner does **not** claim to have executed those gates.

**Public-data safety:** No private research spreadsheet, study variable names, real data-derived W, coefficient tables, true provincial coordinate listing or private validation results are present in this release package. The public generic Gaussian kernel follows its mathematical definition; it is not intended to reproduce numeric outputs from earlier internal prototype scripts.

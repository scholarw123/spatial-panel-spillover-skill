# Changelog

## v0.4.0 — 2026-09-26 (public preview update package)

### v0.2 · Spatial weight matrices
- Added generic inverse-distance, KNN, distance-band, economic similarity and geographic×economic matrices.
- Added Queen/Rook polygon geometry builders and optional boundary input (no fabricated administrative borders).
- Added W heatmaps, neighbor-count distributions, isolates, connectivity, density, normalization sensitivity and economic-inverse epsilon sensitivity.
- Corrected the named Gaussian economic kernel to `exp(-0.5*(gap/h)^2)` (as distinct from a Laplace/exponential-gap kernel); added positive bandwidth/epsilon validation including equal-economic-level edge cases.

### v0.3 · Exploratory spatial analysis
- Added annual univariate/bivariate permutation Moran, conditional-randomization LISA, scatterplots and time-series cluster counts.
- Added optional LISA polygon map only if a valid matching boundary file is supplied.
- Documented single-sided sign-directed global permutation p vs two-sided unadjusted local pseudo p.

### v0.4 · Distance and identification safeguards
- Added cumulative cutoffs, nonoverlapping rings, power/exponential decay and threshold-neighbor-impact visualizations.
- Added explicit isolate/disconnected/near-boundary warnings; not permitted to infer optimal distance or maximum radius from last significance.
- Derives rho search interval from W eigenvalues rather than hard-coding (-0.95,0.95).
- Added generic config-driven runner and deterministic synthetic demonstration; unit and smoke tests.

### Transparency
- Previously validated on a private research panel, but **no real data, region identifiers, model result figures or reverse-identifiable research settings are released**.
- Public runner is a standalone v0.2–v0.4 demonstration; wider v0.1 protocol steps (LM, SAR/SEM comparison, LR/Wald, etc.) are not silently claimed as auto-run features.

## v0.1.0 — 2026-09-26
首个公开预览版：中文研究协议，数据和 W 审计、Moran、非空间/空间模型选择、效应分解、稳健性与可视化的完整**方法流程说明**。

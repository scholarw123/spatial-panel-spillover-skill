# 输出规范

在 JSON 配置的 `output_dir` 下：

- `run_metadata.json`：配置、N/T、seed、置换次数、估计器与研究边界。
- `weights/*.csv`：W 每一行/列带 unit 标签，方便核对排序。
- `v02_weight_diagnostics.csv` / `v02_weight_sensitivity_sdm.csv` / `v02_normalization_sensitivity.csv` / `v02_economic_weight_metadata.json`。
- `v03_global_bivariate_moran.csv` / `v03_lisa_Y.csv` / `v03_lisa_summary.csv`。
- `v04_cumulative_thresholds.csv` / `v04_distance_rings.csv` / `v04_decay_sensitivity.csv` / `v04_identification_guard.txt`。
- `plots/*.png`：W 热图、邻居数、跨期 Moran、选定时期散点图、LISA 计数、阈值—邻居数—间接效应关联图；真实地图仅在边界有效时出现。

失败/跳过模型使用 `status` 和 `error` 明示；不可只输出成功或显著的规格。所有 p 值须注明随机化尾部、估计 SE 类型和是否做多重检验校正。

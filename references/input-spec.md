# 输入规范（v0.4.0）

1. `panel`：UTF-8 CSV 或 xlsx；一行一个 `unit × time`，必须平衡；列名通过 `columns` 映射，核心 `y/x` 和 controls 数值且有限，禁止重复及自动补值。
2. `coordinates`：UTF-8 CSV，列必须为 `unit,lat,lon`（十进制度，W 采用 haversine 公里距离）。`unit` 唯一且与面板 ID 集合完全一致；CSV 中 unit 出现顺序即 W 顺序。坐标可表示质心、行政中心等，但须在研究中说明选择及来源。
3. `columns`：`id, time, y, x, controls[]`，`economic_anchor` 可选，可与 controls 重合。
4. `output_dir`：输出路径，运行时创建；相对路径相对于配置文件本身。
5. `boundary_path` / `boundary_id_col` 可选：合法、可验证的 polygon GeoJSON/Shapefile/GPKG；需要 `geopandas`；必须完整匹配 ID、不允许重复。Shapefile 须提供完整 sidecar 文件，不能只上传 `.shp`。
6. `permutations` 至少 99（公开演示默认 199；正式探索一般 999 或更高），seed 固定并记录。W 是静态且全期共享；当前实现不是非平衡或 `W_t` 估计器。

参考 `../assets/config.example.json` 与 `../examples/synthetic_demo/config.json`。阈值公里数应根据研究领域/地理尺度预先指定，而不是随意复制演示数值。使用经济锚的 period mean 会利用样本全期信息，仅为描述性敏感性默认；正式研究建议配置预定基期并修改该计算逻辑，且披露经济 W 的内生性风险。

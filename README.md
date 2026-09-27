# Spatial Panel Spillover Analysis Skill（中文）

> **v0.4.0 public preview** · 通用空间面板研究协议 + v0.2–v0.4 可运行扩展。公开仓库只含人工生成的模拟案例，不包含任何未公开项目的数据或结果。

目标是将数据审计、空间 W 定义、ESDA、空间效应分解、距离敏感性与论文解释规范化，而不是调节设定来寻找显著性。请先阅读 [`SKILL.md`](SKILL.md)。

## 新增的功能

| 模块 | 公开可运行功能 |
| --- | --- |
| v0.2 空间 W | 距离倒数、KNN、距离带、经济相似（Gaussian/逆距离和 ε 敏感性）、经济×地理、可选真实边界 Queen/Rook；W 热图/邻居数/孤立单元/连通性；行/谱/对称/全局标准化对照 |
| v0.3 ESDA | Global 与双变量 Moran（置换检验）、条件随机化 LISA、Moran 散点图、LISA 跨期计数；合法边界文件下可绘制 LISA 地图 |
| v0.4 距离衰减 | 累计距离阈值、距离环、幂律/指数衰减、阈值—邻居密度—效应联动、边界声明护栏；按 W 特征值导出 rho 合法搜索区间 |

**方法协议 ≠ 自动 runner 的全部能力。** `SKILL.md` 还描述论文级非空间基准、LM、SAR/SEM/SDM 模型比较与 LR/Wald 约束检验；当前公开的 v0.4 扩展脚本只执行其实际实现的模块，并不声称自动完成上述所有主模型步骤、聚类稳健推断或因果识别。真实论文请与成熟计量软件交叉核验。

## 快速运行：全部使用模拟数据

Python 3.10+：

```bash
pip install -r requirements.txt
python scripts/smoke_test.py
# 或：
python scripts/run_spatial_panel.py examples/synthetic_demo/config.json
python -m unittest discover -s tests -v
```

在 `examples/synthetic_demo/outputs/` 中看到 W 矩阵、诊断 CSV、Moran / LISA CSV、距离敏感性 CSV、图形与识别警告。`generate_demo_data.py` 使用固定 seed 制造 12 个虚构地区×6年，**不是对真实研究数据的匿名改名/重抽样**。

## 替换为自己的合法数据

从 [`assets/config.example.json`](assets/config.example.json) 复制配置。面板 CSV（或 xlsx）至少包括 `unit,year,Y,X` 和控制变量；坐标 CSV 必须为 `unit,lat,lon`（W 顺序以坐标文件的 unit 行次序为准）；时间和地区不得重复，空间 ID 集合必须完全一致；面板必须平衡。示例 JSON 可配置 KNN、W 距离带、经济锚、累计阈值、rings、衰减函数、置换 seed。详细格式：[`references/input-spec.md`](references/input-spec.md)。

如果需 Queen/Rook 或 LISA 聚类地图，请自己提供来源/许可合规的 polygon 边界并安装 `geopandas`，指定 `boundary_path` 和 `boundary_id_col`；只给坐标绝不自动伪造省界。

> 公开版经过通用化与边界条件修正（包括真正的 Gaussian 经济核定义）；旧私有验证包中的经济 W 数值不应被当作公开 demo 的预期输出。

## 方法解释须知

- `WX` 系数不等于间接效应，SDM 要用空间乘数分解。
- 双变量 Moran 和 LISA 是空间相关性，不是因果溢出。
- 经济 W 中全期平均锚只是演示性、共同静态 W，不能自动宣称外生；必须论证选择经济距离的机制。
- 若阈值图出现孤立单元/网络不连通，runner 只记录 W 诊断，不会将其悄悄作为可比 SDM 结果。
- 不能按最低 p 值挑“最优距离”或按最后一个显著阈值宣称“最大半径”。
- 当前 SDM 结果以集中 Gaussian 似然和 Hessian/delta-method 计算，不代表稳健聚类 SE；需报告这一区别。

## 目录

```text
SKILL.md               研究协议 / 方法判断
README.md              使用说明
CHANGELOG.md           版本变更
ROADMAP.md             下一步路线图
requirements.txt       依赖
scripts/
  run_spatial_panel.py           统一入口
  run_spatial_extensions.py      v0.2–v0.4 核心
  smoke_test.py                  synthetic end-to-end test
tests/test_spatial_extensions.py 数学及边界单元测试
references/                       方法、输入、决策、输出及可视化说明
assets/config.example.json        通用配置示例
examples/synthetic_demo/          完全人工生成的公开演示
```

## GitHub 网页端更新与引用

本版本为已有仓库的**覆盖/新增文件包**，不包含原仓库无需修改的 `LICENSE`、`.gitignore`、`CONTRIBUTING.md`、`GITHUB_PUBLISHING.md`，上传时请保留原文件。逐步操作见包外/包内的 [`GITHUB_WEB_UPLOAD_GUIDE.md`](GITHUB_WEB_UPLOAD_GUIDE.md)。在通过仓库 Release 发布后，引用请指向对应固定 tag 的 URL；如后续配置 Zenodo DOI，可再补 `CITATION.cff`，不要编造 DOI。

## License

延续原仓库 MIT License，参阅根目录 [`LICENSE`](LICENSE)。欢迎 Issue/PR，建议提供可以公开的最小模拟复现而非未发表研究数据。

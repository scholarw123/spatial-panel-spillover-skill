# Spatial Panel Spillover Analysis Skill（中文版）

一个面向中文社会科学研究者的**空间面板数据与空间溢出效应分析 Skill**。

> 当前版本：`v0.1.0`（public preview）  
> 状态：可用于学习、复现、研究流程标准化；尚不是“覆盖所有空间计量方法”的完整工具箱。

## 它解决什么问题？

很多空间面板论文的研究主题会变，但分析流程高度重复：数据审计、空间权重矩阵、Moran's I、双向固定效应、LM/Robust LM、SAR/SEM/SDM、LR/Wald、空间效应分解、稳健性和可视化。

这个 Skill 的目标不是“替你自动找显著结果”，而是把一套可复用的研究协议固化下来，让 AI/研究者每次都按一致、可审计的流程工作。

## 当前支持

- 平衡地区×年份面板数据审计；
- 逆地理距离 W、逆距离带 W 的自动构造；
- 用户自带 W 矩阵（CSV）；
- 行标准化与孤立单元检查；
- Global Moran's I（置换检验）；
- pooled OLS / unit FE / TWFE；
- LM-Lag / LM-Error / Robust LM；
- SAR / SEM / SDM；
- SDM→SAR、SDM→SEM 的 LR/Wald 检验；
- Direct / Indirect / Total effects；
- 距离阈值敏感性；
- 自动生成基础论文级图形。

## 当前明确不支持 / 不自动完成

- 非平衡空间面板估计；
- Local Moran / LISA 的正式统计推断；
- 邻接矩阵的自动生成；
- 经济距离、经济—地理嵌套矩阵的自动生成（可通过 `matrix_csv` 输入）；
- 动态空间面板、System GMM、空间 DID、空间门槛模型；
- 自动因果识别；
- 无真实边界文件时生成行政区地图。

这些功能会在后续版本逐步补充，见 [`ROADMAP.md`](ROADMAP.md)。

## 最快上手

### 1. 安装 Python 依赖

建议 Python 3.10+。

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 跑通自带的模拟案例

```bash
python scripts/run_spatial_panel.py examples/synthetic_demo/config.json
```

也可以执行 smoke test：

```bash
python scripts/smoke_test.py
```

运行成功后，会在：

```text
examples/synthetic_demo/outputs/
```

生成描述统计、Moran's I、基准回归、LM 检验、空间模型比较、效应分解、距离阈值敏感性以及图形。

### 3. 换成你的数据

复制：

```text
assets/config.example.json
```

修改：

- `panel.id`
- `panel.time`
- `variables.y`
- `variables.x`
- `variables.controls`
- `weights`
- 数据路径

然后运行：

```bash
python scripts/run_spatial_panel.py your_config.json
```

## 在 ChatGPT / Agent 中怎么用？

这个仓库不仅有 Python runner，更重要的是根目录的 [`SKILL.md`](SKILL.md)。它把空间面板研究中的分析顺序、判断逻辑、禁止事项和输出规范写成了可复用 Skill。

典型使用方式：

> 请使用空间面板空间溢出效应分析 Skill 检查附件数据。Y 是 XXX，X 是 XXX，控制变量为 XXX，地区变量为 XXX，年份变量为 XXX。先做数据和 W 审计，再按 Skill 的 Gate 顺序执行分析，不要为了显著性调整模型。

Skill 负责的是“**这类问题应该怎么做**”；具体研究的 X、Y、控制变量、样本期和 W 仍由研究设计决定。

## 默认分析闭环

```text
研究设定
  ↓
数据审计
  ↓
W 审计
  ↓
描述统计 + 趋势图
  ↓
Moran's I
  ↓
非空间基准（FE/TWFE）
  ↓
LM / Robust LM
  ↓
SAR / SEM / SDM
  ↓
LR / Wald
  ↓
Direct / Indirect / Total effects
  ↓
空间 W / 距离阈值敏感性
  ↓
可视化 + 论文解释
```

## 研究诚信护栏

本 Skill 明确禁止：

- 为了显著性反复调整样本、W 或变量；
- 将 `W×X` 原始系数直接称为空间溢出效应；
- 只凭 AIC/BIC 机械选择最终模型；
- “A 组显著、B 组不显著”就宣布存在组间差异；
- 某项稳健性失败却写成“所有检验均稳健”；
- 用距离阈值敏感性直接宣称真实溢出在某公里处终止；
- 在没有真实地理边界数据时臆造地图。

## 仓库结构

```text
spatial-panel-spillover-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── requirements.txt
├── CHANGELOG.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── assets/
│   └── config.example.json
├── references/
│   ├── input-spec.md
│   ├── methodology.md
│   ├── decision-rules.md
│   ├── visualization.md
│   └── output-spec.md
├── scripts/
│   └── run_spatial_panel.py
└── examples/
    └── synthetic_demo/
        ├── README.md
        ├── generate_demo_data.py
        ├── panel.csv
        ├── coordinates.csv
        └── config.json
```

## 为什么案例是 synthetic data？

公开仓库不包含任何未公开项目的真实数据、变量名、题目、结果数值或可反向识别信息。示例数据由固定随机种子人工生成，只用于展示数据结构和验证 runner 是否能够正常执行。

## 版本定位

`v0.1.0` 是第一个公开预览版。当前 Skill 主要来自一套已经完整跑通的空间面板分析流程，以及通用空间计量原则的整理。它会继续迭代，不应被理解为“空间计量的最终标准答案”。

如果你发现模型实现、检验口径、空间权重构造或论文解释存在问题，欢迎提交 Issue 或 Pull Request。

## License

MIT License。见 [`LICENSE`](LICENSE)。

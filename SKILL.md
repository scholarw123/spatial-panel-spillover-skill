name: spatial-panel-spillover-analysis-zh
description: 面向地区×年份面板数据的中文空间计量研究协议，覆盖面板与空间权重审计、逆地理距离/Queen/Rook/KNN/距离带/经济和经济—地理嵌套 W、Moran/LISA、TWFE、SAR/SEM/SDM 的方法判断、空间效应分解以及距离衰减和边界声明审查。适用于可复现研究和空间计量结果诊断；不得为了显著性改变研究设定。
面板数据空间溢出效应实证分析 Skill · v0.4.0
本文件是研究执行协议，不是“运行就能识别因果效应”的自动回归宏。遵循：研究设定 → 数据审计 → W 审计 → 描述统计 → 空间探索 → 非空间基准 → LM/模型比较 → SDM 效应分解 → W/距离稳健性 → 异质性与机制 → 论文输出。若工具实现尚不覆盖某步，应如实标记为未执行，不能将建议步骤冒充自动估计结果。
0. 研究输入确认（必须先做）
识别空间 ID、时间列、因变量 Y、核心解释变量 X、控制变量、单位/变换、经济指标、地理坐标所代表的地理点、用户提供的边界文件许可和 W 的理论定义。说明固定效应、估计器、标准误、置换次数与 seed。不可擅自插补、缩尾、删样本、更换变量或替换 W。
公开 runner 使用 examples/synthetic_demo/config.json 同款 JSON 配置：panel、coordinates、columns.id/time/y/x/controls/economic_anchor、output_dir。具体见 references/input-spec.md。仅处理共同静态 W 的平衡面板。若变成动态 W_t、非平衡面板或跨期行政区划调整，应停止套用当前估计器。
Gate A：数据审计
核验 N×T、重复 ID×time、缺失、非有限值、各期覆盖、单位顺序、组内变异、量纲与对数处理。原始数据不允许静默补齐。
将坐标文件按 unit 显式重排。当前 runner 以坐标 CSV 的顺序作为 W 行列顺序，再以 (time, unit) 重排面板；绝不依赖 Excel/CSV 原始行次序碰巧一致。
对时间不变协变量引致的 FE 共线性要有解释，不可以用改变量顺序等技巧“修复”。
Gate B / v0.2：空间权重 W 审计与扩展
在回归前记录 W 的生成理由和元数据。允许候选：逆地理距离、距离带（二元/逆距离）、KNN（有向/union/intersection）、Queen/Rook 邻接、经济相似（Gaussian/逆距离）、地理×经济乘积嵌套，以及用户输入的合法 W。Queen/Rook 要求由用户提供有效、可用且地区 ID 完整匹配的真实 polygon 边界，不能从省会/质心坐标推测邻接关系。
每个 W 必须检查：N×N、对角为零、非负有限、ID 匹配、原始对称性、标准化方式、孤立单元、最少/平均/最多邻居数、网络连通分量、密度、谱半径，并输出 W 热图和邻居数分布；若有孤立单元或图不连通，不静默将其作为同质 SDM 效果与其他 W 并列比较，需记录且可以只做诊断。
经济 W 推荐预先理论指定且保持时间不变的经济锚（例如事前基期，不得用结果变量定义）；演示 runner 的 economic_anchor 采用全期平均，可能利用事后信息，仅适合描述性敏感性，不可据此宣称严格预定性或外生性。对于近零经济差异应事先声明 Gaussian 带宽 / 逆差稳定项 ε 并作 ε 敏感性。
标准化对比在同一个原始 W 上进行：row、spectral、symmetric、global sum=N。不能把不同尺度的原始 rho 或 WX 系数直接当作同一个效应量比较；使用同一效应定义的 Direct / Indirect / Total 对照。
W 首先服务于空间连接机制假设，而不是哪个矩阵带来更小 p 值。见 references/methodology.md。
Gate C：时序与分布
输出 N、均值、标准差、最小/最大、组内/组间变化；根据数据生成 X/Y 趋势和异常点诊断。数据期及区域分组必须与研究设计一致。趋势并非因果证据。
Gate D / v0.3：空间探索性分析
对每个年份分别计算 Y、X 的 Global Moran's I，明确 W、置换次数、seed、零假设与 p 值尾部；双变量 Moran X_i—(WY)_i 需要说明方向，与 Y_i—(WX)_i 不等价。
Local Moran / LISA 使用条件随机化；输出 unit/year/z/Wz/local_I/p_perm/HH/LL/HL/LH/NS。本 runner 的 LISA p 为双侧未作多重检验调整的 pseudo p，多个单元×年份检验应显式说明多重比较限制。没有真实边界仍可计算 Local I，但不得画行政区聚类地图。
Moran 散点图与跨期 LISA 计数属于探索性空间模式，不等于 SDM 间接效应、因果溢出或干预评估；全距离 W 的“局部”含义与邻接 W 不同。
Gate E–F：非空间基准、模型诊断与选择
理论框架应报告 pooled、unit FE、TWFE（必要时空间单元聚类稳健 SE），然后考虑 LM-Lag、LM-Error、Robust LM、SAR、SEM、SDM、LR/Wald 约束与 AIC/BIC。不能凭单个 p 值或 AIC 机械选择。若所用 runner 未提供上述估计步骤，输出明确标记“协议要求，当前扩展 runner 未自动执行”，不能虚构结果。
本版本公开 run_spatial_extensions.py 的 SDM 敏感性估计器采用双向去均值的集中 Gaussian 似然、数值 Hessian 和 delta method；仅为共同静态 W 的演示/复现方法，不替代成熟空间计量软件的全套诊断或稳健聚类推断。若需要正式主表，应对照成熟软件/库作交叉核验并清楚报告估计口径。
Gate G：空间效应分解
SDM 必须用 S(W)=(I−ρW)^{-1} 和 S(W)(βI+θW) 的均值对角、均值非对角行和、均值总行和给出 Direct / Indirect / Total；不能把 θ 或 WX 的原始系数直接叫“间接效应”。记录 rho 合法区间：本 runner依据 W 特征值导出搜索边界，不硬编码 (-0.95, 0.95)。数值处于边界附近必须告警。对标准误类型及假设充分披露。
Gate H / v0.4：距离衰减与边界
可执行：累计距离截断、互不重叠距离环 (a,b]、幂律 d^{-α}、指数 exp(-d/h)、阈值/邻居密度/间接效应联动。累计截断改变网络集合与行标准化权重；环形 W 可能孤立或不连通。保留每个阈值的网络诊断、回归状态、所用 W、系数/影响/推断。
识别边界检查（必需）：不能把最大系数/最低 p 值所对应的阈值称作“最优距离”；不能将最后一个显著累计阈值叫作“最大溢出半径”或断言越过它真实效应为零。孤立单元、断连、近边界 rho、预先指定阈值不足、多个规格筛选均应如实标记。相邻设定的影响估计不是独立样本。见 references/decision-rules.md。
输出与可复现性
至少记录 input/config、ID 顺序、W 定义和标准化、N/T、seed、置换次数、估计器、数值方法、合法边界、每一步状态/失败原因、图表。参照 references/output-spec.md 和 references/visualization.md。对失败 W 应保留诊断，不得悄悄跳过不利结果。
保密与公开案例
公开仓库中只能包含固定随机种子人工生成的 synthetic demo (R01…R12, Y/X/C1/C2)，不得放入真实研究题目、变量名、未发表数值、真实坐标清单、数据文件、原始 W 或可反向识别的阶段结果。研究数据的内部验证结果与 GitHub 发布包必须完全分开。任何第三方边界文件需确认来源、许可与行政区划时间匹配。
执行入口与功能边界
pip install -r requirements.txt
python scripts/smoke_test.py
python scripts/run_spatial_panel.py examples/synthetic_demo/config.json
python -m unittest discover -s tests -v
​
入口 run_spatial_panel.py 调用 run_spatial_extensions.py；当前自动生成 v0.2/v0.3/v0.4 的 W 诊断、ESDA、SDM 敏感性、距离环/衰减。并未自动完成本协议中描述的 pooled/FE/LM/SAR/SEM/LR/Wald 及正式因果识别；若需要完整论文主表，需另行复核。真实 Queen/Rook 和 LISA 地图需额外安装 geopandas 并提供有效边界文件。

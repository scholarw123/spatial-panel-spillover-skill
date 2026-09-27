# Synthetic demo（完全人工数据）

使用固定随机种子由 `generate_demo_data.py` 独立生成 12 个**虚构地区** `R01`…`R12`、6 年（72 条）的 Y/X/C1/C2 与简化地理坐标。数据中的数值、地区标识、坐标和系数均非对任何真实研究的匿名改名、采样或复制，不能作为论文实证结果。

```bash
python examples/synthetic_demo/generate_demo_data.py
python scripts/run_spatial_panel.py examples/synthetic_demo/config.json
```

输出进入本文件夹的 `outputs/`（Git 不收录生成数据）；测试时也可以运行 `python scripts/smoke_test.py`。`config.json` 中阈值/seed 只为模拟测试，切勿挪用为其他研究的先验设定。

# 只用 GitHub 网页更新当前仓库（不用 Desktop）

打开：https://github.com/scholarw123/spatial-panel-spillover-skill 。这份 ZIP 是**版本更新包**，不是完整仓库备份。现有 `LICENSE`、`.gitignore`、`CONTRIBUTING.md`、`GITHUB_PUBLISHING.md` 都不需要动，也不要删除。

## 1. 先在电脑解压

进入解压所得文件夹 `spatial-panel-spillover-skill-v0.4.0`，看到根目录的 `SKILL.md`、`README.md` 等文件和 `scripts`、`references` 等文件夹。**不要把 ZIP 本身上传，也不要把这个外层文件夹再套入 GitHub。**

## 2. 替换五个已有根目录文件

先更新 **`SKILL.md`、`README.md`、`CHANGELOG.md`、`ROADMAP.md`、`requirements.txt`**，一个一个做：

1. 电脑上用记事本打开更新包内对应同名文件，`Ctrl+A` → `Ctrl+C` 复制全文。
2. GitHub 仓库网页点击同名文件，例如 `SKILL.md`，点文件右上的铅笔 **Edit this file**。
3. 编辑器里 `Ctrl+A` → `Ctrl+V`，用新版内容完全替换旧内容（不要仅把全文追加在下面）。
4. 点击 **Commit changes…**，Commit message 可写 `Update SKILL for v0.4.0`；选 **Commit directly to the main branch**，再次点击 **Commit changes**。
5. 对剩余四个文件重复。网页版直接提交后不需要 Push。

这样处理最稳妥，不依赖 GitHub 上传页面是否接受覆盖同名文件。`ROADMAP.md` 之前虽然已经添加了进度说明，但这次新版还需要用同样方法替换。

## 3. 上传新的目录和文件

回仓库首页 → **Add file → Upload files**。在电脑的更新包里选择/拖入以下五个文件夹及说明文件（**是这些内容，不是它们的上一级文件夹**）：

- `scripts/`（3 个 Python 文件）
- `tests/`（1 个测试文件）
- `references/`（5 个 Markdown）
- `assets/`（1 个 JSON）
- `examples/`（synthetic_demo 下的 README、生成脚本、两份模拟 CSV 和配置 JSON）
- `GITHUB_WEB_UPLOAD_GUIDE.md`（可选，但方便下次更新）

GitHub 官方网页上传支持拖入文件或文件夹。如果浏览器不能拖文件夹，就先用 **Add file → Create new file** 输入带目录的文件名（例如 `scripts/run_spatial_extensions.py`），粘贴内容后提交；也可进入目录逐个 Upload files。

检查待上传列表：正确路径为 `scripts/run_spatial_extensions.py`、`examples/synthetic_demo/panel.csv` 等；**不要出现 `spatial-panel-spillover-skill-v0.4.0/scripts/...` 的多余外层目录**。提交信息：`Add v0.2-v0.4 generic runner, demo and tests`，点 Commit changes。

## 4. 回到仓库核对

首页 README 顶部应是 `v0.4.0`，并能看到 `scripts/`、`references/`、`assets/`、`examples/` 和 `tests/`。特别检查 `scripts/run_spatial_extensions.py`，以及 `examples/synthetic_demo/config.json` 是否在正确路径。

GitHub 网页上传本身**不会帮你执行 Python**；本包已在生成环境通过单元测试和端到端模拟案例，但上传后如需再验证，可在支持 Python 的环境里运行：

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/smoke_test.py
```

完成核对后才去 **Releases → Draft a new release**，创建 tag `v0.4.0`。在此之前不要误以为“代码跑通过”等于“代码已经进入 GitHub”。

## 公开数据警戒线

千万别把另一个**真实研究验证 ZIP**上传。这里只上传本更新包中的 `R01`…`R12`、`Y/X/C1/C2` 完全模拟案例，不上传任何未发表研究的真实 Excel、真实 W 或数值结果。

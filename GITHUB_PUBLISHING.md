# GitHub 发布指南

本文件针对第一次发布 GitHub 开源仓库的用户。

## 一、发布前检查

确认仓库公开版中没有：

- 未公开论文题目；
- 原始项目变量名；
- 未公开数据；
- 可反向识别项目的精确结果数值；
- API Key、密码、邮箱口令等秘密信息。

当前公开包的示例使用 synthetic data。

## 二、在 GitHub 网页新建仓库

1. 登录 GitHub；
2. 右上角 `+` → `New repository`；
3. Repository name 推荐：`spatial-panel-spillover-skill`；
4. Description 可写：`面向中文社会科学研究者的空间面板数据与空间溢出效应分析 Skill`；
5. 选择 `Public`；
6. **不要**在 GitHub 页面额外初始化 README、.gitignore 或 License，因为压缩包里已经有；
7. 点击 `Create repository`。

## 三、最简单的上传方式：网页 Upload files

解压 GitHub 发布 ZIP 后，进入最外层项目文件夹，确认你看到 `README.md`、`SKILL.md`、`LICENSE` 等。

在新建的空仓库页面：

1. 点击 `uploading an existing file` 或 `Add file` → `Upload files`；
2. 将项目文件和文件夹拖入上传区；
3. Commit message 填：`Initial public release v0.1.0`；
4. 点击 `Commit changes`。

注意：不要把“包含项目文件夹的上一层目录”再套一层上传，否则仓库首页会看不到 README。

正确：

```text
repo-root/
├── README.md
├── SKILL.md
├── LICENSE
└── ...
```

不推荐：

```text
repo-root/
└── spatial-panel-spillover-skill/
    ├── README.md
    └── ...
```

## 四、推荐的正式方式：Git 命令行

在解压后的项目根目录执行：

```bash
git init
git add .
git commit -m "Initial public release v0.1.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/spatial-panel-spillover-skill.git
git push -u origin main
```

把 `YOUR_USERNAME` 换成你的 GitHub 用户名。

## 五、发布第一个 Release

代码上传完成后：

1. 仓库首页右侧找到 `Releases`；
2. 点击 `Create a new release`；
3. Tag 填：`v0.1.0`；
4. Release title 填：`v0.1.0 - First public preview`；
5. Release notes 可写：

```text
首个公开预览版：
- 中文空间面板分析 Skill；
- 数据与 W 审计；
- Moran's I、TWFE、LM/Robust LM；
- SAR/SEM/SDM、LR/Wald；
- Direct/Indirect/Total effects；
- 距离阈值敏感性与基础可视化；
- synthetic demo，不包含未公开项目数据。
```

6. 将 GitHub 发布用 ZIP 作为 Release asset 上传；
7. 点击 `Publish release`。

## 六、仓库首页建议设置

### About

Description：

`面向中文社会科学研究者的空间面板数据与空间溢出效应分析 Skill`

Topics 建议：

- `spatial-econometrics`
- `panel-data`
- `spatial-panel`
- `spatial-durbin-model`
- `social-science`
- `research-workflow`
- `agent-skill`
- `chinese`

## 七、每次更新的版本习惯

建议采用语义化版本：

- `v0.1.0`：首个公开版；
- `v0.2.0`：新增一批功能；
- `v0.2.1`：修 Bug，不改变主要功能；
- `v1.0.0`：进入相对稳定版。

每次更新：

1. 修改代码与文档；
2. 更新 `CHANGELOG.md`；
3. 本地运行 `python scripts/smoke_test.py`；
4. commit + push；
5. 创建新的 GitHub Release；
6. 上传对应版本 ZIP。

## 八、CITATION.cff

当前 `v0.1.0` 暂未加入 `CITATION.cff`，可以在你确定公开署名、仓库地址和是否绑定 Zenodo 后再补充。

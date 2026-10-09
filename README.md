# 数学建模竞赛多 Agent 工作流

一套面向 Codex 的本地数学建模竞赛 Agent 框架，包含总控、备赛研究、建模求解和只读审阅角色，以及 12 个按任务选择的 Skill。通过文件协议串联问题分析、文献证据、模型选择、代码实验和论文素材，保留可复现的命令、产物与哈希。

仓库同时提供一个仅使用 Python 标准库的合成预测 demo，便于检查代码和任务协议。真正的模型调用由 Codex 宿主执行，Python 入口不会创建子 Agent。

## 角色与能力

| 角色 | 指令入口 | 职责 |
|---|---|---|
| Orchestrator | `AGENTS.md` | 按本次目标确定范围，派发任务、核验交接和汇总交付 |
| researcher | `prompts/researcher.md` | 备赛、文献与方法研究、知识卡和算法模板 |
| solver | `prompts/solver.md` | 根据已提供的赛题与附件建模、编程、实验和论文素材 |
| reviewer | `prompts/reviewer.md` | 只读核对模型、代码、实验与引用，返回证据和局限 |

九个通用 Skill：`problem-analysis`、`data-processing`、`literature-evidence`、`model-selection`、`mathematical-modeling`、`algorithm-implementation`、`experiment-analysis`、`visualization`、`paper-writing`。

三个条件 Skill：`eeg-c-task` 用于核实为 2026 C 题视觉认知 EEG 或同结构任务的场景；`independent-validation` 用于已有结果的独立复核；`submission-audit` 用于最终候选包和当届规则已齐备的交付审查。

局部修改、翻译和格式转换由当前 Agent 直接完成。完整备赛、完整解题或明确要求多 Agent 工作时，才使用角色调度和文件交接。`orchestration/routes.json` 是项目路由约定，Skill 清单由总控按条件选择。

## 快速开始

### 1. 下载项目

不熟悉 Git 时，可以直接 [下载最新源码 ZIP](https://github.com/fmyu78296-code/math-modeling-agent/archive/refs/heads/main.zip)，或在仓库页面选择 **Code → Download ZIP**。完整解压后进入 `math-modeling-agent-main` 文件夹。

已经安装 Git 时，在终端运行：

```powershell
git clone https://github.com/fmyu78296-code/math-modeling-agent.git
cd math-modeling-agent
```

两种方式获取相同的项目源码。打开的目录应直接包含 `AGENTS.md`、`README.md`、`tools/`、`.codex/` 和 `.agents/`；不需要把角色和 Skill 逐个复制到全局目录。下载与克隆操作可参考 [GitHub 官方下载说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives) 和 [克隆说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)。

### 2. 准备环境并打开项目

先确认 Python 版本：

```powershell
python --version
```

基础 demo 和离线测试需要 **Python 3.11 或更高版本**，无需安装第三方库。在部分 Windows 环境中，可用 `py -3.11` 替代下文的 `python`；macOS/Linux 常用 `python3`。使用能找到的、版本符合要求的 Python 命令即可。

在 Codex 中打开刚下载的项目根目录，按客户端提示信任项目并新建本地任务。保留 `.codex/` 与 `.agents/` 两个目录，角色和 Skill 是否被宿主实际加载按 [原生验收步骤](validation/CODEX_SMOKE_TEST.md) 检查。

只查看框架或运行离线 demo 时，不需要调用 Codex 模型；让角色研究、求解或审阅时，需要已配置并可正常使用的 Codex 环境。

### 3. 检查配置

仓库默认使用 **legacy 配置**，并附带两套配置快照。先保留默认配置；只有客户端兼容情况要求切换时再运行对应命令：

```powershell
python tools/config_mode.py current
# 使用旧式角色注册格式的客户端：
python tools/config_mode.py legacy
```

切换工具只修改项目内的配置，并把原配置备份到 `work/config-backups/`。`current` 与 `legacy` 是本项目的配置名称；各自字段以客户端兼容情况为准。历史格式核对见 `docs/OFFICIAL_CONFIG_REVIEW.md`。

### 4. 运行第一个 demo

在项目根目录的终端运行：

```powershell
python tools/project.py check
python -m unittest discover -s tests -v
python tools/project.py route --task templates/task.example.json
python tools/project.py demo --run-id first-demo
python tools/project.py validate --task competition/runs/first-demo/task.json --result competition/runs/first-demo/result.json
```

成功后会生成 `competition/runs/first-demo/`，其中包括：

| 文件 | 用途 |
|---|---|
| `task.json`、`result.json` | 任务要求、状态与产物哈希 |
| `metrics.json`、`predictions.csv` | 候选模型指标与最终预测 |
| `forecast.svg` | 合成数据与预测图 |
| `model.md`、`paper.md` | 模型说明与教学论文素材 |
| `provenance.json`、`run_log.txt` | 输入来源与运行记录 |

每次 demo 使用新的 `--run-id`，例如 `first-demo-02`，并在后续 `validate` 命令中使用相同编号。程序拒绝覆盖已有目录。仓库不附带既有运行结果。`route` 只检查任务路由，静态检查和离线 demo 的通过不代表原生角色调用已通过。

## 在 Codex 中使用

第一次打开项目，可以先发送：

> 请读取本项目 AGENTS.md，简要说明总控和三个专业角色的职责，检查实际可用的角色及项目 Skill，并告诉我下一步如何开始。暂不进行完整赛题求解。

确认角色和 Skill 可用后，再根据目标选择下面的提示词。描述清楚输入文件、希望完成的范围与期望产物；正式建模时可补充截止时间和计算资源。

备赛示例：

> 按 AGENTS.md 担任总控，派 researcher 阅读完整角色指令，围绕预测与优化建立有限的备赛任务。核验来源和适用条件，实际验证代码后再合入知识库。

完整解题示例：

> 先核对 competition/input/ 中的题目、全部附件、字段解释与当届规则，列出缺失材料和各问要求。输入齐备后再为 solver 创建独占任务目录。先做问题分析和文献证据核验，再建立基线与主模型。完成后派 reviewer 检查结果、代码和引用的一致性，汇总真实运行命令与局限。

局部任务示例：

> 将指定的论文文件转换为 LaTeX，保持内容、公式和图表对应，只检查本次转换受影响的部分。

三个专业角色的完整提示词保存在 `prompts/`，角色配置要求子 Agent 自行读取。总控最多并发派发三个子 Agent，子 Agent 不递归委派。宿主不可用时要明确记录失败或回退。

## 目录结构

```text
math-modeling-agent/
├── AGENTS.md                 # 总控范围、调度与科学要求
├── .codex/                   # 三角色配置
├── .agents/skills/           # 12 个 Skill 与相关指南
├── prompts/                  # 完整角色提示词
├── orchestration/            # 路由与 task/result 协议校验
├── algorithms/               # 可运行基线算法
├── competition/
│   ├── demo/                 # 合成题、数据、参数与管线
│   ├── input/                # 用户本地的正式输入
│   └── runs/                 # solver 独占运行目录
├── knowledge/                # 方法指南、教学知识卡与 researcher 输出
├── refs/                     # 用户自建文献索引与本地原文
├── templates/                # 任务、文献、实验和论文模板
├── tools/                    # 检查、demo、配置切换与文献去重
├── tests/                    # 离线自动测试和合成文献测试
├── validation/               # Schema、原生验收步骤与上传版实测报告
├── compat/                   # current / legacy 配置快照
└── docs/                     # 架构、协议与模块映射说明
```

## 文献与真实输入

把题目、附件、字段解释和赛事规则放在 `competition/input/`，保留原始文件。文献资料按 `refs/README.md` 建立 `catalog.csv` 和 `file_hashes.json`；上传版索引初始为空。C/D 的已有私有论文、题目附件和小组整理材料不随上传版发布。

`tools/reference_bridge.py` 用于文件哈希校验、书目匹配和稳定来源 ID 合并，主张是否被原文支持仍需核验。新的检索产物保存在独占任务目录，按 `templates/literature-evidence.md` 记录定位、适用条件与冲突。

论文写作的内容框架与配图指南在 `paper-writing`、`visualization` Skill 中。约 30 页是可调整的写作目标，实际格式和工具使用以当届规则和用户授权为准。

处理真实赛题需要第三方库时，可在项目内创建环境，再安装实际需要的依赖。以下为 Windows PowerShell 示例：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
```

后续用 `.venv\Scripts\python.exe` 运行相关代码。这个依赖文件只是可选建议，不是所有模型的完整依赖清单或锁定环境；根据题目和代码补充依赖并记录实际版本。

`.gitignore` 默认排除正式输入、独占运行目录、文献原文子目录和本地环境。文献索引的三个根目录文件允许提交，填写个人索引后需按自己的分享范围检查。

## 常见问题

| 问题 | 处理方式 |
|---|---|
| `python` 找不到，或提示缺少 `tomllib` | 检查 Python 是否安装并可在终端找到；`tomllib` 需要 Python 3.11 或更高版本。 |
| Codex 没发现角色或 Skill | 确认打开的是含 `AGENTS.md` 的根目录，点目录完整，项目已被客户端信任；按原生验收步骤检查发现与配置兼容情况。 |
| 配置字段不被客户端识别 | 按客户端实际支持的格式选择 `legacy` 或 `current`，切换后重新打开项目或会话检查。 |
| demo 提示运行目录已存在 | 改用新的 `--run-id`，同步修改 `validate` 命令中的目录名。 |
| 文献 `seed` 提示没有本地来源 | 仓库初始索引为空，先按 `refs/README.md` 登记真实来源与文件哈希。 |
| 已看到角色名称，是否代表已调用成功 | 以真实创建、执行和返回事件为依据；仅列出名字或离线路由不足以证明实际调用。 |

## 获取更新

通过 Git 克隆的项目，在本地修改已提交或妥善保存后，可运行：

```powershell
git pull --ff-only
```

通过 ZIP 下载的项目，可重新下载最新源码，先解压到新目录，再按需要迁移自己的输入、文献和运行结果。框架的离线验证范围见 [实测报告](validation/TEST_REPORT.md)，任务与结果格式见 [文件协议](docs/protocol.md)。

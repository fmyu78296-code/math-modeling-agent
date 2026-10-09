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

基础 demo 和离线测试需要 Python 3.11 或更高版本，无需安装第三方库。需要处理真实赛题时，再按实际模型选择安装 `requirements-optional.txt` 中的依赖。

下载或克隆仓库后，在 Codex 中打开包含 `AGENTS.md` 的项目根目录；确认 `.codex/` 与 `.agents/` 两个目录完整。角色和 Skill 是否被宿主实际加载，按 `validation/CODEX_SMOKE_TEST.md` 验收。

上传版保留原项目已使用的 **legacy 配置**，并附带两套配置快照。需要切换时运行：

```powershell
python tools/config_mode.py current
# 使用旧式角色注册格式的客户端：
python tools/config_mode.py legacy
```

切换工具只修改项目内的配置，并把原配置备份到 `work/config-backups/`。`current` 与 `legacy` 是本项目的配置名称；各自字段以客户端兼容情况为准。历史格式核对见 `docs/OFFICIAL_CONFIG_REVIEW.md`。

在项目根运行离线检查和示例：

```powershell
python tools/project.py check
python -m unittest discover -s tests -v
python tools/project.py route --task templates/task.example.json
python tools/project.py demo --run-id first-demo
python tools/project.py validate --task competition/runs/first-demo/task.json --result competition/runs/first-demo/result.json
```

每次 demo 使用新的 `--run-id`，程序拒绝覆盖已有目录。上传版不附带既有运行结果。`route` 只检查任务路由，静态检查和离线 demo 的通过不代表原生角色调用已通过。

## 在 Codex 中使用

备赛示例：

> 按 AGENTS.md 担任总控，派 researcher 阅读完整角色指令，围绕预测与优化建立有限的备赛任务。核验来源和适用条件，实际验证代码后再合入知识库。

完整解题示例：

> 先核对 competition/input/ 中的题目、附件与规则，再为 solver 创建独占任务目录。先做问题分析和文献证据核验，再建立基线与主模型。完成后派 reviewer 检查结果、代码和引用的一致性，汇总真实运行命令与局限。

局部任务示例：

> 将指定的论文文件转换为 LaTeX，保持内容、公式和图表对应，只检查本次转换受影响的部分。

三个专业角色的完整提示词保存在 `prompts/`，角色配置要求子 Agent 自行读取。总控最多并发派发三个子 Agent，子 Agent 不递归委派。宿主不可用时要明确记录失败或回退。

## 目录结构

```text
cumcm-multi-agent/
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
└── docs/                     # 架构、协议、模块映射与 GitHub 上传说明
```

## 文献与真实输入

把题目、附件、字段解释和赛事规则放在 `competition/input/`，保留原始文件。文献资料按 `refs/README.md` 建立 `catalog.csv` 和 `file_hashes.json`；上传版索引初始为空。C/D 的已有私有论文、题目附件和小组整理材料不随上传版发布。

`tools/reference_bridge.py` 用于文件哈希校验、书目匹配和稳定来源 ID 合并，主张是否被原文支持仍需核验。新的检索产物保存在独占任务目录，按 `templates/literature-evidence.md` 记录定位、适用条件与冲突。

论文写作的内容框架与配图指南在 `paper-writing`、`visualization` Skill 中。约 30 页是可调整的写作目标，实际格式和工具使用以当届规则和用户授权为准。

## GitHub 上传版说明

此目录是从本地工作区整理出的独立副本。保留 Agent 框架、教学知识卡、代码和模板；正式赛题、私有文献、历史实验与论文、虚拟环境、缓存、本机设置和旧日志未打入上传包。文献工具测试使用明确标为合成的夹具，下载后可独立运行。

`.gitignore` 排除本地数据、运行结果和环境文件；`.gitattributes` 统一文本换行。文件清单与哈希见 `MANIFEST.sha256.json`，本次运行结果见 `validation/TEST_REPORT.md`。

上传步骤见 [docs/GITHUB_UPLOAD.md](docs/GITHUB_UPLOAD.md)。仓库所有者可按自己的发布计划添加 `LICENSE`。

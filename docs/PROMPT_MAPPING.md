# 指令与模块映射

总控从 `AGENTS.md` 判断本次任务范围；专业角色按 `.codex/agents/` 中的指令读取 `prompts/` 的完整提示词。十二个 Skill 是按需读取的阶段指令文件，由总控和角色根据任务证据选择。

| 阶段 | Skill 或文件 | 主要产物 |
|---|---|---|
| 任务范围与调度 | AGENTS.md、docs/protocol.md | 独占任务、依赖、验收条件、结果 |
| 赛题分析 | problem-analysis | 子问题、变量、依赖与假设 |
| 数据处理 | data-processing | 数据字典、清洗日志、处理代码 |
| 文献证据 | literature-evidence | 来源索引、原文定位、主张与适用性记录 |
| 模型选择 | model-selection | 候选比较、基线与验证计划 |
| 数学化 | mathematical-modeling | 变量、推导、目标与约束 |
| 算法实现 | algorithm-implementation | 可运行程序、参数与日志 |
| 实验分析 | experiment-analysis | 指标、敏感性、稳健性与解释 |
| 图表 | visualization | 图、源数据、导出与版面检查 |
| 论文 | paper-writing | 有证据的章节和结论对应表 |
| 条件：视觉认知 EEG | eeg-c-task | 原始通道、事件与试次契约检查 |
| 条件：独立复核 | independent-validation | 复现证据、发现与局限 |
| 条件：最终候选包 | submission-audit | 当届规则对应与交付审查 |

研究输出由总控验收后列入 solver 输入；reviewer 只读返回，总控保存报告。局部编辑与格式转换按 AGENTS.md 的范围规则直接执行。

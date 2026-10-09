# 原生 Codex 验收（用户环境）
会消耗模型额度；离线测试不能替代。
0. 如使用已测 CLI 0.133.0，先运行 python tools/config_mode.py legacy；支持新规范的版本可保留 current。
1. 从含 AGENTS.md 的项目根打开 Codex，信任项目并记录版本、模型和权限。
2. 请求列出实际可用 researcher、solver、reviewer 以及十二个项目 Skill 路径，不可用则明确报告。区分 Codex 原生发现与 routes.json 静态声明。
3. 输入“使用 $problem-analysis 分析 competition/demo/problem.md”，核对读取了本项目 SKILL.md。再请求说明 $literature-evidence 的路径和所需产物；仅列文件不能证明实际执行了检索。
4. 请求原生 researcher 阅读 knowledge/cards/linear-trend.md 返回适用边界，同时原生 reviewer 只读对照 algorithms/linear.py；等待真实返回，保留调用事件。
5. 派原生 solver 读取完整 prompts/solver.md 并运行 python tools/project.py demo --run-id codex-demo，核验结果和实际 Skill 读取情况。
6. 保存 spawn/等待/返回事件和角色标识到 validation/runs/，不以口头宣称调用成功作证据。
7. 让 researcher 对一条可访问的原始文献做小范围检索，核对 references.csv、claim_source_map.csv、model_transfer.md 与可读原文一致；让 reviewer 只读核查一条论文引用。另对 C 题只执行 eeg-c-task 的小范围数据契约核查，记录真实通道和事件；已有结果时再让 reviewer 做一次 independent-validation。仅在有最终候选包和当届规则时执行 submission-audit。保存实际调用及访问记录，未执行的环节标记未验证。缺附件任务应 blocked；重开项目检查发现持续有效。
8. 旧版不支持时升级，或完整 prompt 传通用 Agent 并标记回退。
9. 文献衔接验收：先按 refs/README.md 建立真实本地索引，再在独占的新 C 题任务目录执行 `python tools/reference_bridge.py seed --topic C --out competition/runs/<task_id>/references.csv`，核对实际登记的本地 ID；将一条新检索结果存成同格式 CSV，再执行 `merge` 并审阅 reference_reconciliation.md。上传版初始索引为空，未补资料时应报告输入未就绪。工具去重不能替代文献主张核验。
此文件是待执行验收步骤，不是通过报告。

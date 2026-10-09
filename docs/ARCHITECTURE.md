# 架构
完整备赛或解题流程：用户 → Orchestrator（AGENTS.md）→ researcher → 文献证据与已核验知识 → Orchestrator → solver → 按阶段选择相关 Skill（C 题按需增加 eeg-c-task）→ 实验/图表/论文素材 → reviewer 按需执行独立复核与提交审查 → 总控交付。

局部编辑、格式转换等明确任务：用户 → 当前 Agent 完成指定产物 → 一次相关检查 → 交付。不为了使用多 Agent 架构而启动研究、建模、完整验收或提交审查。完整流程和轻量流程的判断规则见 AGENTS.md。

第一层、第二层是职责分工，不要求 researcher 创建 solver。跨角色信息由总控转交；文献产物须验收后作为下游任务输入。routes.json 的 conditional_skills 是供总控按 when 判断的条件路由，不是自动分类器。独立任务可并行，有上下游依赖则等待。Skill 不会自行启动 Agent。
离线程序共用路由和协议，只证明文件、路径和示例代码联通；不证明真实模型调用或 Skill 选择。

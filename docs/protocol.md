# 任务和结果协议 v1
这是本项目文件协议，不是 Codex 官方 API。routes.json 需要总控主动读取，不会自动调度模型。本协议适用于总控显式创建的 prepare/solve/review 子任务；用户要求的局部编辑、格式转换等直接任务按 AGENTS.md 的轻量规则执行，不必虚构 task.json、result.json、哈希交接或子 Agent 调用。

Task 字段：schema_version=1、task_id、mode、inputs、depends_on、output_dir、acceptance、budget_minutes。
task_id 仅字母数字、下划线、短横线。mode 为 prepare/solve/review。inputs 是现存文件相对路径；depends_on 是 completed 任务 id；acceptance 为非空验收条件列表；budget_minutes 为正整数。
output_dir 必须对应 knowledge/runs/<task_id>、competition/runs/<task_id>、validation/runs/<task_id>。
路径统一 /，拒绝绝对路径、反斜线、..、盘符及解析后逃出项目的符号链接。
JSON Schema 在 validation/schemas/；校验器是本项目专用，不是通用 JSON Schema 实现。

Result 字段：schema_version、task_id、agent、status、summary、artifacts、commands、limitations。
agent 与路由一致；status 为 completed/partial/blocked/failed。
artifacts 项包含 path 和 sha256，文件必须在任务输出目录，哈希为真实 SHA256。result.json 不给自身算哈希。
commands 仅记录真实执行命令；completed 需产物，其他状态需说明局限。
reviewer 只读返回结构化内容，由总控保存报告、计算哈希和落盘。

总控维护 queued → running → completed/partial/blocked/failed。任务输入不可变，重跑用新 id，不覆盖已有目录。
依赖只消费 completed；partial 需拆出明确可验收的新任务。校验通过后总控仍须审阅科学意义和 acceptance。
示例：先 demo，再 python tools/project.py validate --task templates/task.example.json --result competition/runs/demo/result.json。

blocked 结果允许输入或依赖尚未就绪，但仍检查字段、路径边界、任务归属和已有产物哈希；不能借 blocked 绕过路径限制。

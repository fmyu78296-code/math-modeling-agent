# 官方配置历史核对（2026-09-22）
以下保存原项目在该日期的配置核对记录，不是当前客户端的兼容性保证。上传副本使用 legacy 配置；本次离线检查范围见 validation/TEST_REPORT.md。
| 配置 | 采用方式 | 官方依据 |
|---|---|---|
| 总控 | 根 AGENTS.md | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |
| Agent | 独立 .codex/agents/*.toml，name、description、developer_instructions | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) |
| 并发 | agents.enabled、max_concurrent_threads_per_session | [配置参考](https://learn.chatgpt.com/docs/config-file/config-reference) |
| Skill | .agents/skills/<name>/SKILL.md 的 name/description | [Build skills](https://learn.chatgpt.com/docs/build-skills) |
| 生效 | 信任项目后加载 .codex/config.toml | [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic) |

不使用虚构的 prompt_file、include、handoffs 字段。长指令由 developer_instructions 要求 Agent 读取。
不固定账号未必可用的模型或修改全局配置。两套角色配置保存在兼容层中，每次只启用其中一套。
本地配置不等于云端 Work 已安装，旧客户端和云端需要各自验收。AGENTS.md 不是常驻服务。
父会话权限可能影响子会话；reviewer 的只读设置不能用来宣称独立权限隔离。

## 安装版兼容实测
原项目测试的 CLI 0.133.0 不识别 agents.enabled；当时文档格式与安装版存在差异。兼容层用 max_threads 及 agents.<name>.config_file。两套快照分别保存于 compat/current 和 compat/legacy，上传副本默认启用 legacy。项目自动加载和原生角色执行仍需在使用者的客户端中验证。

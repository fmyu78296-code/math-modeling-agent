# 旧版 CLI 兼容层
本机 codex-cli 0.133.0 将 agents.enabled 当作角色并报错：invalid type: boolean true, expected struct AgentRoleToml。
这是原项目在 2026-09-22 记录的兼容差异。上传副本默认启用 legacy；本目录使用旧式 agents.<name>.config_file 注册角色，两套配置可通过切换工具选择。
从项目根执行 python tools/config_mode.py legacy，将当前 .codex/config.toml 和三个角色文件备份到 work/config-backups/ 后切换。
恢复当前官方格式：python tools/config_mode.py current。
不修改 ~/.codex，不设置项目全局信任。仍须在用户客户端信任项目、重开会话并执行原生验收。
legacy/max_threads 的具体并发计数以该版本为准；总控仍限制最多三个子 Agent。

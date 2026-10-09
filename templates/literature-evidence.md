# 文献证据产物模板

在当前任务 `output_dir` 下创建下列文件。先核对 refs/catalog.csv：已有来源沿用 C01–C05、D01–D10、D05B 的 source_id；新来源使用新的稳定 ID，按 refs/README.md 与本地记录去重。来源 ID 在四个文件及论文中保持一致；一项主张对应多篇文献时，在映射表中分多行。CSV 用 UTF-8 保存，含逗号或换行的字段按 CSV 规则加引号。

## search_log.md

逐条记录日期、平台/站点、精确检索式、筛选或排除理由、实际打开的 URL/DOI、可读范围以及检索受限情形。未联网或只检索本地资料时明确写出。

## references.csv

表头：`source_id,title,authors,year,venue,doi,url,accessed_at,access_level,verification_status,notes`

`access_level` 使用 `full_text`、`abstract`、`metadata`、`unavailable` 之一；`verification_status` 使用 `verified`、`partially_verified`、`unverified` 之一。refs/catalog.csv 的 `partially_verified` 只表示文件和部分元数据已核对，不表示主张已核验。未知字段留空并在 `notes` 说明，不能猜测。后续搜索结果可保存为 `codex_found.csv`，再用 tools/reference_bridge.py 合并，保留冲突报告。

## claim_source_map.csv

表头：`claim_id,claim_text,source_id,locator,source_support,scope_limit,usage,verification_status`

`locator` 写页码、章节、公式号或网页小节；`usage` 说明用于背景、公式、参数、算法选择还是评价。不能定位的主张不得作为已核验依据。

## model_transfer.md

按子问题和候选模型记录：文献模型的输入输出、变量和单位、核心假设、公式及原始适用范围；本题数据和约束对应关系；需要修改或重新估计的部分；验证计划；最终采用或放弃理由。把文献作者的结果与本项目的实验结果分别标记。

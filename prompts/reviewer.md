# reviewer
按任务阅读 .agents/skills/literature-evidence/SKILL.md；需要独立结果复核时读 .agents/skills/independent-validation/SKILL.md，已有最终候选包且需要提交前审查时读 .agents/skills/submission-audit/SKILL.md。只读核对逐问覆盖、量纲、公式代码对应、泄漏、基线公平性、测试隔离、优化可行性、最优性声明、指标和图表来源。核对论文主张与 claim_source_map.csv、references.csv、refs/catalog.csv、合并冲突报告、原始文献可读范围和模型迁移条件是否一致；缺链接、定位、全文访问或外推依据时明确标出。
每个发现包含路径、证据、影响、复现与修复建议。需写文件的复现实验交总控派独立任务。无发现只表示检查范围内未发现，不能保证全局正确。返回检查范围和未测试项，由总控保存。

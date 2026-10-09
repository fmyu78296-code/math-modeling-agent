# 本地文献与来源索引

上传版只提供空索引，不附带任何用户文献原文。请将自己的原文保存在本目录的子目录，使用稳定 `source_id` 在 `catalog.csv` 登记，并在 `file_hashes.json` 记录每个文件相对项目根的路径与 SHA256。

`catalog.csv` 已包含所需表头。`topic` 使用 `C` 或 `D`，其余字段按本地资料如实填写；未核验的资料标为 `unverified`，部分核验标为 `partially_verified`。`local_file`、`local_text` 使用项目根相对路径，例如 `refs/C_EEG/source01.pdf`。书目和文件匹配不代表论文主张已经核验。

哈希清单格式如下，示例占位值需要替换为实际哈希：

```json
{
  "refs/C_EEG/source01.pdf": "填写该文件的实际 SHA256"
}
```

本地可用 `Get-FileHash -Algorithm SHA256 -LiteralPath 'refs/C_EEG/source01.pdf'` 获取真实哈希。文件和索引必须对应；原文缺失或哈希变化会被工具拒绝。

## 与新检索衔接

先创建独占任务目录并完成本地索引，再运行：

```powershell
python tools/reference_bridge.py seed --topic C --out competition/runs/TASK_ID/references.csv
python tools/reference_bridge.py merge --topic C --incoming competition/runs/TASK_ID/codex_found.csv --out competition/runs/TASK_ID/references_merged.csv --report competition/runs/TASK_ID/reference_reconciliation.md
```

将 `TASK_ID` 替换为已创建的任务编号，D 题使用 `--topic D`。输出文件必须尚不存在。空索引运行 `seed` 会提示缺少来源，这是输入就绪检查；不会自动检索或生成论文。

新资料字段与 `templates/literature-evidence.md` 一致。记录实际搜索查询、访问页面和日期；对真正采用的主张补充原文页码、章节、适用条件和本题实测证据。小组整理稿可作为线索，但不能替代原始资料。

`.gitignore` 排除本目录的原文子目录。根目录三个说明/索引文件允许提交；加入个人索引后，按自己的发布范围检查再提交。

`tests/test_reference_bridge.py` 使用临时目录中的合成书目与文本测试去重和哈希逻辑；其中的来源与 DOI 都是测试占位数据。

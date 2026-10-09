# GitHub 上传副本实测

日期：2026-10-09。环境：Windows、Python 3.11.5。

## 实际执行

| 命令 | 结果 |
|---|---|
| `python -B tools/project.py check` | passed；legacy、3 个路由、12 个 Skill |
| `python -B -m unittest discover -s tests -v` | 38 项；37 通过、1 跳过、0 失败 |
| `python -B tools/project.py demo --run-id github-package-check-001` | passed；选择 linear |
| `python -B tools/project.py validate --task competition/runs/github-package-check-001/task.json --result competition/runs/github-package-check-001/result.json` | passed |

跳过项为 Windows 环境禁止非特权创建符号链接的路径逃逸测试。测试输出明确记录了该原因。

合成 demo 测试集 MAE 为 `0.6828985507246372`，RMSE 为 `0.8174745563524017`。这是合成教学数据的离线程序结果。

## 上传副本改动

- 保留原框架的三个专业角色、12 个 Skill、路由、协议、基线代码和模板。
- 更新公开 README、目录说明、GitHub 上传步骤、换行与忽略规则；移除会话编号和依赖私有原文的文档表述。
- 文献索引保留字段表头，哈希清单初始为空；用户原文与小组整理材料不包含在公开副本中。
- `tests/test_reference_bridge.py` 改为临时目录中的合成书目和文本，覆盖文件校验、DOI 别名匹配、冲突提示与文件篡改拦截；不要求任何私人论文文件。
- 原项目算法、demo、协议和角色提示词未因打包改写。此前历史联调记录不作为本次副本的通过证据。

本次 demo 产物移到上传目录外保存；公开源码目录保持无历史运行状态。发布清单的 SHA256 覆盖除清单自身外的公开文件。

## 范围与未验证项

这次检查针对上传副本的离线可运行性与文件范围。没有重新调用原生专业角色、开展正式题目求解、访问文献网页或验证比赛论文和成绩。使用者应按 `CODEX_SMOKE_TEST.md` 在自己的 Codex 客户端检查角色与 Skill 加载。

可选第三方依赖、MATLAB、GPU、商用求解器以及 Linux/macOS 未在此次检查中运行。

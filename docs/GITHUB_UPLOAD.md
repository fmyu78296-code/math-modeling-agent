# 上传 GitHub

请从这一份整理后的 `cumcm-multi-agent` 目录上传。原工作目录包含赛题附件、环境和历史产物，两个目录的内容不同。

## 使用 Git 提交

在 GitHub 创建目标仓库，复制其仓库地址。创建空仓库后，在本目录执行：

```powershell
git init -b main
git add .
git status --short
git commit -m "Initial release of math modeling agent workflow"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

将 `YOUR_USERNAME` 和 `YOUR_REPOSITORY` 替换为自己的账号与仓库名。提交前的 `git status` 应包含 `.agents/skills/`、`.codex/`、`AGENTS.md`、README、代码和模板。原工作区的赛题、文献与历史运行不在这一副本中。

如果使用其他上传方式，也要确保以点开头的 `.agents/`、`.codex/`、`.gitignore`、`.gitattributes` 一并上传，并把本目录内容作为仓库根目录。

## 上传版验证

```powershell
python tools/project.py check
python -m unittest discover -s tests -v
python tools/project.py demo --run-id upload-demo
python tools/project.py validate --task competition/runs/upload-demo/task.json --result competition/runs/upload-demo/result.json
```

已有同名运行时换一个 `--run-id`。运行目录被 Git 忽略，生成实验后仍可在本地使用。

## 公开范围

这一版包含三种专业角色、12 个 Skill、方法说明、任务模板、基线算法、合成 demo 和离线测试。它不包含用户的正式赛题、实际论文、比赛运行产物、原文文献或本机环境。文献索引需要用户按 `refs/README.md` 在本地初始化。

`validation/TEST_REPORT.md` 只记录这一上传副本的检查。原生角色发现、真实模型求解和赛事成绩，应分别提供对应证据。

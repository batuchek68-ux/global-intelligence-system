# International Trade AI Operating System

这是一个能在 GitHub Actions 上运行的国际工程贸易云端操作系统工程实现，不是蓝图。

系统目标：

- 国际工程贸易项目推进：读取项目材料，生成风险判断、下一步动作和请示事项。
- 科研与情报：生成每日情报简报，支持无密钥离线模式和有密钥搜索模式。
- 视频内容：把项目与情报转成短视频脚本和可编辑分镜。
- 微信/企业微信推进：把需要人工批准的事项写入 outbox；配置 webhook 后可推送。
- 学习闭环：每次运行记录到 `memory/`，供后续复盘、迭代和自动化继续使用。

## 本地运行

```powershell
cd C:\Users\Surface\Documents\智慧情报分析平台\02_源代码\international-trade-ai
python workflows\preflight_check.py
python workflows\daily_job.py
```

运行结果会写入：

- `memory/last_run.json`
- `memory/cases/*.json`
- `memory/execution_logs/*.json`
- `research/briefs/*.md`
- `media/drafts/*.md`
- `comm/outbox/*.json`
- `reports/headquarters_status.md`
- `reports/owner_inbox.md`
- `reports/watchdog_status.md`

## GitHub 运行

1. 把 `international-trade-ai` 文件夹上传为 GitHub 仓库。
2. 在 GitHub 仓库设置 Secrets：
   - `OPENAI_API_KEY` 可选，用于后续接入真实模型。
   - `BING_SEARCH_KEY` 可选，用于真实 Web 搜索。
   - `WECHAT_WEBHOOK_URL` 可选，用于企业微信机器人推送。
3. 打开 Actions，手动运行 **International Trade AI Ops**，或等待每日定时任务。
4. 手动运行 **GitHub Cloud Acceptance**，确认云端总部验收报告通过。

也可以先生成发布包：

```powershell
python workflows\prepare_release.py
```

生成结果：

- `dist/international-trade-ai.zip`
- `dist/release_manifest.json`

没有任何密钥时，系统仍会在离线模式跑完整流程，生成可审阅的草稿、请示和运行记录。

GitHub Actions 每次运行前会执行：

```text
python workflows/preflight_check.py
python workflows/ensure_labels.py
```

`preflight_check.py` 会检查 workflow、权限、重大事项回复入口、总部报告、目录结构和说明文档是否齐全。`ensure_labels.py` 会准备 GitHub Issue 标签：`major-matter`、`owner-decision`、`autonomous`。

另有 **24h Codex Watchdog**：

```text
.github/workflows/watchdog.yml
```

它每 6 小时检查一次总部状态是否新鲜、是否有待你决策的重大事项，并生成 `reports/watchdog_status.md`。

另有 **GitHub Cloud Acceptance**：

```text
.github/workflows/cloud_acceptance.yml
```

它会在 GitHub 上一次性运行预检、测试、每日主循环、watchdog 和云端验收脚本，并生成 `reports/cloud_acceptance.md`、`reports/cloud_acceptance.json`，用于证明当前仓库具备“GitHub 云端 AI 总部”的运行闭环。

如果本机没有 `git` 或 GitHub CLI，也可以用标准库脚本触发云端验收：

先做只读连接体检：

```powershell
$env:GITHUB_TOKEN = "你的 GitHub token"
$env:GITHUB_REPOSITORY = "owner/repository"
python workflows\cloud_connection_check.py
```

体检结果会写入：

```text
reports/cloud_connection_check.json
```

然后触发云端验收：

```powershell
$env:GITHUB_TOKEN = "你的 GitHub token"
$env:GITHUB_REPOSITORY = "owner/repository"
python workflows\trigger_cloud_acceptance.py --ref main
```

运行结果会写入：

```text
reports/cloud_acceptance_remote.json
```

如果仓库还没有上传代码，也可以不安装 `git`/`gh`，直接通过 GitHub API 上传并触发验收：

```powershell
$env:GITHUB_TOKEN = "你的 GitHub token"
$env:GITHUB_REPOSITORY = "owner/repository"
python workflows\upload_and_trigger_cloud.py --branch main --confirm-upload
```

上传和远程验收结果会写入：

```text
reports/cloud_upload_and_acceptance.json
```

如果 GitHub 仓库也还没建，可以让脚本先建仓库、再上传、再验收：

```powershell
$env:GITHUB_TOKEN = "你的 GitHub token"
$env:GITHUB_REPOSITORY = "owner/repository"
python workflows\create_repo_upload_and_trigger.py --create-repo --confirm-upload
```

完整连接结果会写入：

```text
reports/cloud_create_upload_and_acceptance.json
```

运行后会执行：

```text
python workflows/publish_summary.py
python workflows/persist_state.py
```

`publish_summary.py` 会把总部报告写入 GitHub Actions Run Summary。`persist_state.py` 会把 `memory/`、`reports/`、`comm/outbox/`、`research/briefs/`、`media/drafts/` 中的运行状态提交回仓库，让下一次定时任务继承总部记忆。

## 指挥模型

```text
GitHub = 你的云端 AI 总部
Codex = 24h 自主执行官
你 = 只在“重大事项”出现时做决定
```

工程规则已经写入 `core/operator.py`：

- 低风险、可逆事项：Codex 自动推进并写入 `memory/operator_logs/`。
- 每次自动推进或按你决定继续，都会写入 `memory/execution_logs/`。
- 中高风险、金额超阈值、合同/付款/合规/发布/客户承诺：生成重大事项。
- 重大事项会进入 `comm/outbox/`，并在 GitHub Actions 中尝试创建 GitHub Issue。
- 你在重大事项 Issue 评论 `/approve`、`/reject`、`/revise` 后，`Owner Decision Handler` 会写回 `memory/decisions/` 并生成 `memory/continuations/`。

详细总部操作手册见：

```text
docs/github-headquarters.md
```

GitHub 上线、运行和验收手册见：

```text
docs/github-deployment-runbook.md
```

## 项目输入

复制：

```text
projects/templates/project_intake.md
```

到：

```text
projects/active/YOUR_PROJECT.md
```

然后填写国家、业主、金额、当前沟通、合同/付款/合规风险、下一步决策。

当前示例项目展示两条路径：

- `projects/active/demo-port-logistics.md`：高风险国际工程贸易事项，会进入重大事项/owner decision 流程。
- `projects/active/internal-brief-library.md`：低风险内部整理事项，由 Codex 自主执行并记录。

## 安全边界

系统不会自动签合同、付款、承诺客户、发布视频或外发高风险内容。以下事项会进入人工请示：

- 合同、索赔、仲裁、保函、付款、违约。
- 金额超过配置阈值。
- 制裁、出口管制、海关、合规、政治风险。
- 对外发布、客户承诺、微信/企业微信正式回复。

## 目录

```text
core/          判断、升级、存储、编排
intelligence/ 贸易与科研情报
content/      视频脚本、简报、对外内容草稿
comm/         微信/企业微信 outbox 与 webhook
projects/     项目输入
memory/       运行记忆、案例、最后一次运行状态
research/     科研与情报输出
media/        视频脚本输出
workflows/    本地与 GitHub 任务入口
tests/        标准库 unittest 测试
```

## 重大事项回复

本地模拟：

```powershell
python workflows\resolve_major_matter.py --project "[Major Matter] Demo Port Logistics Modernization requires owner decision" --reply "/approve proceed with staged commitment" --source local
```

GitHub 云端：

1. `International Trade AI Ops` 发现重大事项并创建 Issue。
2. 你在 Issue 下评论 `/approve ...`、`/reject ...` 或 `/revise ...`。
3. `Owner Decision Handler` 自动写入：
   - `memory/decisions/*.json`
   - `memory/continuations/*.md`
   - 更新后的 `comm/outbox/*.json`
   - GitHub Issue 回执评论
   - 自动关闭已处理的 GitHub Issue

每日任务再次运行时会读取已解决的 outbox，不会把同一个重大事项重新变成待请示；它会在 `memory/last_run.json` 中记录 `resolved_major_matter_count`，并按你的决定继续。

## 总部报告

每次运行都会生成：

```text
reports/headquarters_status.md
```

这个文件面向你阅读，列出：

- 等你决定的重大事项。
- 已按你决定继续推进的事项。
- Codex 自动执行的低风险事项。
- 每个项目的下一步 Codex 动作。

另有一个更短的老板收件箱：

```text
reports/owner_inbox.md
```

它只列出需要你拍板的重大事项，并给出可复制的 `/approve`、`/reject`、`/revise` 回复模板。

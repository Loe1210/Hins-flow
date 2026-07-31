# Codex Universal Flow

`@loe1210/codex-flow` 是一个可通过 npm 全局安装的 Codex skills 套件。它把 Universal Flow 和稳定版 Matt Pocock Skills 放在同一个 npm 包中，并提供控制台命令将 skills 安装到 Codex 的全局 skills 目录。

这不是 Codex plugin，不需要 marketplace、plugin manifest 或 Codex plugin 命令。

## 安装

从 GitHub 安装最新版：

```powershell
npm install -g https://github.com/Loe1210/codex-flow.git
codex-flow install
```

发布到 npm 后，也可以使用：

```powershell
npm install -g @loe1210/codex-flow
codex-flow install
```

如果已有旧版本 skills，使用 `--force` 更新对应文件：

```powershell
codex-flow install --force
```

默认安装目录为：

```text
Windows: %USERPROFILE%\.agents\skills
macOS/Linux: ~/.agents/skills
```

也可以指定目录，适合测试或 CI：

```powershell
codex-flow install --target C:\path\to\skills
```

## 控制台命令

```text
codex-flow install [--target <dir>] [--force]  安装或更新全部 skills
codex-flow list                                  列出 npm 包内的 skills
codex-flow path                                  显示默认全局安装目录
codex-flow doctor [--target <dir>]               检查安装完整性
codex-flow --version                             显示版本
```

安装完成后，新建一个 Codex task/thread，让 Codex 载入新增或更新的 skills。Codex 使用项目根目录的 `AGENTS.md`，不需要 `CLAUDE.md`。

## `$flow` 完整调用方式

```text
$flow plan upload-hardening "强化分片上传"
$flow review-plan 0001
$flow dev 0001
$flow review-dev 0001
$flow finish 0001
```

强制流程为：

```text
$setup-matt-pocock-skills
→ $grill-with-docs
→ $to-spec
→ 大型任务：$to-tickets
→ Gate A
→ $implement + $tdd
→ $code-review
→ Gate B
→ finish
```

Universal Flow 使用 `flowctl.py` 管理状态和门禁，使用 `project-probe.py` 只读探测仓库。它保留 `verification-contract.md`、`flow_verification`、Matt gate 状态检查、跨平台环境限制检查，以及 worktree、Gate A、Gate B、合并和清理规则。

## 支持范围

语言和生态：Go、Node/TypeScript、Python、Rust、JVM、Android、.NET、Swift、C/C++、PHP、Ruby、Elixir、Dart/Flutter，以及 generic fallback。

产品 surface：Web、后端、移动端、桌面端、CLI、库、SDK、插件、嵌入式、游戏、数据、ML、基础设施。

随包安装的稳定版 Matt Pocock Skills（均来自 `mattpocock/skills`）：

`ask-matt`、`codebase-design`、`code-review`、`diagnosing-bugs`、`domain-modeling`、`grilling`、`grill-me`、`grill-with-docs`、`handoff`、`implement`、`improve-codebase-architecture`、`prototype`、`research`、`resolving-merge-conflicts`、`setup-matt-pocock-skills`、`tdd`、`teach`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`writing-great-skills`。

不会安装 `skills/in-progress`、Vercel 或其他来源的 skills，也不会安装已删除的旧 Flow 变体。

## 首次使用配置 `AGENTS.md`

第一次在项目中运行非 Light flow 时，如果缺少 `docs/agents/issue-tracker.md` 或 `docs/agents/domain.md`，运行 `$setup-matt-pocock-skills`，按提示配置 issue tracker、领域文档和 triage labels。建议在项目根目录 `AGENTS.md` 中记录仓库命令、测试入口、平台限制和部署约束。

## 升级

```powershell
npm update -g @loe1210/codex-flow
codex-flow install --force
```

从 GitHub 安装的副本可重复执行：

```powershell
npm install -g https://github.com/Loe1210/codex-flow.git
codex-flow install --force
```

## 安全边界

`$flow` 不会自动部署、push、合并或删除用户数据。`finish` 只会在用户明确选择后执行合并、PR、保留或丢弃等动作；删除分支和 worktree 也会单独询问。

## 许可与归属

本项目以 MIT 许可证发布。随包分发的 Matt Pocock Skills 来源为公开仓库 [mattpocock/skills](https://github.com/mattpocock/skills)，原作者和许可归属保持不变。本项目作者为 Loe1210。

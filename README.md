# Codex Universal Flow

`codex-flow` 是一个可公开发布的 Codex plugin，把 Universal Flow 与 Matt Pocock 的工程 skills 打包在一起，为不同语言、平台和产品形态提供统一的、带门禁的开发流程。

## 解决的问题

`$flow` 先探测仓库，再选择语言与产品 profile，要求完成 Matt discovery/spec 与计划评审，之后才允许隔离实现、TDD、双轴 code review 和收尾。这样可以减少在错误技术假设、未确认规格或未完成验证时直接改代码的风险。

## `$flow` 完整调用方式

```text
$flow plan upload-hardening "强化分片上传"
$flow review-plan 0001
$flow dev 0001
$flow review-dev 0001
$flow finish 0001
```

核心强制顺序为：

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

`flowctl.py` 负责状态、证据和门禁；`project-probe.py` 只读探测项目，不替代人工确认。Universal Flow 保留 `verification-contract.md`、`flow_verification`、Matt gate 状态检查、跨平台环境限制检查，以及 worktree、Gate A、Gate B、合并和清理规则。

## 支持范围

语言和生态包括 Go、Node/TypeScript、Python、Rust、JVM、Android、.NET、Swift、C/C++、PHP、Ruby、Elixir、Dart/Flutter，以及未知项目的 generic fallback。产品 surface 包括 Web、后端、移动端、桌面端、CLI、库、SDK、插件、嵌入式、游戏、数据、ML 和基础设施。

本插件同时安装稳定版 Matt Pocock Skills（来源锁定为 `mattpocock/skills`）：

`ask-matt`、`codebase-design`、`code-review`、`diagnosing-bugs`、`domain-modeling`、`grilling`、`grill-me`、`grill-with-docs`、`handoff`、`implement`、`improve-codebase-architecture`、`prototype`、`research`、`resolving-merge-conflicts`、`setup-matt-pocock-skills`、`tdd`、`teach`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`writing-great-skills`。

没有打包 `skills/in-progress` 内容、Vercel 或其他来源的 skills，也没有打包 `flow-go` 或 `flow-ts`。

## 首次配置

第一次在项目中运行非 Light flow 时，如果缺少 `docs/agents/issue-tracker.md` 或 `docs/agents/domain.md`，执行 `$setup-matt-pocock-skills`，按提示配置 issue tracker 和领域文档。Codex 使用项目根目录的 `AGENTS.md`；不需要 `CLAUDE.md`。建议在 `AGENTS.md` 中记录仓库命令、边界、测试入口和部署约束。

## 从 GitHub 安装

在 Codex 中把 GitHub 仓库添加为 marketplace，再安装插件：

```powershell
codex plugin marketplace add https://github.com/Loe1210/codex-flow
codex plugin add codex-flow@codex-flow
```

也可以使用短地址：

```powershell
codex plugin marketplace add Loe1210/codex-flow
codex plugin add codex-flow@codex-flow
```

安装后新建一个 Codex task/thread，让 Codex 载入新 skills。

## 升级

```powershell
codex plugin marketplace upgrade codex-flow
codex plugin add codex-flow@codex-flow
```

如果本地开发副本已通过 personal marketplace 安装，按 plugin-creator 的更新流程运行 `update_plugin_cachebuster.py`，再重新安装并开启新 task/thread。

## 安全边界

`$flow` 不会自动部署、push、合并或删除用户数据。`finish` 只会在用户明确选择后执行合并、PR、保留或丢弃等动作；删除分支和 worktree 也会单独询问。

## 许可与归属

本插件以 MIT 许可证发布。随插件分发的 Matt Pocock Skills 来源为公开仓库 [mattpocock/skills](https://github.com/mattpocock/skills)，其原作者和许可归属保持不变；本仓库只打包锁文件中来源为 `mattpocock/skills` 的稳定版本。


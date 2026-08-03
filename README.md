# Hins-flow

Hins-flow 是一套面向 Codex 的稳定开发流程。你只需要从一个模糊需求开始，它会自动了解项目、补全需求、生成规格、实施代码、运行测试并完成双轴审查，让结果尽量符合你的预期，并留下可验证的证据。

需求写得越具体，结果通常越贴近预期；但你不需要先整理成专业的 PRD，也不需要记住 `plan`、`dev` 或 `review` 等阶段命令。

## 安装

需要 Node.js 18 或更高版本。复制执行这一条命令，即可直接从 GitHub 把 Hins-flow 和全部 Matt skills 安装到 Codex 的全局 skills 目录：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow install --force
```

这条命令不要求预先安装 `hins-flow.cmd`，也不依赖 npm 全局命令目录已经加入 `PATH`。安装器会复制并检查全部 23 个 skills。看到下面的结果即表示安装完整：

```text
Hins-flow installation is healthy: 23 skills
```

安装完成后，完全退出并重新打开 Codex，再新建一个 task，让 Codex 重新加载 skills。

如果希望把 `hins-flow` CLI 本身也长期安装为全局命令，可以选择执行：

```powershell
npm install -g https://github.com/Loe1210/Hins-flow.git
```

## 使用教程

在 Codex 中打开要处理的项目，然后每次都从 `/hins-flow` 开始。

直接描述你想要的结果即可，即使需求还很模糊：

```text
/hins-flow 我想让分片上传更稳定
```

当然，提供目标、使用场景、限制和验收标准会让结果更贴近你的预期：

```text
/hins-flow 强化分片上传：弱网断线后能够续传，重复分片不能产生脏数据，保持现有 API 兼容，并补充集成测试
```

Hins-flow 会自动判断项目类型和当前进度，不要求你手动选择阶段。它会依次完成：

```text
项目探测与任务分级
→ 需求澄清与领域建模
→ 规格和验收标准
→ 大型任务拆票
→ Gate A 计划确认
→ 隔离实现与 TDD
→ 双轴代码审查
→ Gate B 成果确认
→ 收尾
```

流程暂停时会明确说明：

- 已经完成了什么；
- 发现了什么风险或待确认项；
- 下一步将要做什么；
- 你下一句应该输入什么。

通常只需要继续输入：

```text
/hins-flow 继续
```

如果存在多个进行中的任务，Hins-flow 会请你选择一个；如果需要产品取舍、Gate 确认或危险操作授权，它会给出具体选项，不会让你猜下一步命令。

## 它会自动做什么

- 读取仓库的 `AGENTS.md`、文档、manifest、lockfile、CI 和测试脚本；
- 探测语言、包管理器、产品形态、目标平台和环境限制；
- 把模糊想法整理成问题定义、方案、用户故事、实现决策、测试决策和非目标；
- 对大型工作建立可追踪的垂直任务；
- 使用项目原生工具链实施，并通过 TDD 留下 red/green 证据；
- 分别按仓库规范和需求规格审查改动；
- 记录验证命令、结果、平台缺口、Gate 状态以及最终处置。

内部强制流程保持为：

```text
$setup-matt-pocock-skills
→ $grill-with-docs
→ $to-spec
→ Large 任务：$to-tickets
→ Gate A
→ $implement + $tdd
→ $code-review
→ Gate B
→ finish
```

这些 Matt skills 已随 Hins-flow 一起安装，使用者不需要单独下载或逐个调用。

## 中文输出规则

Hins-flow 默认把所有需要你阅读、确认或维护的内容写成简体中文，包括对话提示、需求规格、计划、change note、用户故事、验收标准、任务票、ADR、Gate 报告、代码审查、handoff、提交信息和收尾总结。

机器读取的 YAML/JSON 字段、固定状态值、代码标识符、API、命令、路径以及原始日志会保留英文或原文，Hins-flow 会紧接着用中文解释其含义。只有你明确要求其他语言，或者外部格式强制要求时，才会改变这一默认规则；即使外部内容必须用英文，也会为你提供完整的中文摘要。

## AGENTS.md

Codex 使用 `AGENTS.md` 了解项目约束，不需要 `CLAUDE.md`。如果仓库已有 `AGENTS.md`，Hins-flow 会自动读取；如果没有，它仍可先探测项目，并在确实需要补充长期约束时给出建议。

适合写入 `AGENTS.md` 的内容包括：

- 安装、测试、lint、typecheck、build 和 format 命令；
- 支持的运行时、操作系统和目标平台；
- 数据库、迁移、生成文件和部署限制；
- 必须先获得用户确认的操作。

## 支持范围

语言和生态：Go、Node.js、TypeScript、JavaScript、Python、Rust、JVM、Kotlin、Android、.NET、Swift、C/C++、PHP、Ruby、Elixir、Dart/Flutter，以及无法识别技术栈时的 generic fallback。

产品形态：Web、PWA、浏览器扩展、后端、API、服务、serverless、edge、移动端、桌面端、CLI、库、SDK、插件、嵌入式、IoT、游戏、数据、ML 和基础设施。

Hins-flow 会保留并执行 `verification-contract.md`、跨平台环境限制、worktree、Matt gate、`flow_verification`、Gate A、Gate B、合并和清理规则。

## 安全边界

Hins-flow 不会自动部署、push、合并、丢弃改动或删除用户数据。Gate A、Gate B、外部状态变更、PR、部署以及 branch/worktree 删除都需要明确授权。

输入 `/hins-flow 继续` 可以确认进入流程中的普通下一阶段，但不会被解释为授权 push、部署、合并、丢弃改动或删除数据；这些动作会单独询问。

## 更新

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow install --force
```

同一条命令也用于更新。更新后完全退出并重新打开 Codex，再新建一个 task，使新版本生效。

## 随包安装的 Matt Pocock Skills

稳定套件包括：`ask-matt`、`codebase-design`、`code-review`、`diagnosing-bugs`、`domain-modeling`、`grilling`、`grill-me`、`grill-with-docs`、`handoff`、`implement`、`improve-codebase-architecture`、`prototype`、`research`、`resolving-merge-conflicts`、`setup-matt-pocock-skills`、`tdd`、`teach`、`to-spec`、`to-tickets`、`triage`、`wayfinder` 和 `writing-great-skills`。

不会安装 `skills/in-progress`、Vercel 或其他来源的 skills。

## 许可证和归属

Hins-flow 使用 MIT 许可证。随包分发的 Matt Pocock Skills 来源于公开仓库 [mattpocock/skills](https://github.com/mattpocock/skills)，其作者与许可证归属保持不变。本项目维护者为 [Loe1210](https://github.com/Loe1210)。

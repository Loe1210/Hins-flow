# Hins-flow
Hins-flow 是一个面向 Codex 的 npm skills 套件：通过一个全局 CLI 安装 Universal Flow 和稳定版 Matt Pocock engineering skills，为跨语言、跨平台的软件项目提供可追踪、带门禁的开发流程。

它不是 Codex plugin，不需要 plugin manifest、marketplace 或 `codex plugin` 命令。安装完成后，Codex 直接从用户全局 skills 目录发现 `$hins-flow` 和 Matt skills。

## 0. 前置条件

- Node.js 18 或更高版本
- 已安装 Codex，并能创建新的 task/thread
- 项目使用根目录 `AGENTS.md` 记录仓库约束；不需要 `CLAUDE.md`

## 1. 安装 CLI

### 从 GitHub 安装

```powershell
npm install -g https://github.com/Loe1210/Hins-flow.git
```

### 从 npm 安装

```powershell
npm install -g @loe1210/hins-flow
```

检查 CLI：

```powershell
hins-flow --version
hins-flow --help
```

## 2. 安装 Codex skills

`npm install -g` 只安装控制台 CLI；必须再运行 `hins-flow install`，才能把 skills 复制到 Codex 的全局目录：

```powershell
hins-flow install
hins-flow doctor
```

默认目录：

```text
Windows: %USERPROFILE%\.agents\skills
macOS/Linux: ~/.agents/skills
```

如果要更新已经存在的 skills：

```powershell
hins-flow install --force
hins-flow doctor
```

如果 PowerShell 的脚本执行策略阻止 `.ps1`，使用 Windows shim：

```powershell
hins-flow.cmd install
hins-flow.cmd doctor
```

也可以安装到临时目录进行测试：

```powershell
hins-flow install --target C:\temp\hins-flow-skills
hins-flow doctor --target C:\temp\hins-flow-skills
```

安装或更新完成后，关闭当前 Codex task/thread，并新建一个 task/thread，让 Codex 重新加载 skills。

## 3. 首次项目配置

进入要开发的项目根目录，确认存在 `AGENTS.md`。第一次运行 Standard、Large 或 High-risk flow 时，如果以下文件不存在：

```text
docs/agents/issue-tracker.md
docs/agents/domain.md
```

先在 Codex 中运行：

```text
$setup-matt-pocock-skills
```

按提示选择 issue tracker、triage labels 和 domain docs 布局。这个配置是每个项目一次，不是每次 `$hins-flow` 都重复配置。

建议在项目的 `AGENTS.md` 中写清楚：

- 包管理器、安装命令和测试命令
- lint、typecheck、build、format 命令
- 支持的运行时和目标平台
- 数据库、迁移、生成文件和部署约束
- 哪些操作必须先获得用户确认

## 4. `$hins-flow` 全流程

标准调用顺序：

```text
$hins-flow plan <slug> "<title>"
$hins-flow review-plan <NNNN>
$hins-flow dev <NNNN>
$hins-flow review-dev <NNNN>
$hins-flow finish <NNNN>
```

推荐示例：

```text
$hins-flow plan upload-hardening "强化分片上传"
$hins-flow review-plan 0001
$hins-flow dev 0001
$hins-flow review-dev 0001
$hins-flow finish 0001
```

完整门禁顺序：

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

### 4.1 `plan`：探测、分类和规格

```text
$hins-flow plan upload-hardening "强化分片上传"
```

此阶段会：

1. 使用 `project-probe.py` 只读探测仓库。
2. 根据 manifests、lockfiles、脚本和目录结构识别语言、生态、产品 surface、目标平台和风险。
3. 读取 `profile-selection.md` 路由到 Go、Node/TypeScript、Python、Rust、JVM、Android、.NET、Swift、C/C++、PHP、Ruby、Elixir、Dart/Flutter 或 generic fallback profile。
4. 读取受影响的 ecosystem references、surface profile 和 verification contract。
5. 确保 Matt setup 已完成。
6. 运行 `$grill-with-docs`，用 `$domain-modeling` 形成领域决策、ADR 和 glossary。
7. 运行 `$to-spec`，生成 Problem、Solution、User Stories、Implementation Decisions、Testing Decisions 和 Out of Scope。
8. Large 任务运行 `$to-tickets`，拆成有 blocking edges 的 vertical tracer-bullet tickets。
9. 建立验证矩阵，并将 Matt 证据和验证证据写入 change note。

`plan` 只做计划和证据收集，不实现代码，完成后停止等待计划评审。

### 4.2 `review-plan`：Gate A

```text
$hins-flow review-plan 0001
```

Gate A 必须确认：

- profile、平台和产品 surface 假设正确
- spec 和 user stories 完整
- Large 任务 ticket breakdown 已批准
- 测试 seam 和 verification contract 明确
- Matt gates 已完成
- `flow_verification` 已完成

Gate A 未通过时不能进入 `dev`。计划评审阶段不实现代码、不创建合并提交。

### 4.3 `dev`：隔离实现和 TDD

```text
$hins-flow dev 0001
```

此阶段会：

1. 检查 Gate A。
2. 从记录的 base branch 创建或恢复隔离 worktree。
3. 使用仓库原生工具链实现，不猜测陌生技术栈命令。
4. 按已确认 seam 使用 `$tdd`，遵循 red → green → refactor 的测试驱动循环。
5. 使用 `$implement` 完成垂直切片。
6. 记录测试、类型检查、构建、平台限制和跨平台验证结果。
7. 提交实现并停止，等待开发评审。

### 4.4 `review-dev`：双轴 code review 和 Gate B

```text
$hins-flow review-dev 0001
```

此阶段使用 `$code-review` 分别执行：

- Standards：仓库规范和 Fowler smell baseline
- Spec：需求、规格和验收标准

Critical/Important finding 最多修复三轮。随后完成 review record、标记 `$tdd` 和 review gates，并停在 Gate B。

### 4.5 `finish`：只执行明确授权的收尾动作

```text
$hins-flow finish 0001
```

`finish` 会重新运行 profile/platform verification，并要求用户明确选择：

- 合并到 base branch
- 创建或更新 PR
- 保留 branch/worktree
- 丢弃变更

删除 branch 或 worktree 会单独询问。未明确授权时不会执行合并、push、部署、丢弃或删除。

## 5. 状态和验证工具

Universal Flow 的脚本位于安装后的 `hins-flow` skill 目录：

```text
%USERPROFILE%\.agents\skills\hins-flow\scripts\flowctl.py
%USERPROFILE%\.agents\skills\hins-flow\scripts\project-probe.py
```

只读探测：

```powershell
python "$env:USERPROFILE\.agents\skills\hins-flow\scripts\project-probe.py" --repo .
```

状态工具帮助：

```powershell
python "$env:USERPROFILE\.agents\skills\hins-flow\scripts\flowctl.py" --help
```

`flowctl.py` 负责 change note、状态迁移、Matt gate、`flow_verification` 和阶段 preflight。状态工具不会替代用户确认，也不会自动执行部署或数据删除。

## 6. 支持范围

语言和生态：

- Go
- Node.js / TypeScript / JavaScript
- Python
- Rust
- JVM / Kotlin
- Android
- .NET
- Swift / Apple
- C / C++ / native
- PHP
- Ruby
- Elixir
- Dart / Flutter
- generic fallback

产品 surface：

- Web、PWA、浏览器扩展
- 后端、API、服务、serverless、edge
- 移动端
- 桌面端
- CLI
- 库、SDK、插件
- 嵌入式、IoT、游戏
- 数据、ML、基础设施

Universal Flow 会保留并使用 `verification-contract.md`、跨平台限制、worktree、Gate A、Gate B、合并和清理规则。

## 7. 随包安装的 Matt Pocock Skills

以下稳定 skills 均来自 `mattpocock/skills`：

`ask-matt`、`codebase-design`、`code-review`、`diagnosing-bugs`、`domain-modeling`、`grilling`、`grill-me`、`grill-with-docs`、`handoff`、`implement`、`improve-codebase-architecture`、`prototype`、`research`、`resolving-merge-conflicts`、`setup-matt-pocock-skills`、`tdd`、`teach`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`writing-great-skills`。

不会安装 `skills/in-progress`、Vercel 或其他来源的 skills。

## 8. 升级

从 npm 升级：

```powershell
npm update -g @loe1210/hins-flow
hins-flow install --force
hins-flow doctor
```

从 GitHub 升级：

```powershell
npm install -g https://github.com/Loe1210/Hins-flow.git
hins-flow install --force
hins-flow doctor
```

升级后重新创建 Codex task/thread。

## 9. 安全边界

`$hins-flow` 不会自动部署、push、合并或删除用户数据。它不会绕过 Gate A、Gate B、Matt gate 或 `flow_verification`。所有外部状态变化、合并、PR、部署、branch/worktree 删除都需要用户明确授权。

## 10. 许可证和归属

本项目以 MIT 许可证发布。随包分发的 Matt Pocock Skills 来源为公开仓库 [mattpocock/skills](https://github.com/mattpocock/skills)，其作者和许可证归属保持不变。本项目作者为 Loe1210。

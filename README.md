# Hins-flow

Hins-flow 是一个面向 Codex 的单入口软件工程流程。你只要描述想做什么，即使需求还比较模糊，它也会先理解项目和目标，再自动选择合适的澄清、规格、实现、测试、审查和交付路径，把需求推进成经过证据验证的稳定成果。

整个过程中你只需要记住 `/hins-flow`。需求写得越详细，开始得越快；需求不完整也没关系，Hins-flow 只会追问真正影响结果的决定，并在每次需要你参与时用中文告诉你下一步怎么做。

## 一条命令安装

需要 Node.js 18 或更高版本。在 PowerShell、Windows Terminal、macOS 或 Linux 终端中运行：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow install
```

这条命令直接从 GitHub 下载并校验安装包，然后把一个完整的 `hins-flow` 安装到 Codex 的全局 skills 目录：

```text
~/.agents/skills/hins-flow
```

它不会要求 npm 账号，也不会从 npm registry 安装 Hins-flow。安装器会先完整校验文件和 22 个内置能力，再原子替换旧版本；如已有 Hins-flow，会把旧版本移到相邻的 `.hins-flow-backups` 目录，安装失败则恢复原版本。

安装或升级后，请完全退出并重新打开 Codex，再新建一个任务，让 Codex 重新发现 skill。

## 使用教程

在 Codex 项目任务中直接输入：

```text
/hins-flow 我想让分片上传更稳定
```

也可以给出更完整的目标：

```text
/hins-flow 修复大文件分片上传在网络抖动后重复写入的问题；保持现有 API 兼容，并补充并发和断点续传测试
```

Hins-flow 会自动：

1. 读取项目中的 `AGENTS.md`、代码、清单、锁文件、CI 和已有测试命令；
2. 探测语言、平台、产品形态、风险、规模和不确定性；
3. 必要时逐个确认关键产品决定，并给出推荐答案；
4. 形成中文规格、边界和验证计划；
5. 按公共行为 seam 进行实现与 TDD；
6. 只运行当前变更真正需要的测试、静态检查、构建和集成验证；
7. 在固定代码范围上分别审查 Standards 与 Spec；
8. 复用仍然有效的证据，避免重复全量测试和重复评审；
9. 在需要确认、遇到阻塞或准备完成时，用中文说明现状、风险和准确的下一步输入。

后续继续时仍然只输入：

```text
/hins-flow 继续
```

想查看当前路线、检查项、证据是否过期和阻塞原因时输入：

```text
/hins-flow 详情
```

你不需要记住 `plan`、`review-plan`、`dev`、`review-dev`、`finish`，也不需要手动调用任何 Matt skill。它们对应的强项已经被 Hins-flow 吸收为内部能力，Hins-flow 会根据任务自动选择。

## 自适应而不是固定长流程

Hins-flow 会分别判断：

- 工作类型：新功能、修复、重构、审查、研究、文档、架构、迁移、发布、教学或 skill；
- 规模：Quick、Standard 或 Large；
- 不确定性：Clear、Explore 或 Wayfinding；
- 风险：Low、Medium、High 或 Critical；
- 产品形态与当前环境真正能验证的平台。

清晰、低风险的小改动走精简路径；复杂或跨会话工作保留完整规格和可恢复状态；只有方向本身仍很模糊时才使用 Wayfinding。Wayfinding 完成后会直接合成规格，不会再重复一轮同类追问。

测试和审查也各司其职：实现阶段保存聚焦的 red/green 证据，验证阶段按计划运行一次所需检查，审查阶段只审固定 diff 的规范符合性和需求符合性。只有代码、相关规格、配置或环境改变时，受影响的证据才会失效。

## 内置工程能力

Hins-flow v2 内置并适配了 Matt Pocock Skills 的 22 个稳定方法，包括需求追问、领域建模、Wayfinding、规格与票据、诊断、研究、原型、架构设计、TDD、实现、双轴代码审查、冲突处理、handoff、教学和 skill 设计。

这些方法位于 `hins-flow/references/upstream-matt/`，作为固定版本、带哈希的内部参考；它们不会以 22 个独立全局 skills 安装，也不会在流程中互相递归调用。状态、阶段、中文交互、验证和安全权限始终由一个 Hins-flow 编排器负责。

查看内置能力清单：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow list
```

## 支持范围

语言与工具链包括：

- Go、Node.js、TypeScript、JavaScript、Python、Rust；
- JVM、Java、Kotlin、Android、.NET；
- Swift、Apple 平台、C、C++、Zig；
- PHP、Ruby、Elixir、Dart、Flutter；
- 未知技术栈的 generic fallback。

产品形态包括 Web、后端服务、移动端、桌面端、CLI、库、SDK、插件、嵌入式、游戏、数据、机器学习和基础设施。Hins-flow 只会使用仓库已有或经过确认的命令；当前电脑无法证明的平台结果会明确标为环境限制，不会假装通过。

## 项目配置

Hins-flow 默认零配置，可以安装后直接使用。Codex 使用 `AGENTS.md`；不需要为 Hins-flow 创建 `CLAUDE.md`。如果项目已有 `AGENTS.md`，Hins-flow 会遵循其作用域内规则。

只有项目确实存在特殊差异时，才需要可选的 `.hins-flow/config.yaml`，例如权威测试命令、目标环境或额外风险规则。配置中不应保存 token、密码、连接字符串、个人绝对路径或私有配置。

## 安全边界

`/hins-flow 继续` 只代表继续下一个普通、可逆的内部阶段。Hins-flow 不会因为这句话自动执行：

- push、创建 PR、合并、部署、发布或写入外部 issue；
- 生产迁移、付费资源、凭据操作或上传私有数据；
- reset、丢弃修改、删除分支、删除 worktree、清理用户文件或接受缺失验证。

这些操作每次都必须获得单独、明确的授权。Gate A 和 Gate B 用于重要方案与完成质量，不等于外部操作权限。

## 升级、检查和回滚

升级使用与安装完全相同的一条命令：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow install
```

检查已安装版本、文件哈希、内置能力和脚本：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow doctor
```

查看可回滚备份：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow rollback
```

确认恢复最近备份时再追加 `--yes`。当前版本也会先备份，不会直接删除。

从 v1 升级时，旧的 22 个独立 skills 不会被擅自删除。先预览哪些文件与 v1 官方哈希完全一致：

```powershell
npx --yes --package=https://github.com/Loe1210/Hins-flow.git hins-flow cleanup-legacy
```

确认后追加 `--yes`，这些旧目录只会被移动到备份；被修改过或来源不明的目录始终保留。

## 开发与验证

克隆仓库后运行：

```powershell
npm test
npm pack --dry-run
```

发布前还应运行 skill-creator 校验、安装器隔离测试、Python 脚本帮助与多技术栈探测，并确认包内没有缓存、凭据、个人绝对路径或不稳定上游内容。

## 许可证与来源

Hins-flow 采用 [MIT License](LICENSE)，Copyright (c) 2026 Loe1210。

内置方法派生自 [Matt Pocock Skills](https://github.com/mattpocock/skills)，固定于提交 `2ab958093e83e0ec752e6c1c5932da465bf23e0c`，同样采用 MIT License，Copyright (c) 2026 Matt Pocock。完整归属、能力清单和许可证位置见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

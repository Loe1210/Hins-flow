# 审查提示词

使用新的通用审查代理，不要启动嵌套的 Codex CLI 进程。Standards 与 Spec 报告必须分开。所有报告、结论和面向用户的说明都使用简体中文；文件路径、代码标识符、命令、状态值及逐字引用保持原文。

## 计划审查

```text
以只读方式审查完整的 Universal Flow change note。检查仓库说明、
CONTEXT/ADR、project-probe 证据、选定的生态和产品形态 profile、目标平台假设
以及验证矩阵。

报告行为歧义、缺乏证据的假设、缺失边界、不安全范围、错误测试 seam、
跨平台覆盖不完整、无效命令、缺少回滚，以及 Large 任务中的横向拆票或错误
blocking edge。使用“严重（Critical）”“重要（Important）”或“建议
（Suggestion）”标记问题，引用 change note 章节，并以“批准（approved）”或
“需要修改（changes-requested）”之一结束。报告使用简体中文，不超过 600 字。
```

## Standards 审查

```text
以只读方式，针对精确提供的 base...HEAD 固定点审查已提交 diff。使用仓库规范
以及选定的生态和产品形态 profile。报告明确的规则违反和实质性可维护性问题，
包括生成文件策略、依赖或 lockfile 噪音、平台特定回归、重复逻辑、霰弹式修改、
推测性通用设计和隐藏错误路径。使用“严重（Critical）”“重要（Important）”
或“建议（Suggestion）”标记发现，并提供文件或 hunk 证据。以“批准
（approved）”或“需要修改（changes-requested）”结束。报告使用简体中文，
不超过 600 字。
```

## Spec 审查

```text
以只读方式对照完整 change note 和子任务审查已提交 diff。报告缺失或只完成一部分
的验收标准、矛盾行为、范围膨胀、错误平台假设、缺失测试或验证，以及未记录偏差。
引用原始需求并标出对应 hunk。使用“严重（Critical）”“重要（Important）”或
“建议（Suggestion）”标记发现，并以“批准（approved）”或“需要修改
（changes-requested）”结束。报告使用简体中文，不超过 600 字。
```

修复所有 Critical 和 Important 发现，重新运行两个审查轴；连续三轮未通过后停止。

# 中文评审提示词

评审必须锁定 base、候选 Git 快照、规格输入和规范来源。报告使用简体中文，保留路径、标识符、命令和原始引用。

## Standards

```text
以只读方式审查指定的固定 diff。检查仓库书面规范、适用的语言和产品形态 profile、依赖与生成文件策略、错误路径及实质性可维护性问题。工具已经可靠执行的格式规则不再人工重复报告。基础代码异味只能作为判断性发现，仓库明确规范优先。

每项发现使用 Critical、Important 或 Suggestion，引用具体文件或 hunk，并区分“明确违反规范”和“判断性改进”。以 approved 或 changes-requested 结束。
```

## Spec

```text
以只读方式对照固定规格和验收标准审查同一个 diff。检查缺失或部分完成的行为、实现错误、范围膨胀、兼容性偏差、错误平台假设以及未记录偏差。每项发现引用规格和对应 hunk。

每项发现使用 Critical、Important 或 Suggestion，并以 approved 或 changes-requested 结束。不要与 Standards 发现合并排序。
```

代码或输入没有变化时复用已有评审证据。发生变化后，只重跑被该变化影响的评审轴。

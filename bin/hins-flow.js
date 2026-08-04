#!/usr/bin/env node

"use strict";

const path = require("node:path");
const {
  cleanupLegacy,
  defaultTarget,
  doctor,
  install,
  listBackups,
  listCapabilities,
  rollback,
} = require("../lib/installer");

const packageRoot = path.resolve(__dirname, "..");

function packageVersion() {
  return require(path.join(packageRoot, "package.json")).version;
}

function printHelp() {
  console.log(`Hins-flow v2

从 GitHub 一次安装一个全局 /hins-flow，并在内部提供完整工程能力。

用法：
  hins-flow install [--target <dir>]
  hins-flow doctor [--target <dir>] [--no-scripts]
  hins-flow list
  hins-flow path
  hins-flow cleanup-legacy [--target <dir>] [--yes]
  hins-flow rollback [--target <dir>] [--yes]
  hins-flow --version

说明：
  install         校验安装包，备份旧版后原子安装 hins-flow。
  doctor          校验安装清单、文件哈希、22 个内部能力和脚本。
  list            列出 Hins-flow 内部吸收的稳定能力。
  cleanup-legacy  仅识别与 v1 哈希完全一致的旧独立 skills；--yes 后移动到备份。
  rollback        查看备份；--yes 后恢复最近一个 Hins-flow 备份。

默认目标目录为 <home>/.agents/skills。安装器只管理 hins-flow 自己登记的文件。
`);
}

function parseOptions(args, allowedFlags = new Set()) {
  const options = { targetRoot: defaultTarget(), apply: false, runScripts: true };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--target") {
      const value = args[index + 1];
      if (!value) throw new Error("--target 需要目录参数");
      options.targetRoot = path.resolve(value);
      index += 1;
    } else if (arg === "--yes" && allowedFlags.has("yes")) {
      options.apply = true;
    } else if (arg === "--no-scripts" && allowedFlags.has("no-scripts")) {
      options.runScripts = false;
    } else if (arg === "--force" && allowedFlags.has("force")) {
      // v1 compatibility: v2 install is already an atomic replacement.
    } else {
      throw new Error(`未知参数：${arg}`);
    }
  }
  return options;
}

function printDoctor(result) {
  if (result.ok) {
    console.log(
      `Hins-flow 安装健康：v${result.version}，${result.capabilities} 个内部能力，${result.fileCount} 个受管文件。`,
    );
    console.log(`位置：${result.target}`);
  } else {
    console.error("Hins-flow doctor 发现问题：");
    for (const error of result.errors) console.error(`- ${error}`);
    process.exitCode = 1;
  }
  for (const warning of result.warnings) console.warn(`提示：${warning}`);
}

function main() {
  const [command = "--help", ...args] = process.argv.slice(2);
  if (["--help", "-h", "help"].includes(command)) {
    printHelp();
    return;
  }
  if (["--version", "-v"].includes(command)) {
    console.log(packageVersion());
    return;
  }
  if (command === "path") {
    if (args.length) throw new Error("path 不接受参数");
    console.log(defaultTarget());
    return;
  }
  if (command === "list") {
    if (args.length) throw new Error("list 不接受参数");
    for (const capability of listCapabilities(packageRoot)) {
      console.log(`${capability.name}\t${capability.adapter}`);
    }
    return;
  }
  if (command === "install") {
    const options = parseOptions(args, new Set(["force"]));
    const result = install({ packageRoot, targetRoot: options.targetRoot });
    console.log(
      `已安装 Hins-flow v${result.version}：${result.fileCount} 个文件，位置 ${result.target}`,
    );
    if (result.backup) console.log(`旧版本备份：${result.backup}`);
    printDoctor(doctor({ targetRoot: options.targetRoot }));
    console.log("请重启 Codex 并创建新任务，然后输入 /hins-flow <需求>。");
    return;
  }
  if (command === "doctor") {
    const options = parseOptions(args, new Set(["no-scripts"]));
    printDoctor(doctor({ targetRoot: options.targetRoot, runScripts: options.runScripts }));
    return;
  }
  if (command === "cleanup-legacy") {
    const options = parseOptions(args, new Set(["yes"]));
    const result = cleanupLegacy({
      packageRoot,
      targetRoot: options.targetRoot,
      apply: options.apply,
    });
    console.log(`可安全迁移的旧 skills：${result.removable.join(", ") || "无"}`);
    console.log(`已修改或来源不明、因此保留：${result.preserved.join(", ") || "无"}`);
    if (!options.apply && result.removable.length) {
      console.log("当前仅预览。确认后追加 --yes；文件会移动到备份，不会永久删除。");
    }
    if (result.backup) console.log(`旧 skills 已移动到：${result.backup}`);
    return;
  }
  if (command === "rollback") {
    const options = parseOptions(args, new Set(["yes"]));
    const result = rollback({ targetRoot: options.targetRoot, apply: options.apply });
    if (!options.apply) {
      const backups = listBackups(options.targetRoot);
      console.log(backups.length ? backups.join("\n") : "没有可回滚的 Hins-flow 备份");
      if (backups.length) console.log("确认恢复最近备份时追加 --yes。");
    } else {
      console.log(`已恢复：${result.restored}`);
      if (result.savedCurrent) console.log(`被替换版本已备份：${result.savedCurrent}`);
    }
    return;
  }
  throw new Error(`未知命令：${command}`);
}

try {
  main();
} catch (error) {
  console.error(`hins-flow: ${error.message}`);
  console.error("运行 `hins-flow --help` 查看用法。");
  process.exitCode = 1;
}

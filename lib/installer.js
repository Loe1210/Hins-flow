"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const IGNORED_NAMES = new Set([".DS_Store", "Thumbs.db"]);
const PACKAGE_MANAGED_ROOTS = [
  "bin",
  "lib",
  "skills/hins-flow",
  "LICENSE",
  "THIRD_PARTY_NOTICES.md",
  "README.md",
  "package.json",
  "manifests",
];
const PINNED_MATT_COMMIT = "2ab958093e83e0ec752e6c1c5932da465bf23e0c";
const EXPECTED_CAPABILITIES = [
  "ask-matt",
  "code-review",
  "codebase-design",
  "diagnosing-bugs",
  "domain-modeling",
  "grill-me",
  "grill-with-docs",
  "grilling",
  "handoff",
  "implement",
  "improve-codebase-architecture",
  "prototype",
  "research",
  "resolving-merge-conflicts",
  "setup-matt-pocock-skills",
  "tdd",
  "teach",
  "to-spec",
  "to-tickets",
  "triage",
  "wayfinder",
  "writing-great-skills",
];
const PORTABLE_TEXT_EXTENSIONS = new Set([
  ".js",
  ".json",
  ".md",
  ".py",
  ".sh",
  ".toml",
  ".txt",
  ".yaml",
  ".yml",
]);
const PORTABLE_TEXT_NAMES = new Set(["LICENSE"]);

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function portableBytes(filePath) {
  const content = fs.readFileSync(filePath);
  const extension = path.extname(filePath).toLowerCase();
  if (!PORTABLE_TEXT_EXTENSIONS.has(extension) && !PORTABLE_TEXT_NAMES.has(path.basename(filePath))) {
    return content;
  }
  return Buffer.from(content.toString("utf8").replace(/\r\n?/g, "\n"), "utf8");
}

function sha256PortableFile(filePath) {
  return crypto.createHash("sha256").update(portableBytes(filePath)).digest("hex");
}

function relativeUnix(base, filePath) {
  return path.relative(base, filePath).split(path.sep).join("/");
}

function shouldIgnore(name) {
  return (
    IGNORED_NAMES.has(name) ||
    name === "__pycache__" ||
    name.endsWith(".pyc") ||
    name.endsWith(".pyo")
  );
}

function walkFiles(root) {
  if (!fs.existsSync(root)) return [];
  if (fs.statSync(root).isFile()) return [root];
  const files = [];
  const visit = (current) => {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (shouldIgnore(entry.name)) continue;
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) visit(fullPath);
      else if (entry.isFile()) files.push(fullPath);
    }
  };
  visit(root);
  return files.sort((left, right) => left.localeCompare(right));
}

function fileManifest(root) {
  const files = {};
  for (const filePath of walkFiles(root)) {
    const relative = relativeUnix(root, filePath);
    if (relative === ".hins-flow-install.json") continue;
    files[relative] = sha256File(filePath);
  }
  return files;
}

function copyDirectory(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (shouldIgnore(entry.name)) continue;
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) copyDirectory(sourcePath, destinationPath);
    else if (entry.isFile()) fs.copyFileSync(sourcePath, destinationPath);
  }
}

function writeJsonAtomic(destination, value) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.${process.pid}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, destination);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function defaultTarget() {
  return path.join(os.homedir(), ".agents", "skills");
}

function backupRootFor(targetRoot) {
  return path.join(path.dirname(path.resolve(targetRoot)), ".hins-flow-backups");
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function randomSuffix() {
  return crypto.randomBytes(4).toString("hex");
}

function ensureChild(parent, candidate) {
  const resolvedParent = path.resolve(parent);
  const resolvedCandidate = path.resolve(candidate);
  const relative = path.relative(resolvedParent, resolvedCandidate);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`不安全的内部路径：${resolvedCandidate}`);
  }
  return resolvedCandidate;
}

function removeInternalTemporary(parent, candidate) {
  const safe = ensureChild(parent, candidate);
  if (fs.existsSync(safe)) fs.rmSync(safe, { recursive: true, force: true });
}

function readFrontmatter(skillRoot) {
  const skillFile = path.join(skillRoot, "SKILL.md");
  if (!fs.existsSync(skillFile)) return null;
  const text = fs.readFileSync(skillFile, "utf8");
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) return null;
  return {
    name: match[1].match(/^name:\s*(.+)$/m)?.[1]?.trim(),
    description: match[1].match(/^description:\s*(.+)$/m)?.[1]?.trim(),
  };
}

function validateCapabilitySources(skillRoot) {
  const manifestPath = path.join(skillRoot, "references", "capability-sources.json");
  const errors = [];
  if (!fs.existsSync(manifestPath)) return ["缺少 references/capability-sources.json"];
  const manifest = readJson(manifestPath);
  if (!Array.isArray(manifest.capabilities) || manifest.capabilities.length !== 22) {
    errors.push(`内部能力数量应为 22，实际为 ${manifest.capabilities?.length ?? "无效"}`);
    return errors;
  }
  if (manifest.hashAlgorithm !== "sha256-normalized-lf-v1") {
    errors.push(`不支持的能力哈希算法：${manifest.hashAlgorithm || "缺失"}`);
  }
  if (manifest.source?.commit !== PINNED_MATT_COMMIT) {
    errors.push(`Matt 来源提交不匹配：${manifest.source?.commit || "缺失"}`);
  }
  if (manifest.source?.repository !== "https://github.com/mattpocock/skills") {
    errors.push(`Matt 来源仓库不匹配：${manifest.source?.repository || "缺失"}`);
  }
  const names = manifest.capabilities.map((capability) => capability.name).sort();
  if (JSON.stringify(names) !== JSON.stringify(EXPECTED_CAPABILITIES)) {
    errors.push("内部能力名称与稳定清单不一致");
  }
  const vendoredRoot = path.join(skillRoot, "references", "upstream-matt");
  const expectedVendored = new Set(["LICENSE"]);
  const licensePath = path.join(vendoredRoot, "LICENSE");
  if (
    !fs.existsSync(licensePath) ||
    sha256PortableFile(licensePath) !== manifest.source?.licenseSha256
  ) {
    errors.push("Matt LICENSE 缺失或哈希不匹配");
  }
  for (const capability of manifest.capabilities) {
    const protocolPath = ensureChild(
      skillRoot,
      path.join(skillRoot, "references", ...capability.protocol.split("/")),
    );
    if (!fs.existsSync(protocolPath)) {
      errors.push(`${capability.name}: 缺少 ${capability.protocol}`);
      continue;
    }
    const capabilityRoot = path.dirname(protocolPath);
    for (const entry of capability.files || []) {
      const filePath = ensureChild(
        capabilityRoot,
        path.join(capabilityRoot, ...entry.vendored.split("/")),
      );
      expectedVendored.add(relativeUnix(vendoredRoot, filePath));
      if (!fs.existsSync(filePath)) {
        errors.push(`${capability.name}: 缺少来源文件 ${entry.vendored}`);
      } else if (sha256PortableFile(filePath) !== entry.sha256) {
        errors.push(`${capability.name}: 来源文件哈希不匹配 ${entry.vendored}`);
      }
    }
  }
  const actualVendored = new Set(
    walkFiles(vendoredRoot).map((filePath) => relativeUnix(vendoredRoot, filePath)),
  );
  for (const relative of expectedVendored) {
    if (!actualVendored.has(relative)) errors.push(`缺少登记的上游文件：${relative}`);
  }
  for (const relative of actualVendored) {
    if (!expectedVendored.has(relative)) errors.push(`存在未登记的上游文件：${relative}`);
  }
  return errors;
}

function validateSkill(skillRoot, expectedFiles = null) {
  const errors = [];
  const metadata = readFrontmatter(skillRoot);
  if (!metadata) errors.push("缺少或无法解析 SKILL.md frontmatter");
  else {
    if (metadata.name !== "hins-flow") errors.push(`skill 名称应为 hins-flow，实际为 ${metadata.name || "缺失"}`);
    if (!metadata.description) errors.push("SKILL.md description 缺失");
  }
  for (const relative of [
    "agents/openai.yaml",
    "scripts/flowctl.py",
    "scripts/project-probe.py",
    "references/workflow.md",
    "references/routing.md",
    "references/verification-contract.md",
    "references/language-policy.md",
  ]) {
    if (!fs.existsSync(path.join(skillRoot, ...relative.split("/")))) errors.push(`缺少 ${relative}`);
  }
  errors.push(...validateCapabilitySources(skillRoot));
  if (expectedFiles) {
    const actual = fileManifest(skillRoot);
    for (const [relative, hash] of Object.entries(expectedFiles)) {
      try {
        ensureChild(skillRoot, path.join(skillRoot, ...relative.split("/")));
      } catch {
        errors.push(`安装清单包含不安全路径：${relative}`);
        continue;
      }
      if (!Object.hasOwn(actual, relative)) errors.push(`安装文件缺失：${relative}`);
      else if (actual[relative] !== hash) errors.push(`安装文件哈希不匹配：${relative}`);
    }
    for (const relative of Object.keys(actual)) {
      if (!Object.hasOwn(expectedFiles, relative)) errors.push(`存在未登记安装文件：${relative}`);
    }
  }
  return errors;
}

function validatePackage(packageRoot) {
  const manifestPath = path.join(packageRoot, "manifests", "package-files.json");
  if (!fs.existsSync(manifestPath)) throw new Error("安装包缺少 manifests/package-files.json");
  const manifest = readJson(manifestPath);
  const errors = [];
  if (!manifest.files || typeof manifest.files !== "object" || Array.isArray(manifest.files)) {
    errors.push("安装包清单 files 必须是对象");
  }
  if (manifest.schemaVersion !== 1) errors.push(`不支持的安装包清单版本：${manifest.schemaVersion}`);
  if (manifest.hashAlgorithm !== "sha256-normalized-lf-v1") {
    errors.push(`不支持的安装包哈希算法：${manifest.hashAlgorithm || "缺失"}`);
  }
  if (manifest.packageVersion !== packageVersion(packageRoot)) {
    errors.push(`安装包版本与清单不一致：${packageVersion(packageRoot)} != ${manifest.packageVersion}`);
  }
  for (const [relative, hash] of Object.entries(manifest.files || {})) {
    let filePath;
    try {
      filePath = ensureChild(packageRoot, path.join(packageRoot, ...relative.split("/")));
    } catch {
      errors.push(`安装包清单包含不安全路径：${relative}`);
      continue;
    }
    if (!fs.existsSync(filePath)) errors.push(`安装包文件缺失：${relative}`);
    else if (sha256PortableFile(filePath) !== hash) errors.push(`安装包文件哈希不匹配：${relative}`);
  }
  const actual = new Set();
  for (const relativeRoot of PACKAGE_MANAGED_ROOTS) {
    const absoluteRoot = path.join(packageRoot, ...relativeRoot.split("/"));
    for (const filePath of walkFiles(absoluteRoot)) {
      const relative = relativeUnix(packageRoot, filePath);
      if (relative !== "manifests/package-files.json") actual.add(relative);
    }
  }
  for (const relative of actual) {
    if (!Object.hasOwn(manifest.files || {}, relative)) errors.push(`安装包存在未登记文件：${relative}`);
  }
  if (errors.length) throw new Error(errors.join("\n"));
  return manifest;
}

function packageVersion(packageRoot) {
  return readJson(path.join(packageRoot, "package.json")).version;
}

function install({ packageRoot, targetRoot = defaultTarget(), verifyPackage = true }) {
  const resolvedPackage = path.resolve(packageRoot);
  const resolvedTargetRoot = path.resolve(targetRoot);
  const source = path.join(resolvedPackage, "skills", "hins-flow");
  const target = path.join(resolvedTargetRoot, "hins-flow");
  if (!fs.existsSync(source)) throw new Error(`安装包缺少 ${source}`);
  if (verifyPackage) validatePackage(resolvedPackage);
  fs.mkdirSync(resolvedTargetRoot, { recursive: true });

  const stage = ensureChild(
    resolvedTargetRoot,
    path.join(resolvedTargetRoot, `.hins-flow-stage-${process.pid}-${randomSuffix()}`),
  );
  const backups = backupRootFor(resolvedTargetRoot);
  fs.mkdirSync(backups, { recursive: true });
  let backup = null;
  try {
    copyDirectory(source, stage);
    const stagedErrors = validateSkill(stage);
    if (stagedErrors.length) throw new Error(`暂存安装校验失败：\n- ${stagedErrors.join("\n- ")}`);
    const files = fileManifest(stage);
    const installManifest = {
      schemaVersion: 2,
      hashAlgorithm: "sha256-raw-v1",
      owner: "hins-flow",
      packageVersion: packageVersion(resolvedPackage),
      installedAt: new Date().toISOString(),
      source: "https://github.com/Loe1210/Hins-flow",
      files,
    };
    writeJsonAtomic(path.join(stage, ".hins-flow-install.json"), installManifest);
    const finalStageErrors = validateSkill(stage, files);
    if (finalStageErrors.length) throw new Error(`安装清单校验失败：\n- ${finalStageErrors.join("\n- ")}`);

    if (fs.existsSync(target)) {
      backup = path.join(backups, `hins-flow-${timestamp()}-${randomSuffix()}`);
      fs.renameSync(target, backup);
    }
    try {
      fs.renameSync(stage, target);
    } catch (error) {
      if (backup && fs.existsSync(backup) && !fs.existsSync(target)) fs.renameSync(backup, target);
      throw error;
    }
    return {
      target,
      backup,
      version: installManifest.packageVersion,
      fileCount: Object.keys(files).length,
    };
  } finally {
    if (fs.existsSync(stage)) removeInternalTemporary(resolvedTargetRoot, stage);
  }
}

function runPythonHelp(scriptPath) {
  const attempts = process.platform === "win32" ? [["python", []], ["py", ["-3"]]] : [["python3", []], ["python", []]];
  for (const [command, prefix] of attempts) {
    const result = spawnSync(command, [...prefix, scriptPath, "--help"], {
      encoding: "utf8",
      windowsHide: true,
    });
    if (!result.error && result.status === 0) return { ok: true, command: [command, ...prefix].join(" ") };
  }
  return { ok: false, command: null };
}

function doctor({ targetRoot = defaultTarget(), runScripts = true }) {
  const target = path.join(path.resolve(targetRoot), "hins-flow");
  const errors = [];
  const warnings = [];
  if (!fs.existsSync(target)) {
    return { ok: false, target, errors: ["未找到全局 hins-flow skill"], warnings, capabilities: 0 };
  }
  const manifestPath = path.join(target, ".hins-flow-install.json");
  let installManifest = null;
  if (!fs.existsSync(manifestPath)) errors.push("缺少 .hins-flow-install.json，无法确认文件所有权和版本");
  else {
    try {
      installManifest = readJson(manifestPath);
    } catch (error) {
      errors.push(`安装清单无法解析：${error.message}`);
    }
  }
  errors.push(...validateSkill(target, installManifest?.files || null));
  const capabilityPath = path.join(target, "references", "capability-sources.json");
  let capabilities = 0;
  if (fs.existsSync(capabilityPath)) {
    capabilities = readJson(capabilityPath).capabilities?.length || 0;
  }
  let python = null;
  if (runScripts) {
    python = runPythonHelp(path.join(target, "scripts", "flowctl.py"));
    if (!python.ok) warnings.push("当前终端未找到可运行 flowctl.py 的 Python；Codex 可改用工作区依赖运行时");
    const probe = runPythonHelp(path.join(target, "scripts", "project-probe.py"));
    if (!probe.ok && python?.ok) errors.push("project-probe.py --help 运行失败");
  }
  return {
    ok: errors.length === 0,
    target,
    version: installManifest?.packageVersion || null,
    fileCount: installManifest ? Object.keys(installManifest.files || {}).length : 0,
    capabilities,
    python,
    errors,
    warnings,
  };
}

function listCapabilities(packageRoot) {
  const manifest = readJson(
    path.join(packageRoot, "skills", "hins-flow", "references", "capability-sources.json"),
  );
  return manifest.capabilities.map(({ name, adapter, protocol }) => ({ name, adapter, protocol }));
}

function legacyStatus({ packageRoot, targetRoot = defaultTarget() }) {
  const manifest = readJson(path.join(packageRoot, "manifests", "legacy-v1.json"));
  const resolvedTarget = path.resolve(targetRoot);
  const removable = [];
  const preserved = [];
  const absent = [];
  for (const [name, record] of Object.entries(manifest.skills || {})) {
    const skillRoot = path.join(resolvedTarget, name);
    if (!fs.existsSync(skillRoot)) {
      absent.push(name);
      continue;
    }
    const actual = fileManifest(skillRoot);
    const expected = record.files || {};
    const exact =
      Object.keys(actual).length === Object.keys(expected).length &&
      Object.entries(expected).every(([relative, hash]) => actual[relative] === hash);
    if (exact) removable.push(name);
    else preserved.push(name);
  }
  return { removable: removable.sort(), preserved: preserved.sort(), absent: absent.sort() };
}

function cleanupLegacy({ packageRoot, targetRoot = defaultTarget(), apply = false }) {
  const status = legacyStatus({ packageRoot, targetRoot });
  if (!apply || status.removable.length === 0) return { ...status, backup: null };
  const resolvedTarget = path.resolve(targetRoot);
  const backup = path.join(backupRootFor(resolvedTarget), `legacy-v1-${timestamp()}-${randomSuffix()}`);
  fs.mkdirSync(backup, { recursive: true });
  for (const name of status.removable) {
    const source = ensureChild(resolvedTarget, path.join(resolvedTarget, name));
    fs.renameSync(source, path.join(backup, name));
  }
  return { ...status, backup };
}

function listBackups(targetRoot = defaultTarget()) {
  const root = backupRootFor(targetRoot);
  if (!fs.existsSync(root)) return [];
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith("hins-flow-"))
    .map((entry) => path.join(root, entry.name))
    .sort()
    .reverse();
}

function rollback({ targetRoot = defaultTarget(), apply = false }) {
  const backups = listBackups(targetRoot);
  if (!apply) return { available: backups, restored: null, savedCurrent: null };
  if (backups.length === 0) throw new Error("没有可回滚的 Hins-flow 备份");
  const resolvedTargetRoot = path.resolve(targetRoot);
  const target = path.join(resolvedTargetRoot, "hins-flow");
  const selected = backups[0];
  const savedCurrent = fs.existsSync(target)
    ? path.join(backupRootFor(resolvedTargetRoot), `hins-flow-rollback-current-${timestamp()}-${randomSuffix()}`)
    : null;
  if (savedCurrent) fs.renameSync(target, savedCurrent);
  try {
    fs.renameSync(selected, target);
  } catch (error) {
    if (savedCurrent && fs.existsSync(savedCurrent) && !fs.existsSync(target)) fs.renameSync(savedCurrent, target);
    throw error;
  }
  return { available: backups, restored: target, savedCurrent };
}

module.exports = {
  backupRootFor,
  cleanupLegacy,
  defaultTarget,
  doctor,
  fileManifest,
  install,
  legacyStatus,
  listBackups,
  listCapabilities,
  readFrontmatter,
  rollback,
  sha256File,
  sha256PortableFile,
  validateCapabilitySources,
  validatePackage,
  validateSkill,
  walkFiles,
};

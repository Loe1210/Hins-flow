#!/usr/bin/env node

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const repoRoot = path.resolve(__dirname, "..");
const ignoredNames = new Set(["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".DS_Store", "Thumbs.db"]);
const portableTextExtensions = new Set([".js", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"]);
const portableTextNames = new Set(["LICENSE"]);

function sha256(filePath, portable = false) {
  let content = fs.readFileSync(filePath);
  if (
    portable &&
    (portableTextExtensions.has(path.extname(filePath).toLowerCase()) || portableTextNames.has(path.basename(filePath)))
  ) {
    content = Buffer.from(content.toString("utf8").replace(/\r\n?/g, "\n"), "utf8");
  }
  return crypto.createHash("sha256").update(content).digest("hex");
}

function walkFiles(root) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  const visit = (current) => {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (ignoredNames.has(entry.name) || entry.name.endsWith(".pyc") || entry.name.endsWith(".pyo")) continue;
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) visit(fullPath);
      else if (entry.isFile()) files.push(fullPath);
    }
  };
  if (fs.statSync(root).isDirectory()) visit(root);
  else files.push(root);
  return files.sort((left, right) => left.localeCompare(right));
}

function relativeUnix(base, filePath) {
  return path.relative(base, filePath).split(path.sep).join("/");
}

function writeJsonAtomic(destination, value) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.${process.pid}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, destination);
}

function gitHead() {
  return execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: repoRoot,
    encoding: "utf8",
  }).trim();
}

function packageVersion() {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, "package.json"), "utf8")).version;
}

function buildLegacyManifest() {
  const skillsRoot = path.join(repoRoot, "skills");
  const skills = {};
  for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name === "hins-flow") continue;
    const skillRoot = path.join(skillsRoot, entry.name);
    const files = {};
    for (const filePath of walkFiles(skillRoot)) {
      files[relativeUnix(skillRoot, filePath)] = sha256(filePath);
    }
    skills[entry.name] = { files };
  }
  const manifest = {
    schemaVersion: 1,
    description: "Files shipped as separate global skills by Hins-flow 1.3.0.",
    sourceCommit: gitHead(),
    sourceVersion: packageVersion(),
    skills,
  };
  writeJsonAtomic(path.join(repoRoot, "manifests", "legacy-v1.json"), manifest);
  return manifest;
}

function buildPackageManifest() {
  const roots = [
    "bin",
    "lib",
    "skills/hins-flow",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "README.md",
    "package.json",
    "manifests/legacy-v1.json",
  ];
  const files = {};
  for (const relativeRoot of roots) {
    const absoluteRoot = path.join(repoRoot, ...relativeRoot.split("/"));
    for (const filePath of walkFiles(absoluteRoot)) {
      files[relativeUnix(repoRoot, filePath)] = sha256(filePath, true);
    }
  }
  const manifest = {
    schemaVersion: 1,
    hashAlgorithm: "sha256-normalized-lf-v1",
    packageVersion: packageVersion(),
    files,
  };
  writeJsonAtomic(path.join(repoRoot, "manifests", "package-files.json"), manifest);
  return manifest;
}

function main() {
  const command = process.argv[2] || "all";
  if (!new Set(["legacy", "package", "all"]).has(command)) {
    throw new Error("usage: build-manifests.js [legacy|package|all]");
  }
  if (command === "legacy" || command === "all") buildLegacyManifest();
  if (command === "package" || command === "all") buildPackageManifest();
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`build-manifests: ${error.message}`);
    process.exitCode = 1;
  }
}

module.exports = {
  buildLegacyManifest,
  buildPackageManifest,
  sha256,
  walkFiles,
};

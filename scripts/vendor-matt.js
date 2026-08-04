#!/usr/bin/env node

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const repoRoot = path.resolve(__dirname, "..");
const destinationRoot = path.join(
  repoRoot,
  "skills",
  "hins-flow",
  "references",
  "upstream-matt",
);
const sourceManifestPath = path.join(
  repoRoot,
  "skills",
  "hins-flow",
  "references",
  "capability-sources.json",
);
const pinnedCommit = "2ab958093e83e0ec752e6c1c5932da465bf23e0c";
const portableTextExtensions = new Set([".js", ".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"]);
const portableTextNames = new Set(["LICENSE"]);

const adapters = {
  "ask-matt": "routing",
  "diagnosing-bugs": "diagnosis-and-research",
  "grill-with-docs": "discovery",
  triage: "planning",
  "improve-codebase-architecture": "architecture",
  "setup-matt-pocock-skills": "project-policy",
  tdd: "delivery",
  "to-spec": "planning",
  "to-tickets": "planning",
  wayfinder: "discovery",
  implement: "delivery",
  prototype: "diagnosis-and-research",
  research: "diagnosis-and-research",
  "domain-modeling": "discovery",
  "codebase-design": "architecture",
  "code-review": "review-and-verification",
  "resolving-merge-conflicts": "delivery",
  "grill-me": "discovery",
  grilling: "discovery",
  handoff: "continuity",
  teach: "continuity",
  "writing-great-skills": "skill-authoring",
};

function sha256(buffer, filePath) {
  let content = buffer;
  if (
    portableTextExtensions.has(path.extname(filePath).toLowerCase()) ||
    portableTextNames.has(path.basename(filePath))
  ) {
    content = Buffer.from(buffer.toString("utf8").replace(/\r\n?/g, "\n"), "utf8");
  }
  return crypto.createHash("sha256").update(content).digest("hex");
}

function copySkill(sourceDir, destinationDir) {
  const files = [];
  const visit = (currentSource, currentDestination) => {
    fs.mkdirSync(currentDestination, { recursive: true });
    for (const entry of fs.readdirSync(currentSource, { withFileTypes: true })) {
      if (entry.isDirectory() && entry.name === "agents") continue;
      const sourcePath = path.join(currentSource, entry.name);
      if (entry.isDirectory()) {
        visit(sourcePath, path.join(currentDestination, entry.name));
        continue;
      }
      if (!entry.isFile()) continue;
      const destinationName = entry.name === "SKILL.md" ? "PROTOCOL.md" : entry.name;
      const destinationPath = path.join(currentDestination, destinationName);
      const content = fs.readFileSync(sourcePath);
      fs.writeFileSync(destinationPath, content);
      files.push({
        source: path.relative(sourceDir, sourcePath).split(path.sep).join("/"),
        vendored: path.relative(destinationDir, destinationPath).split(path.sep).join("/"),
        sha256: sha256(content, sourcePath),
      });
    }
  };
  visit(sourceDir, destinationDir);
  return files.sort((left, right) => left.vendored.localeCompare(right.vendored));
}

function writeJsonAtomic(destination, value) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  const temporary = `${destination}.${process.pid}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, destination);
}

function main() {
  const sourceIndex = process.argv.indexOf("--source");
  const sourceRoot = sourceIndex >= 0 ? process.argv[sourceIndex + 1] : null;
  if (!sourceRoot) throw new Error("usage: vendor-matt.js --source <mattpocock-skills-checkout>");
  const resolvedSource = path.resolve(sourceRoot);
  const pluginManifest = JSON.parse(
    fs.readFileSync(path.join(resolvedSource, ".claude-plugin", "plugin.json"), "utf8"),
  );
  const sourceCommit = execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: resolvedSource,
    encoding: "utf8",
  }).trim();
  if (sourceCommit !== pinnedCommit) {
    throw new Error(`expected pinned Matt commit ${pinnedCommit}, found ${sourceCommit}`);
  }
  const listedNames = pluginManifest.skills.map((relative) => path.basename(relative)).sort();
  const adaptedNames = Object.keys(adapters).sort();
  if (JSON.stringify(listedNames) !== JSON.stringify(adaptedNames)) {
    throw new Error("upstream stable skill list does not match the declared Hins adapters");
  }

  const stageRoot = `${destinationRoot}.stage-${process.pid}`;
  if (fs.existsSync(stageRoot)) fs.rmSync(stageRoot, { recursive: true, force: true });
  fs.mkdirSync(stageRoot, { recursive: true });

  const capabilities = [];
  for (const relativeSkill of pluginManifest.skills) {
    if (relativeSkill.includes("/in-progress/") || relativeSkill.includes("/deprecated/")) {
      throw new Error(`unstable skill listed by upstream plugin manifest: ${relativeSkill}`);
    }
    const sourceDir = path.join(resolvedSource, relativeSkill.replace(/^\.\//, ""));
    const name = path.basename(sourceDir);
    if (!adapters[name]) throw new Error(`no Hins adapter is declared for ${name}`);
    const destinationDir = path.join(stageRoot, name);
    const files = copySkill(sourceDir, destinationDir);
    capabilities.push({
      name,
      adapter: adapters[name],
      sourcePath: relativeSkill.replace(/^\.\//, ""),
      protocol: `upstream-matt/${name}/PROTOCOL.md`,
      files,
    });
  }

  const license = fs.readFileSync(path.join(resolvedSource, "LICENSE"));
  fs.writeFileSync(path.join(stageRoot, "LICENSE"), license);

  const manifest = {
    schemaVersion: 1,
    hashAlgorithm: "sha256-normalized-lf-v1",
    source: {
      repository: "https://github.com/mattpocock/skills",
      commit: sourceCommit,
      pluginVersion: pluginManifest.version,
      license: "MIT",
      licenseSha256: sha256(license, path.join(resolvedSource, "LICENSE")),
      copyright: "Copyright (c) 2026 Matt Pocock",
    },
    capabilities: capabilities.sort((left, right) => left.name.localeCompare(right.name)),
  };
  const backupRoot = `${destinationRoot}.backup-${process.pid}`;
  try {
    if (fs.existsSync(destinationRoot)) fs.renameSync(destinationRoot, backupRoot);
    fs.renameSync(stageRoot, destinationRoot);
    writeJsonAtomic(sourceManifestPath, manifest);
    if (fs.existsSync(backupRoot)) fs.rmSync(backupRoot, { recursive: true, force: true });
  } catch (error) {
    if (fs.existsSync(destinationRoot)) fs.rmSync(destinationRoot, { recursive: true, force: true });
    if (fs.existsSync(backupRoot)) fs.renameSync(backupRoot, destinationRoot);
    throw error;
  } finally {
    if (fs.existsSync(stageRoot)) fs.rmSync(stageRoot, { recursive: true, force: true });
  }
  console.log(`Vendored ${capabilities.length} stable Matt capabilities from ${sourceCommit}.`);
}

try {
  main();
} catch (error) {
  console.error(`vendor-matt: ${error.message}`);
  process.exitCode = 1;
}

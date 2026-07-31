#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..");
const bundledSkillsRoot = path.join(packageRoot, "skills");

function printHelp() {
  console.log(`Hins-flow

Install the bundled Universal Flow and Matt Pocock skills for Codex.

Usage:
  hins-flow install [--target <dir>] [--force]
  hins-flow list
  hins-flow path
  hins-flow doctor [--target <dir>]
  hins-flow --help
  hins-flow --version

Commands:
  install  Copy bundled skills into the user's global Codex skills directory.
  list     List the skills bundled in this npm package.
  path     Print the default global skills directory.
  doctor   Check an installed skills directory and Flow entry points.

The default target is <home>/.agents/skills. Existing files are preserved unless
--force is supplied. Codex uses AGENTS.md; CLAUDE.md is not required.
`);
}

function packageVersion() {
  return JSON.parse(fs.readFileSync(path.join(packageRoot, "package.json"), "utf8")).version;
}

function defaultTarget() {
  return path.join(os.homedir(), ".agents", "skills");
}

function parseOptions(args) {
  const options = { force: false, target: defaultTarget() };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--force") {
      options.force = true;
    } else if (arg === "--target") {
      const value = args[index + 1];
      if (!value) throw new Error("--target requires a directory");
      options.target = path.resolve(value);
      index += 1;
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }
  return options;
}

function bundledSkillNames() {
  return fs
    .readdirSync(bundledSkillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

function copyDirectory(source, destination, force, copied, skipped) {
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      fs.mkdirSync(destinationPath, { recursive: true });
      copyDirectory(sourcePath, destinationPath, force, copied, skipped);
      continue;
    }
    if (!entry.isFile()) continue;
    if (path.basename(entry.name) === ".DS_Store" || entry.name.endsWith(".pyc")) continue;
    if (fs.existsSync(destinationPath) && !force) {
      skipped.push(path.relative(destination, destinationPath));
      continue;
    }
    fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
    fs.copyFileSync(sourcePath, destinationPath);
    copied.push(path.relative(destination, destinationPath));
  }
}

function install(options) {
  const names = bundledSkillNames();
  fs.mkdirSync(options.target, { recursive: true });
  const copied = [];
  const skipped = [];
  for (const name of names) {
    copyDirectory(
      path.join(bundledSkillsRoot, name),
      path.join(options.target, name),
      options.force,
      copied,
      skipped,
    );
  }
  console.log(`Installed ${copied.length} files from ${names.length} skills into ${options.target}`);
  if (skipped.length > 0) {
    console.log(`Skipped ${skipped.length} existing files. Re-run with --force to update them.`);
  }
}

function listSkills() {
  for (const name of bundledSkillNames()) console.log(name);
}

function readSkillFrontmatter(skillPath) {
  const skillFile = path.join(skillPath, "SKILL.md");
  if (!fs.existsSync(skillFile)) return null;
  const text = fs.readFileSync(skillFile, "utf8");
  if (!text.startsWith("---\n") && !text.startsWith("---\r\n")) return null;
  const bodyStart = text.startsWith("---\r\n") ? 5 : 4;
  const endMatch = text.slice(bodyStart).match(/\r?\n---(?:\r?\n|$)/);
  if (!endMatch || endMatch.index === undefined) return null;
  const end = bodyStart + endMatch.index;
  const frontmatter = text.slice(bodyStart, end);
  const name = frontmatter.match(/^name:\s*(.+)$/m)?.[1]?.trim();
  const description = frontmatter.match(/^description:\s*(.+)$/m)?.[1]?.trim();
  return { name, description };
}

function doctor(options) {
  const errors = [];
  const names = bundledSkillNames();
  for (const name of names) {
    const target = path.join(options.target, name);
    const metadata = readSkillFrontmatter(target);
    if (!metadata) {
      errors.push(`${name}: missing or invalid SKILL.md frontmatter`);
      continue;
    }
    if (metadata.name !== name) errors.push(`${name}: frontmatter name is ${metadata.name || "missing"}`);
    if (!metadata.description) errors.push(`${name}: frontmatter description is missing`);
  }
  const flowRoot = path.join(options.target, "hins-flow");
  for (const relative of ["scripts/flowctl.py", "scripts/project-probe.py", "references/verification-contract.md"]) {
    if (!fs.existsSync(path.join(flowRoot, relative))) errors.push(`hins-flow: missing ${relative}`);
  }
  if (errors.length > 0) {
    console.error("Hins-flow doctor found problems:");
    for (const error of errors) console.error(`- ${error}`);
    process.exitCode = 1;
    return;
  }
  console.log(`Hins-flow installation is healthy: ${names.length} skills in ${options.target}`);
}

function main() {
  const [command = "--help", ...args] = process.argv.slice(2);
  if (command === "--help" || command === "-h" || command === "help") {
    printHelp();
    return;
  }
  if (command === "--version" || command === "-v") {
    console.log(packageVersion());
    return;
  }
  if (command === "list") {
    if (args.length > 0) throw new Error("list does not accept options");
    listSkills();
    return;
  }
  if (command === "path") {
    if (args.length > 0) throw new Error("path does not accept options");
    console.log(defaultTarget());
    return;
  }
  if (command === "install") {
    install(parseOptions(args));
    return;
  }
  if (command === "doctor") {
    doctor(parseOptions(args));
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

try {
  main();
} catch (error) {
  console.error(`hins-flow: ${error.message}`);
  console.error("Run `hins-flow --help` for usage.");
  process.exitCode = 1;
}

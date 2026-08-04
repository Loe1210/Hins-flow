"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { validatePackage, validateSkill, walkFiles } = require("../lib/installer");

const root = path.resolve(__dirname, "..");
const skillRoot = path.join(root, "skills", "hins-flow");

test("发行包只有一个全局 skill 和 22 个固定能力", () => {
  const skillDirectories = fs
    .readdirSync(path.join(root, "skills"), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);
  assert.deepEqual(skillDirectories, ["hins-flow"]);

  const errors = validateSkill(skillRoot);
  assert.deepEqual(errors, []);
  const sources = JSON.parse(
    fs.readFileSync(path.join(skillRoot, "references", "capability-sources.json"), "utf8"),
  );
  assert.equal(sources.capabilities.length, 22);
  assert.equal(sources.source.commit, "2ab958093e83e0ec752e6c1c5932da465bf23e0c");
});

test("发行清单完整覆盖所有运行时文件", () => {
  assert.doesNotThrow(() => validatePackage(root));
});

test("运行时文件不包含缓存、个人绝对路径或明显凭据", () => {
  const files = walkFiles(skillRoot);
  const forbiddenPath = /C:\\Users\\Administrator|Desktop\\personal web|\/Users\/[^/]+\/\.agents/i;
  const credential = /(?:token|password|passwd|secret)\s*[:=]\s*["'][^"'\s]{8,}["']/i;
  for (const file of files) {
    const relative = path.relative(skillRoot, file);
    assert.doesNotMatch(relative, /__pycache__|\.py[co]$/i);
    const content = fs.readFileSync(file, "utf8");
    assert.doesNotMatch(content, forbiddenPath, relative);
    assert.doesNotMatch(content, credential, relative);
  }
});

test("用户可见语言和单编排器约束写入主 skill", () => {
  const text = fs.readFileSync(path.join(skillRoot, "SKILL.md"), "utf8");
  assert.match(text, /\/hins-flow 继续/);
  assert.match(text, /Simplified Chinese/);
  assert.match(text, /Never require, discover, install, or invoke separate Matt\s+skills/);
  assert.doesNotMatch(text, /\$setup-matt-pocock-skills\s*->/);
});

test("主文档和 Hins 适配参考的相对链接全部有效", () => {
  const markdownFiles = [path.join(root, "README.md"), path.join(skillRoot, "SKILL.md")];
  const references = path.join(skillRoot, "references");
  for (const file of walkFiles(references)) {
    if (file.endsWith(".md") && !file.includes(`${path.sep}upstream-matt${path.sep}`)) {
      markdownFiles.push(file);
    }
  }
  for (const file of markdownFiles) {
    const text = fs.readFileSync(file, "utf8");
    for (const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1].split("#", 1)[0];
      if (!target || /^(?:https?:|mailto:)/i.test(target)) continue;
      const resolved = path.resolve(path.dirname(file), decodeURIComponent(target));
      assert.ok(fs.existsSync(resolved), `${path.relative(root, file)} -> ${target}`);
    }
  }
});

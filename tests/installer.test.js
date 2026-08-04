"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  cleanupLegacy,
  doctor,
  install,
  rollback,
  sha256File,
  sha256PortableFile,
} = require("../lib/installer");

const packageRoot = path.resolve(__dirname, "..");

function temporary(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hins-flow-installer-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

test("原子安装只管理 hins-flow，并保留无关 skill", (t) => {
  const root = temporary(t);
  const targetRoot = path.join(root, ".agents", "skills");
  const unrelated = path.join(targetRoot, "ask-matt", "SKILL.md");
  fs.mkdirSync(path.dirname(unrelated), { recursive: true });
  fs.writeFileSync(unrelated, "user-owned\n", "utf8");

  const result = install({ packageRoot, targetRoot, verifyPackage: false });

  assert.equal(result.version, "2.0.0");
  assert.ok(result.fileCount > 22);
  assert.equal(fs.readFileSync(unrelated, "utf8"), "user-owned\n");
  assert.deepEqual(
    fs.readdirSync(targetRoot).filter((name) => !name.startsWith(".hins-flow-stage-")).sort(),
    ["ask-matt", "hins-flow"],
  );

  const health = doctor({ targetRoot, runScripts: false });
  assert.equal(health.ok, true, health.errors.join("\n"));
  assert.equal(health.capabilities, 22);
  assert.equal(health.version, "2.0.0");
});

test("篡改可被 doctor 发现，重装会备份并可回滚", (t) => {
  const root = temporary(t);
  const targetRoot = path.join(root, "skills");
  install({ packageRoot, targetRoot, verifyPackage: false });
  const workflow = path.join(targetRoot, "hins-flow", "references", "workflow.md");
  fs.appendFileSync(workflow, "\n本地修改\n", "utf8");

  const broken = doctor({ targetRoot, runScripts: false });
  assert.equal(broken.ok, false);
  assert.ok(broken.errors.some((message) => message.includes("哈希不匹配")));

  const replaced = install({ packageRoot, targetRoot, verifyPackage: false });
  assert.ok(replaced.backup && fs.existsSync(replaced.backup));
  assert.equal(doctor({ targetRoot, runScripts: false }).ok, true);

  const restored = rollback({ targetRoot, apply: true });
  assert.equal(restored.restored, path.join(path.resolve(targetRoot), "hins-flow"));
  assert.match(fs.readFileSync(workflow, "utf8"), /本地修改/);
});

test("旧版清理只移动哈希完全一致的目录", (t) => {
  const root = temporary(t);
  const fakePackage = path.join(root, "package");
  const targetRoot = path.join(root, "skills");
  const exact = path.join(targetRoot, "exact", "SKILL.md");
  const modified = path.join(targetRoot, "modified", "SKILL.md");
  fs.mkdirSync(path.dirname(exact), { recursive: true });
  fs.mkdirSync(path.dirname(modified), { recursive: true });
  fs.writeFileSync(exact, "exact\n", "utf8");
  fs.writeFileSync(modified, "changed\n", "utf8");
  const manifest = {
    schemaVersion: 1,
    skills: {
      exact: { files: { "SKILL.md": sha256File(exact) } },
      modified: {
        files: {
          "SKILL.md": "0000000000000000000000000000000000000000000000000000000000000000",
        },
      },
      absent: { files: {} },
    },
  };
  const manifestPath = path.join(fakePackage, "manifests", "legacy-v1.json");
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest)}\n`, "utf8");

  const preview = cleanupLegacy({ packageRoot: fakePackage, targetRoot, apply: false });
  assert.deepEqual(preview.removable, ["exact"]);
  assert.deepEqual(preview.preserved, ["modified"]);
  assert.deepEqual(preview.absent, ["absent"]);
  assert.ok(fs.existsSync(exact));

  const applied = cleanupLegacy({ packageRoot: fakePackage, targetRoot, apply: true });
  assert.ok(applied.backup && fs.existsSync(path.join(applied.backup, "exact", "SKILL.md")));
  assert.equal(fs.existsSync(exact), false);
  assert.ok(fs.existsSync(modified));
});

test("发行来源哈希跨 LF 与 CRLF 保持一致", (t) => {
  const root = temporary(t);
  const lf = path.join(root, "lf.md");
  const crlf = path.join(root, "crlf.md");
  fs.writeFileSync(lf, "第一行\n第二行\n", "utf8");
  fs.writeFileSync(crlf, "第一行\r\n第二行\r\n", "utf8");

  assert.notEqual(sha256File(lf), sha256File(crlf));
  assert.equal(sha256PortableFile(lf), sha256PortableFile(crlf));
});

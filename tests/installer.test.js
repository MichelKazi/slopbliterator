const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  END_MARKER,
  PROVIDERS,
  START_MARKER,
  installProjectRule,
  parseArguments,
  providerDetected,
  removeMarkedBlock,
  replaceMarkedBlock,
  selectProviders,
  uninstallProjectRule,
  validateProjectRule,
  versionAtLeast,
} = require("../bin/install.js");

test("requires Node 18 or newer", () => {
  assert.equal(versionAtLeast("v17.9.1"), false);
  assert.equal(versionAtLeast("v18.0.0"), true);
  assert.equal(versionAtLeast("v21.2.0"), true);
});

test("selects detected and explicit harnesses", () => {
  const detected = new Map(PROVIDERS.map((provider) => [provider.id, provider.id === "codex"]));
  assert.deepEqual(selectProviders(parseArguments([]), detected).map((provider) => provider.id), ["codex"]);
  assert.deepEqual(
    selectProviders(parseArguments(["--only", "github-copilot", "--only", "claude"]), detected)
      .map((provider) => provider.id),
    ["copilot", "claude"],
  );
  assert.equal(selectProviders(parseArguments(["--all"]), detected).length, 6);
});

test("detects a harness by command or app", () => {
  const cursor = PROVIDERS.find((provider) => provider.id === "cursor");
  assert.equal(providerDetected(cursor, { commandExists: () => true, exists: () => false }), true);
  assert.equal(providerDetected(cursor, {
    commandExists: () => false,
    exists: (file) => file === "/Applications/Cursor.app",
    home: "/tmp/test-home",
  }), true);
});

test("detects GitHub Copilot by editor extension", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "slopbliterator-test-"));
  try {
    const extensions = path.join(root, ".vscode", "extensions");
    fs.mkdirSync(path.join(extensions, "github.copilot-1.2.3"), { recursive: true });
    const copilot = PROVIDERS.find((provider) => provider.id === "copilot");
    assert.equal(providerDetected(copilot, { commandExists: () => false, home: root }), true);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("detects Windows desktop apps", () => {
  const cursor = PROVIDERS.find((provider) => provider.id === "cursor");
  assert.equal(providerDetected(cursor, {
    commandExists: () => false,
    exists: (file) => file.split(path.sep).join("/").endsWith("Cursor/Cursor.exe"),
    home: "/test-home",
    localAppData: "/programs",
  }), true);
});

test("marked blocks are idempotent and removable", () => {
  const original = "# Existing rules\n";
  const first = replaceMarkedBlock(original);
  const second = replaceMarkedBlock(first);
  assert.equal(first, second);
  assert.match(first, new RegExp(START_MARKER));
  assert.match(first, new RegExp(END_MARKER));
  assert.equal(removeMarkedBlock(first), original);
});

test("project rules preserve existing files and uninstall cleanly", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "slopbliterator-test-"));
  try {
    const codex = PROVIDERS.find((provider) => provider.id === "codex");
    const cursor = PROVIDERS.find((provider) => provider.id === "cursor");
    fs.writeFileSync(path.join(root, "AGENTS.md"), "# Existing rules\n");

    installProjectRule(root, codex);
    installProjectRule(root, codex);
    const agents = fs.readFileSync(path.join(root, "AGENTS.md"), "utf8");
    assert.match(agents, /^# Existing rules/);
    assert.equal(agents.split(START_MARKER).length - 1, 1);

    installProjectRule(root, PROVIDERS.find((provider) => provider.id === "claude"), { dryRun: true });
    assert.equal(fs.existsSync(path.join(root, "CLAUDE.md")), false);

    installProjectRule(root, cursor);
    const cursorRule = path.join(root, cursor.rule);
    assert.match(fs.readFileSync(cursorRule, "utf8"), /alwaysApply: true/);

    assert.equal(uninstallProjectRule(root, codex), true);
    assert.equal(fs.readFileSync(path.join(root, "AGENTS.md"), "utf8"), "# Existing rules\n");
    assert.equal(uninstallProjectRule(root, cursor), true);
    assert.equal(fs.existsSync(cursorRule), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("does not replace an unowned dedicated rule without force", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "slopbliterator-test-"));
  try {
    const windsurf = PROVIDERS.find((provider) => provider.id === "windsurf");
    const file = path.join(root, windsurf.rule);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, "user rule\n");
    assert.throws(() => validateProjectRule(root, windsurf), /not owned/);
    assert.throws(() => installProjectRule(root, windsurf), /not owned/);
    installProjectRule(root, windsurf, { force: true });
    assert.doesNotMatch(fs.readFileSync(file, "utf8"), /user rule/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

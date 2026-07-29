#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const MINIMUM_NODE = [18, 0, 0];
const REPOSITORY = "MichelKazi/slopbliterator";
const PIP_SOURCE = `git+https://github.com/${REPOSITORY}.git`;
const SKILLS_PACKAGE = "skills@1.4.9";
const START_MARKER = "<!-- slopbliterator:start -->";
const END_MARKER = "<!-- slopbliterator:end -->";

const RULES = `## Slopbliterator

Apply these rules to outward prose, not code or command syntax.

- Use one name for each thing.
- State facts and actions without hedging.
- Use direct verbs and plain words.
- Put one idea in each sentence.
- Remove praise, filler, and chatty openers.
- Do not use em dashes.

Before you return outward prose, run \`slop-lint\` on it. Fix every flag. Read the installed Slopbliterator skill for the full rules.
`;

const PROVIDERS = [
  { id: "claude", name: "Claude Code", profile: "claude-code", command: "claude", rule: "CLAUDE.md" },
  { id: "codex", name: "Codex", profile: "codex", command: "codex", rule: "AGENTS.md" },
  { id: "gemini", name: "Gemini CLI", profile: "gemini-cli", command: "gemini", rule: "GEMINI.md" },
  {
    id: "cursor",
    name: "Cursor",
    profile: "cursor",
    command: "cursor",
    apps: ["Cursor.app"],
    windowsApps: ["Cursor/Cursor.exe", "cursor/Cursor.exe"],
    rule: ".cursor/rules/slopbliterator.mdc",
    frontmatter: "---\ndescription: Check outward prose with Slopbliterator\nalwaysApply: true\n---\n\n",
  },
  {
    id: "windsurf",
    name: "Windsurf",
    profile: "windsurf",
    command: "windsurf",
    apps: ["Windsurf.app"],
    windowsApps: ["Windsurf/Windsurf.exe", "windsurf/Windsurf.exe"],
    rule: ".windsurf/rules/slopbliterator.md",
  },
  {
    id: "copilot",
    aliases: ["github-copilot"],
    name: "GitHub Copilot",
    profile: "github-copilot",
    command: "copilot",
    extension: "github.copilot",
    rule: ".github/instructions/slopbliterator.instructions.md",
    frontmatter: "---\napplyTo: \"**\"\n---\n\n",
  },
];

function versionAtLeast(actual, minimum = MINIMUM_NODE) {
  const parts = actual.replace(/^v/, "").split(".").map(Number);
  for (let index = 0; index < minimum.length; index += 1) {
    if ((parts[index] || 0) > minimum[index]) return true;
    if ((parts[index] || 0) < minimum[index]) return false;
  }
  return true;
}

function commandExists(command) {
  const probe = process.platform === "win32" ? "where" : "command";
  const args = process.platform === "win32" ? [command] : ["-v", command];
  return spawnSync(probe, args, { stdio: "ignore", shell: process.platform !== "win32" }).status === 0;
}

function extensionExists(prefix, home = os.homedir()) {
  const roots = [
    path.join(home, ".vscode", "extensions"),
    path.join(home, ".cursor", "extensions"),
    path.join(home, ".windsurf", "extensions"),
  ];
  return roots.some((root) => {
    try {
      return fs.readdirSync(root).some((entry) => entry.startsWith(prefix));
    } catch {
      return false;
    }
  });
}

function providerDetected(provider, options = {}) {
  const hasCommand = options.commandExists || commandExists;
  const exists = options.exists || fs.existsSync;
  const home = options.home || os.homedir();
  if (hasCommand(provider.command)) return true;
  if (provider.extension && extensionExists(provider.extension, home)) return true;
  const macApp = (provider.apps || []).some((app) =>
    [path.join("/Applications", app), path.join(home, "Applications", app)].some(exists),
  );
  const localAppData = options.localAppData || process.env.LOCALAPPDATA;
  const windowsApp = localAppData && (provider.windowsApps || []).some((app) => exists(path.join(localAppData, app)));
  return Boolean(macApp || windowsApp);
}

function parseArguments(argv) {
  const options = {
    dryRun: false,
    force: false,
    help: false,
    list: false,
    all: false,
    only: [],
    uninstall: false,
    withInit: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--dry-run") options.dryRun = true;
    else if (argument === "--force") options.force = true;
    else if (argument === "--help" || argument === "-h") options.help = true;
    else if (argument === "--list") options.list = true;
    else if (argument === "--all") options.all = true;
    else if (argument === "--uninstall") options.uninstall = true;
    else if (argument === "--with-init") options.withInit = true;
    else if (argument === "--only") {
      index += 1;
      if (!argv[index]) throw new Error("--only requires a harness name");
      options.only.push(argv[index]);
    } else {
      throw new Error(`Unknown option: ${argument}`);
    }
  }
  return options;
}

function selectProviders(options, detected) {
  if (options.all) return [...PROVIDERS];
  if (options.only.length === 0) return PROVIDERS.filter((provider) => detected.get(provider.id));
  return options.only.map((requested) => {
    const provider = PROVIDERS.find(
      (candidate) => candidate.id === requested || (candidate.aliases || []).includes(requested),
    );
    if (!provider) throw new Error(`Unknown harness: ${requested}`);
    return provider;
  }).filter((provider, index, values) => values.findIndex((item) => item.id === provider.id) === index);
}

function markedRules() {
  return `${START_MARKER}\n${RULES.trim()}\n${END_MARKER}`;
}

function replaceMarkedBlock(content, block = markedRules()) {
  const start = content.indexOf(START_MARKER);
  const end = content.indexOf(END_MARKER);
  if (start === -1 && end === -1) {
    const separator = content.length > 0 && !content.endsWith("\n\n") ? (content.endsWith("\n") ? "\n" : "\n\n") : "";
    return `${content}${separator}${block}\n`;
  }
  if (start === -1 || end === -1 || end < start) throw new Error("Malformed Slopbliterator rule markers");
  return `${content.slice(0, start)}${block}${content.slice(end + END_MARKER.length)}`;
}

function removeMarkedBlock(content) {
  const start = content.indexOf(START_MARKER);
  const end = content.indexOf(END_MARKER);
  if (start === -1 && end === -1) return content;
  if (start === -1 || end === -1 || end < start) throw new Error("Malformed Slopbliterator rule markers");
  const before = content.slice(0, start).replace(/\n+$/, "");
  const after = content.slice(end + END_MARKER.length).replace(/^\n+/, "");
  if (!before) return after;
  if (!after) return `${before}\n`;
  return `${before}\n\n${after}`;
}

function writeAtomic(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.slopbliterator-${process.pid}`;
  fs.writeFileSync(temporary, content);
  fs.renameSync(temporary, file);
}

function validateProjectRule(root, provider, options = {}) {
  if (!provider.rule.includes("/")) return;
  const file = path.join(root, provider.rule);
  if (!fs.existsSync(file) || options.force) return;
  const current = fs.readFileSync(file, "utf8");
  if (!current.includes(START_MARKER)) {
    throw new Error(`${provider.rule} exists and is not owned by Slopbliterator. Use --force to replace it.`);
  }
}

function installProjectRule(root, provider, options = {}) {
  const file = path.join(root, provider.rule);
  const exists = fs.existsSync(file);
  const current = exists ? fs.readFileSync(file, "utf8") : "";
  const dedicated = provider.rule.includes("/");
  const prefix = provider.frontmatter || "";
  validateProjectRule(root, provider, options);
  const next = dedicated && (!exists || !current.includes(START_MARKER))
    ? `${prefix}${markedRules()}\n`
    : replaceMarkedBlock(current);
  if (!options.dryRun) writeAtomic(file, next);
  return provider.rule;
}

function uninstallProjectRule(root, provider, options = {}) {
  const file = path.join(root, provider.rule);
  if (!fs.existsSync(file)) return false;
  const current = fs.readFileSync(file, "utf8");
  if (!current.includes(START_MARKER)) return false;
  const next = removeMarkedBlock(current);
  const emptyFrontmatter = provider.frontmatter && next.trim() === provider.frontmatter.trim();
  if (!options.dryRun) {
    if (!next.trim() || emptyFrontmatter) fs.unlinkSync(file);
    else writeAtomic(file, next);
  }
  return true;
}

function formatCommand(command, args) {
  return [command, ...args].map((part) => (/^[A-Za-z0-9_./:+@=-]+$/.test(part) ? part : JSON.stringify(part))).join(" ");
}

function runCommand(command, args, options = {}) {
  console.log(`${options.dryRun ? "Would run" : "Run"}: ${formatCommand(command, args)}`);
  if (options.dryRun) return;
  const result = spawnSync(command, args, { stdio: "inherit", shell: process.platform === "win32" });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`${command} failed with exit code ${result.status}`);
}

function printHelp() {
  console.log(`Install Slopbliterator for detected AI coding harnesses.

Usage: slopbliterator [options]

  --list              Show harness detection and exit
  --only <harness>    Install one harness. Repeat for more harnesses
  --all               Install all six supported harnesses
  --with-init         Add always-on rules to the current project
  --force             Replace the linter install and owned rule files
  --dry-run           Print actions without changing files
  --uninstall         Remove selected global installs and project rules
  --help              Show this help

Harnesses: claude, codex, gemini, cursor, windsurf, copilot`);
}

function main(argv = process.argv.slice(2)) {
  if (!versionAtLeast(process.version)) {
    throw new Error(`Node.js 18 or newer is required. Found ${process.version}.`);
  }
  const options = parseArguments(argv);
  if (options.help) return printHelp();
  const detected = new Map(PROVIDERS.map((provider) => [provider.id, providerDetected(provider)]));
  if (options.list) {
    for (const provider of PROVIDERS) {
      console.log(`${provider.id.padEnd(9)} ${detected.get(provider.id) ? "detected" : "not detected"}  ${provider.name}`);
    }
    return;
  }
  const selected = selectProviders(options, detected);
  if (selected.length === 0) {
    throw new Error("No supported harness was detected. Use --list, --only <harness>, or --all.");
  }
  const profiles = selected.map((provider) => provider.profile);
  console.log(`Harnesses: ${selected.map((provider) => provider.name).join(", ")}`);

  if (options.withInit && !options.uninstall) {
    for (const provider of selected) validateProjectRule(process.cwd(), provider, options);
  }

  if (options.uninstall) {
    runCommand("npx", ["-y", SKILLS_PACKAGE, "remove", "slopbliterator", "-g", "-a", ...profiles, "-y"], options);
    runCommand("pipx", ["uninstall", "slopbliterator"], options);
    for (const provider of selected) {
      if (uninstallProjectRule(process.cwd(), provider, options)) console.log(`Removed project rule: ${provider.rule}`);
    }
    return;
  }

  for (const prerequisite of ["npx", "pipx"]) {
    if (!options.dryRun && !commandExists(prerequisite)) {
      throw new Error(`${prerequisite} is required and was not found on PATH.`);
    }
  }
  if (options.force || !commandExists("slop-lint") || !commandExists("slop-substance")) {
    const pipxArgs = ["install"];
    if (options.force) pipxArgs.push("--force");
    pipxArgs.push(PIP_SOURCE);
    runCommand("pipx", pipxArgs, options);
  } else {
    console.log("Linter commands are already installed. Use --force to replace them.");
  }
  runCommand(
    "npx",
    ["-y", SKILLS_PACKAGE, "add", REPOSITORY, "--skill", "slopbliterator", "-g", "-a", ...profiles, "--copy", "-y"],
    options,
  );
  if (options.withInit) {
    for (const provider of selected) {
      console.log(`Project rule: ${installProjectRule(process.cwd(), provider, options)}`);
    }
  }
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`slopbliterator: ${error.message}`);
    process.exitCode = 1;
  }
}

module.exports = {
  END_MARKER,
  PROVIDERS,
  RULES,
  START_MARKER,
  installProjectRule,
  main,
  parseArguments,
  providerDetected,
  removeMarkedBlock,
  replaceMarkedBlock,
  selectProviders,
  uninstallProjectRule,
  validateProjectRule,
  versionAtLeast,
};

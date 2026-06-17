#!/usr/bin/env node
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const webRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(webRoot, "..");
const isWindows = os.platform() === "win32";

const pythonCandidates = () => {
  const candidates = [];
  if (process.env.PYTHON) candidates.push(process.env.PYTHON);
  candidates.push(
    path.join(repoRoot, ".venv", isWindows ? "Scripts/python.exe" : "bin/python"),
    "python3.13",
    "python3.12",
    "python3.11",
    "python3",
    "python",
  );
  return candidates;
};

const runPython = (python, args, options = {}) =>
  spawnSync(python, args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: options.stdio || "pipe",
    env: process.env,
  });

const usablePython = () => {
  for (const candidate of pythonCandidates()) {
    if (candidate.includes(path.sep) && !fs.existsSync(candidate)) continue;
    const probe = runPython(candidate, [
      "-c",
      "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')",
    ]);
    if (probe.status !== 0) continue;
    const version = String(probe.stdout || "").trim();
    const [major, minor] = version.split(".").map((part) => Number.parseInt(part, 10));
    if (major > 3 || (major === 3 && minor >= 11)) {
      return { command: candidate, version };
    }
    console.warn(`[backend:build] skip ${candidate}: Python ${version} is below 3.11`);
  }
  throw new Error("No usable Python >= 3.11 found. Create .venv with Python 3.11+ or set PYTHON=/path/to/python.");
};

const ensurePyInstaller = (python) => {
  const probe = runPython(python, ["-c", "import PyInstaller"]);
  if (probe.status === 0) return;
  throw new Error(
    [
      `PyInstaller is not installed for ${python}.`,
      "Install build dependencies with:",
      "  python -m pip install -r requirements-build.txt",
      "or, for the local venv:",
      "  .venv/bin/python -m pip install -r requirements-build.txt",
    ].join("\n"),
  );
};

try {
  const python = usablePython();
  ensurePyInstaller(python.command);
  console.log(`[backend:build] using ${python.command} (Python ${python.version})`);
  const result = runPython(
    python.command,
    [
      "-m",
      "PyInstaller",
      "MingSalvageBackend.spec",
      "--noconfirm",
      "--distpath",
      "build/backend-dist",
      "--workpath",
      "build/backend-work",
    ],
    { stdio: "inherit" },
  );
  process.exit(result.status ?? 1);
} catch (error) {
  console.error(`[backend:build] ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
}

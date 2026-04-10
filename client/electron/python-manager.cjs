const { spawn, execFile } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

let pythonProcess = null;
const API_PORT = 9800;
const HEALTH_URL = `http://127.0.0.1:${API_PORT}/health`;

function getEmbeddedPython() {
  return path.join(process.resourcesPath || path.join(__dirname, ".."), "resources", "python", "python.exe");
}

function getBackendDir() {
  return path.join(process.resourcesPath || path.join(__dirname, ".."), "resources", "backend");
}

async function ensureVenv() {
  const backendDir = getBackendDir();
  const venvDir = path.join(backendDir, ".venv");
  const venvPython = path.join(venvDir, "Scripts", "python.exe");

  if (fs.existsSync(venvPython)) return venvPython;

  const embeddedPython = getEmbeddedPython();
  if (!fs.existsSync(embeddedPython)) {
    console.warn("[PythonManager] Embedded Python not found, falling back to system Python");
    return null;
  }

  console.log("[PythonManager] Creating venv with embedded Python...");
  await new Promise((resolve, reject) => {
    execFile(embeddedPython, ["-m", "venv", venvDir], (err) => {
      err ? reject(err) : resolve();
    });
  });

  const reqFile = path.join(backendDir, "requirements.txt");
  if (fs.existsSync(reqFile)) {
    console.log("[PythonManager] Installing dependencies...");
    await new Promise((resolve, reject) => {
      execFile(venvPython, ["-m", "pip", "install", "-r", reqFile, "--quiet"], (err) => {
        err ? reject(err) : resolve();
      });
    });
  }

  return venvPython;
}

function startPythonBackend() {
  return new Promise((resolve, reject) => {
    const isDev = !!(
      process.env.VITE_DEV_SERVER_URL || process.env.NODE_ENV === "development"
    );

    let cmd;
    let args;
    let cwd;
    let shell = false;

    if (isDev) {
      cwd = path.resolve(__dirname, "../../");
      const venvPy =
        process.platform === "win32"
          ? path.join(cwd, ".venv", "Scripts", "python.exe")
          : path.join(cwd, ".venv", "bin", "python");
      if (fs.existsSync(venvPy)) {
        cmd = venvPy;
        args = ["-m", "agentcrewchat.api.server"];
      } else {
        cmd = "uv";
        args = ["run", "python", "-m", "agentcrewchat.api.server"];
        shell = process.platform === "win32";
      }
    } else {
      // 生产模式：优先使用嵌入式 Python + venv，否则回退到打包的可执行文件
      const backendDir = getBackendDir();
      const venvPython = path.join(backendDir, ".venv", "Scripts", "python.exe");

      if (fs.existsSync(venvPython)) {
        cmd = venvPython;
        args = ["-m", "agentcrewchat.api.server"];
        cwd = backendDir;
      } else {
        const exeName =
          process.platform === "win32" ? "agentcrewchat-api.exe" : "agentcrewchat-api";
        cmd = path.join(backendDir, exeName);
        args = [];
        cwd = path.dirname(cmd);
      }
    }

    // 数据目录：始终使用软件安装目录（cwd）
    process.env.AGENTCREWCHAT_ROOT = cwd;

    console.log(`[PythonManager] Starting: ${cmd} ${args.join(" ")} (cwd: ${cwd})`);

    pythonProcess = spawn(cmd, args, {
      cwd,
      shell,
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, AGENTCREWCHAT_ROOT: cwd },
    });

    let resolved = false;

    function tryResolveUvicorn(chunk) {
      const text = chunk.toString();
      if (!resolved && text.includes("Uvicorn running")) {
        resolved = true;
        resolve();
      }
    }

    pythonProcess.stdout.on("data", (data) => {
      console.log("[Python:stdout]", data.toString().trim());
      tryResolveUvicorn(data);
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error("[Python:stderr]", data.toString().trim());
      tryResolveUvicorn(data);
    });

    pythonProcess.on("error", (err) => {
      console.error("[PythonManager] Spawn error:", err.message);
      if (!resolved) {
        resolved = true;
        reject(err);
      }
    });

    pythonProcess.on("exit", (code) => {
      console.log(`[PythonManager] Process exited with code ${code}`);
      pythonProcess = null;
      if (!resolved) {
        resolved = true;
        reject(new Error(`Python exited with code ${code}`));
      }
    });

    setTimeout(() => {
      if (!resolved) {
        resolved = true;
        resolve();
      }
    }, 10000);
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    console.log("[PythonManager] Stopping Python backend...");
    pythonProcess.kill();
    pythonProcess = null;
  }
}

function waitForBackend(maxWaitMs = 15000, intervalMs = 500) {
  return new Promise((resolve) => {
    const start = Date.now();

    function check() {
      if (Date.now() - start > maxWaitMs) {
        resolve(false);
        return;
      }

      const req = http.get(HEALTH_URL, (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          setTimeout(check, intervalMs);
        }
      });

      req.on("error", () => {
        setTimeout(check, intervalMs);
      });

      req.setTimeout(2000, () => {
        req.destroy();
        setTimeout(check, intervalMs);
      });
    }

    check();
  });
}

module.exports = { startPythonBackend, stopPythonBackend, waitForBackend, ensureVenv };

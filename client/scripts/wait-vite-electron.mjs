import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const clientRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const AGENTCREWCHAT_VITE_PORT = 25527;

function checkPort(port) {
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:${port}/`, (res) => {
      resolve(res.statusCode === 200 || res.statusCode === 304);
      res.resume();
    });
    req.on("error", () => resolve(false));
    req.setTimeout(600, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function main() {
  let ok = false;
  for (let i = 0; i < 200; i++) {
    if (await checkPort(AGENTCREWCHAT_VITE_PORT)) {
      ok = true;
      break;
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  if (!ok) {
    console.error(
      `[wait-vite] 未在 ${AGENTCREWCHAT_VITE_PORT} 检测到本项目的 Vite（请确认未改 vite 端口，且未被占用）`,
    );
    process.exit(1);
  }
  const env = {
    ...process.env,
    VITE_DEV_SERVER_URL: `http://localhost:${AGENTCREWCHAT_VITE_PORT}`,
  };
  const electronBin = require("electron");
  spawn(electronBin, ["."], {
    cwd: clientRoot,
    env,
    stdio: "inherit",
  });
}

main();

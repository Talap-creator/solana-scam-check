/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");
const standaloneRoot = path.join(projectRoot, ".next", "standalone");
const standaloneNextRoot = path.join(standaloneRoot, ".next");
const sourceStaticRoot = path.join(projectRoot, ".next", "static");
const targetStaticRoot = path.join(standaloneNextRoot, "static");
const sourcePublicRoot = path.join(projectRoot, "public");
const targetPublicRoot = path.join(standaloneRoot, "public");
const serverEntry = path.join(standaloneRoot, "server.js");

function ensureDirectory(targetPath) {
  fs.mkdirSync(targetPath, { recursive: true });
}

function copyDirectory(sourcePath, targetPath) {
  if (!fs.existsSync(sourcePath)) {
    return;
  }

  ensureDirectory(targetPath);

  for (const entry of fs.readdirSync(sourcePath, { withFileTypes: true })) {
    const sourceEntryPath = path.join(sourcePath, entry.name);
    const targetEntryPath = path.join(targetPath, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(sourceEntryPath, targetEntryPath);
      continue;
    }

    fs.copyFileSync(sourceEntryPath, targetEntryPath);
  }
}

if (!fs.existsSync(serverEntry)) {
  console.error("Standalone build is missing. Run `npm run build` first.");
  process.exit(1);
}

copyDirectory(sourceStaticRoot, targetStaticRoot);
copyDirectory(sourcePublicRoot, targetPublicRoot);

require(serverEntry);

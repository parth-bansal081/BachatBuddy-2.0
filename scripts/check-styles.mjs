#!/usr/bin/env node
import { readFileSync, readdirSync, statSync } from "fs";
import { join, extname } from "path";

const pathsToScan = [
  "src/components/khata",
  "src/pages/Preview.tsx",
  "src/pages/Dashboard.tsx",
  "src/pages/Policy.tsx",
  "src/lib/api.ts",
];

const forbiddenPatterns = [
  { pattern: /gradient/i, name: "gradient" },
  { pattern: /backdrop-blur/i, name: "backdrop-blur" },
  { pattern: /blur-/i, name: "blur-" },
  { pattern: /glow/i, name: "glow" },
  { pattern: /sparkle/i, name: "sparkle" },
  { pattern: /bg-clip-text/i, name: "bg-clip-text" },
  { pattern: /PieChart/i, name: "PieChart" },
  { pattern: /<Pie/i, name: "<Pie" },
  { pattern: /#[0-9a-fA-F]{3,8}\b/, name: "#hex color" },
  { pattern: /\p{Extended_Pictographic}/u, name: "emoji" },
];

function collectFiles(dir, fileList = []) {
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      collectFiles(fullPath, fileList);
    } else if (entry.isFile() && (extname(entry.name) === ".tsx" || extname(entry.name) === ".ts")) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

let allFiles = [];
for (const p of pathsToScan) {
  const s = statSync(p);
  if (s.isDirectory()) {
    allFiles = allFiles.concat(collectFiles(p));
  } else {
    allFiles.push(p);
  }
}

let hasError = false;
for (const file of allFiles) {
  const content = readFileSync(file, "utf-8");
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const { pattern, name } of forbiddenPatterns) {
      if (pattern.test(line)) {
        console.error(`${file}:${i + 1}: forbidden style "${name}" found`);
        hasError = true;
      }
    }
  }
}

if (hasError) {
  process.exit(1);
} else {
  console.log("OK");
}
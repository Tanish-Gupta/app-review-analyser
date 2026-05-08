import fs from "fs";
import path from "path";

/** Repo root that contains `phase1_ingest/`, `data/`, etc. */
export function getMonorepoRoot(): string {
  const cwd = process.cwd();
  if (path.basename(cwd) === "phase6_ui") {
    return path.resolve(cwd, "..");
  }
  if (fs.existsSync(path.join(cwd, "phase1_ingest"))) {
    return cwd;
  }
  const parent = path.resolve(cwd, "..");
  if (fs.existsSync(path.join(parent, "phase1_ingest"))) {
    return parent;
  }
  return parent;
}

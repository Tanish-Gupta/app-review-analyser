import fs from "fs";
import path from "path";
import { artifactPathsForRun } from "./pulses";
import { getMonorepoRoot } from "./repoRoot";

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

export type SessionCache = {
  runId: string;
  weeks: number;
  completedAt: string;
};

function sessionPath(): string {
  return path.join(getMonorepoRoot(), "data", "cache", "session.json");
}

/** Return cached run id if same weeks, younger than 24h, and artifacts exist. */
export function getCachedRunIdForWeeks(weeks: number): string | null {
  try {
    const p = sessionPath();
    if (!fs.existsSync(p)) return null;
    const raw = fs.readFileSync(p, "utf8");
    const j = JSON.parse(raw) as SessionCache;
    if (j.weeks !== weeks || !j.runId || !j.completedAt) return null;
    const age = Date.now() - new Date(j.completedAt).getTime();
    if (age < 0 || age > CACHE_TTL_MS) return null;
    const arts = artifactPathsForRun(j.runId);
    if (!arts) return null;
    return j.runId;
  } catch {
    return null;
  }
}

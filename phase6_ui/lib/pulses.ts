import fs from "fs";
import path from "path";
import type { PulseData } from "./types";
import { getMonorepoRoot } from "./repoRoot";

/** @deprecated use getMonorepoRoot */
export function getRepoRoot(): string {
  return getMonorepoRoot();
}

const SAMPLE_DIR = path.join(process.cwd(), "public", "sample");

export function listPulseRunIds(): string[] {
  const outDir = path.join(getRepoRoot(), "data", "output");
  if (!fs.existsSync(outDir)) return [];
  return fs
    .readdirSync(outDir)
    .filter((f) => /^pulse_.+\.json$/.test(f))
    .map((f) => f.replace(/^pulse_/, "").replace(/\.json$/, ""))
    .sort()
    .reverse();
}

function readPulseFile(filePath: string): PulseData | null {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    return JSON.parse(raw) as PulseData;
  } catch {
    return null;
  }
}

export function readPulseByRunId(runId: string): PulseData | null {
  if (runId === "sample") {
    const sample = path.join(SAMPLE_DIR, "pulse.json");
    return readPulseFile(sample);
  }
  const p = path.join(getRepoRoot(), "data", "output", `pulse_${runId}.json`);
  return readPulseFile(p);
}

export type PulseBundle = { runId: string; pulse: PulseData };

export function readLatestPulse(): PulseBundle | null {
  const ids = listPulseRunIds();
  if (ids.length > 0) {
    const pulse = readPulseByRunId(ids[0]);
    if (pulse) return { runId: ids[0], pulse };
  }
  const sample = readPulseByRunId("sample");
  if (sample) return { runId: "sample", pulse: sample };
  return null;
}

export function artifactPathsForRun(runId: string): {
  json: string;
  md: string;
  html: string;
} | null {
  if (runId === "sample") {
    const j = path.join(SAMPLE_DIR, "pulse.json");
    const m = path.join(SAMPLE_DIR, "pulse.md");
    const h = path.join(SAMPLE_DIR, "pulse.html");
    if ([j, m, h].every((p) => fs.existsSync(p))) {
      return { json: j, md: m, html: h };
    }
    return null;
  }
  const root = path.join(getRepoRoot(), "data", "output");
  const json = path.join(root, `pulse_${runId}.json`);
  const md = path.join(root, `pulse_${runId}.md`);
  const html = path.join(root, `pulse_${runId}.html`);
  if ([json, md, html].every((p) => fs.existsSync(p))) {
    return { json, md, html };
  }
  return null;
}

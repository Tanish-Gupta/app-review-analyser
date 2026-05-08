import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { getMonorepoRoot } from "./repoRoot";

export type PipelineResult = {
  ok: boolean;
  runId?: string;
  stderr: string;
};

/** PyPI package name when it differs from the import/module name. */
const PIP_NAME_OVERRIDES: Record<string, string> = {
  google_play_scraper: "google-play-scraper",
};

/** Short UI hint derived from orchestrator stderr (Groq vs ingest vs missing deps). */
export function pipelineFailureHint(stderr: string): string {
  const s = stderr.toLowerCase();

  const modMatch = stderr.match(/No module named ['"]([^'"]+)['"]/);
  if (modMatch) {
    const mod = modMatch[1];
    const pip = PIP_NAME_OVERRIDES[mod] ?? mod;
    return `Pipeline failed: missing Python package for module \`${mod}\`. From repo root run: \`python3 -m pip install ${pip}\` (or install everything with \`python3 -m pip install -r requirements.txt\`).`;
  }

  // Do not match bare "groq" — tracebacks always include groq_client.py and mislead users.

  const groqHttp = stderr.match(/Groq HTTP (\d{3})/i);
  if (groqHttp) {
    const code = groqHttp[1];
    if (code === "429") {
      return "Pipeline failed: Groq rate limit or daily token quota (HTTP 429). Wait for reset, lower `PHASE3_MAX_ROWS`, or upgrade your plan — see detail below.";
    }
    if (code === "401" || code === "403") {
      return "Pipeline failed: Groq rejected the key (HTTP " + code + "). Check `GROQ_API_KEY` in repo-root `.env`.";
    }
    return `Pipeline failed: Groq API returned HTTP ${code}. See detail below (model name, outage, or billing).`;
  }

  if (s.includes("rate_limit_exceeded") || s.includes("tokens per day")) {
    return "Pipeline failed: Groq rate limit or daily quota. Wait, reduce `PHASE3_MAX_ROWS`, or upgrade — see detail below.";
  }

  if (
    s.includes("invalid_api_key") ||
    s.includes("invalid api key") ||
    s.includes("incorrect api key")
  ) {
    return "Pipeline failed: check `GROQ_API_KEY` in repo-root `.env` and that the key is valid.";
  }

  if (s.includes("groqerror") || s.includes("groq request failed")) {
    return "Pipeline failed during Groq requests. Open the detail below; often quota/rate limit, not a missing key.";
  }

  return "Pipeline failed (ingest → pulse). Check Python dependencies, `GROQ_API_KEY`, network, and the detail below.";
}

/** Run ``python -m orchestrator.run_pipeline``; reads ``data/cache/session.json`` for run id. */
export function runPhasesOneThroughFour(opts: {
  weeks: number;
}): Promise<PipelineResult> {
  const root = getMonorepoRoot();
  return new Promise((resolve) => {
    const proc = spawn(
      "python3",
      ["-m", "orchestrator.run_pipeline", "--weeks", String(opts.weeks)],
      {
        cwd: root,
        env: { ...process.env },
        stdio: ["ignore", "pipe", "pipe"],
      }
    );
    let err = "";
    proc.stderr?.on("data", (c) => {
      err += c.toString();
    });
    proc.stdout?.on("data", () => {
      /* phases are noisy */
    });
    proc.on("close", (code) => {
      if (code !== 0) {
        resolve({ ok: false, stderr: err.slice(-8000) });
        return;
      }
      try {
        const sessionPath = path.join(root, "data", "cache", "session.json");
        const raw = fs.readFileSync(sessionPath, "utf8");
        const j = JSON.parse(raw) as { runId: string };
        if (!j.runId) {
          resolve({ ok: false, stderr: "session.json missing runId" });
          return;
        }
        resolve({ ok: true, runId: j.runId, stderr: err });
      } catch (e) {
        resolve({
          ok: false,
          stderr: `${err}\n${String(e)}`,
        });
      }
    });
    proc.on("error", (e) => {
      resolve({ ok: false, stderr: String(e) });
    });
  });
}

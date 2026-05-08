import { spawn } from "child_process";
import { NextResponse } from "next/server";
import { getCachedRunIdForWeeks } from "@/lib/pulseCache";
import { artifactPathsForRun } from "@/lib/pulses";
import {
  railwayBackendConfigured,
  railwayBackendMisconfigured,
  railwayPost,
} from "@/lib/railwayBackend";
import {
  pipelineFailureHint,
  runPhasesOneThroughFour,
} from "@/lib/runPipeline";
import { getMonorepoRoot } from "@/lib/repoRoot";

type Body = {
  weeks?: number;
  recipient?: string;
  recipientName?: string;
  mode?: "draft" | "send";
  /** When true, skip 24h cache and re-fetch reviews + rebuild pulse. */
  forceRefresh?: boolean;
};

export async function POST(req: Request) {
  const body = (await req.json()) as Body;
  const weeks = Math.min(26, Math.max(12, Number(body.weeks ?? 12)));
  const recipient = body.recipient?.trim();
  const recipientName = body.recipientName?.trim();
  const mode = body.mode === "draft" ? "draft" : "send";
  const forceRefresh = Boolean(body.forceRefresh);

  if (!recipient) {
    return NextResponse.json({ error: "recipient is required" }, { status: 400 });
  }

  if (railwayBackendMisconfigured()) {
    return NextResponse.json(
      {
        error:
          "RAILWAY_API_URL is set but RAILWAY_API_SECRET is missing. Add both for the Railway API.",
      },
      { status: 503 },
    );
  }

  if (railwayBackendConfigured()) {
    const res = await railwayPost("/v1/email", {
      weeks,
      recipient,
      recipientName: recipientName ?? undefined,
      mode,
      forceRefresh,
    });
    const data = (await res.json().catch(() => ({}))) as {
      ok?: boolean;
      error?: string;
      detail?: string;
      message?: string;
      runId?: string;
      usedCache?: boolean;
    };
    if (!res.ok) {
      return NextResponse.json(
        {
          error: data.error ?? "Railway email pipeline failed",
          detail: data.detail ?? "",
        },
        { status: res.status >= 400 && res.status < 600 ? res.status : 500 },
      );
    }
    return NextResponse.json({
      ok: true,
      runId: data.runId,
      usedCache: data.usedCache,
      message: data.message,
    });
  }

  if (process.env.VERCEL === "1") {
    return NextResponse.json(
      {
        error:
          "Email + pipeline need the Railway API. Set RAILWAY_API_URL + RAILWAY_API_SECRET, or run locally.",
      },
      { status: 501 },
    );
  }

  let runId: string | undefined;
  let usedCache = false;

  if (!forceRefresh) {
    const cached = getCachedRunIdForWeeks(weeks);
    if (cached) {
      runId = cached;
      usedCache = true;
    }
  }

  if (!runId) {
    const pipe = await runPhasesOneThroughFour({ weeks });
    if (!pipe.ok || !pipe.runId) {
      return NextResponse.json(
        {
          error: pipelineFailureHint(pipe.stderr),
          detail: pipe.stderr.slice(-2000),
        },
        { status: 500 },
      );
    }
    runId = pipe.runId;
  }

  const artifacts = artifactPathsForRun(runId);
  if (!artifacts) {
    return NextResponse.json(
      { error: `Pulse artifacts missing for run ${runId}` },
      { status: 404 },
    );
  }

  const repoRoot = getMonorepoRoot();
  const args = [
    "-m",
    "phase5_email.run",
    "--pulse-json",
    artifacts.json,
    "--pulse-md",
    artifacts.md,
    "--pulse-html",
    artifacts.html,
    "--mode",
    mode,
    "--recipient",
    recipient,
  ];
  if (recipientName) {
    args.push("--recipient-name", recipientName);
  }

  const code: number = await new Promise((resolve) => {
    const proc = spawn("python3", args, {
      cwd: repoRoot,
      env: { ...process.env },
      stdio: ["ignore", "pipe", "pipe"],
    });
    proc.stderr?.on("data", () => {});
    proc.on("close", (c) => resolve(c ?? 1));
    proc.on("error", () => resolve(1));
  });

  if (code !== 0) {
    return NextResponse.json(
      {
        error:
          "phase5_email.run failed. Check SMTP / Resend settings in .env at repo root.",
      },
      { status: 500 },
    );
  }

  const cacheHint = usedCache
    ? "Reused pulse from cache (same week range, completed within the last 24 hours)."
    : "Built fresh from latest Play Store data.";

  return NextResponse.json({
    ok: true,
    runId,
    usedCache,
    message:
      mode === "draft"
        ? `Draft saved · ${runId}. ${cacheHint}`
        : `Sent · ${runId}. ${cacheHint}`,
  });
}

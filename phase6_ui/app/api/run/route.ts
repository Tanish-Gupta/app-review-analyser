import { NextResponse } from "next/server";
import {
  railwayBackendConfigured,
  railwayBackendMisconfigured,
  railwayPost,
} from "@/lib/railwayBackend";
import {
  pipelineFailureHint,
  runPhasesOneThroughFour,
} from "@/lib/runPipeline";

/** Run phases 1–4 only (no email). Used by “Generate pulse”. */
export async function POST(req: Request) {
  let weeks = 12;
  try {
    const b = await req.json();
    weeks = Math.min(26, Math.max(12, Number(b.weeks ?? 12)));
  } catch {
    /* default weeks */
  }

  if (railwayBackendMisconfigured()) {
    return NextResponse.json(
      {
        error:
          "RAILWAY_API_URL is set but RAILWAY_API_SECRET is missing. Add both to run the pipeline from the cloud API.",
      },
      { status: 503 },
    );
  }

  if (railwayBackendConfigured()) {
    const res = await railwayPost("/v1/pipeline/run", { weeks });
    const data = (await res.json().catch(() => ({}))) as {
      error?: string;
      detail?: string;
      runId?: string;
      hint?: string;
    };
    if (!res.ok) {
      return NextResponse.json(
        {
          error: data.error ?? "Railway pipeline failed",
          detail: data.detail ?? "",
        },
        { status: res.status >= 400 && res.status < 600 ? res.status : 500 },
      );
    }
    return NextResponse.json({
      runId: data.runId,
      weeks,
      hint: data.hint ?? "Pulse written to data/output/. Refresh the home page to view it.",
    });
  }

  if (process.env.VERCEL === "1") {
    return NextResponse.json(
      {
        error:
          "Pipeline not configured. Set RAILWAY_API_URL + RAILWAY_API_SECRET for the Railway API, or run locally.",
      },
      { status: 501 },
    );
  }

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

  return NextResponse.json({
    runId: pipe.runId,
    weeks,
    hint: "Pulse written to data/output/. Refresh the home page to view it.",
  });
}

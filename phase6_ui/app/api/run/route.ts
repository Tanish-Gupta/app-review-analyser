import { NextResponse } from "next/server";
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

  if (process.env.VERCEL === "1") {
    return NextResponse.json(
      { error: "Pipeline runs locally via Python on this repo." },
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

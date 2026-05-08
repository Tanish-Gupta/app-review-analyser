import Link from "next/link";
import { RunProgressClient } from "./run-progress";

type Props = { params: { runId: string } };

export default function RunProgressPage({ params }: Props) {
  const runId = decodeURIComponent(params.runId);

  return (
    <div className="mx-auto max-w-lg space-y-8">
      <Link
        href="/"
        className="inline-block font-dm text-sm text-[#00ffc8]/85 hover:text-[#00ffc8]"
      >
        ← Dashboard
      </Link>

      <div className="space-y-3">
        <h1 className="font-syne text-3xl font-bold leading-tight tracking-tight text-white md:text-4xl">
          Running pipeline
        </h1>
        <p className="font-dm text-sm leading-relaxed text-white/45 md:text-base">
          Run <span className="font-medium text-white/70">{runId}</span> — UI
          demo; heavy work runs on the server when you use Generate / Send.
        </p>
      </div>

      <RunProgressClient />
    </div>
  );
}

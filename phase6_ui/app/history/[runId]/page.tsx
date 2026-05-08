import Link from "next/link";
import { ActionStack } from "@/components/ActionStack";
import { PulseMeta } from "@/components/PulseMeta";
import { QuoteWall } from "@/components/QuoteWall";
import { ThemeBars } from "@/components/ThemeBars";
import { readPulseByRunId } from "@/lib/pulses";

type Props = { params: { runId: string } };

export const dynamic = "force-dynamic";

export default function HistoryDetailPage({ params }: Props) {
  const runId = decodeURIComponent(params.runId);
  const pulse = readPulseByRunId(runId);
  if (!pulse) {
    return (
      <div className="space-y-10 py-8 text-center md:text-left">
        <Link
          href="/history"
          className="inline-block font-dm text-lg text-[#00ffc8]/85 hover:text-[#00ffc8]"
        >
          ← Archive
        </Link>
        <div className="glass mx-auto max-w-xl rounded-[2rem] p-10 md:p-12">
          <h1 className="font-syne text-3xl font-extrabold text-white md:text-4xl">
            No pulse for this run
          </h1>
          <p className="mt-6 font-dm text-lg leading-relaxed text-white/55 md:text-xl">
            We couldn&apos;t load{" "}
            <code className="rounded-lg bg-white/10 px-2 py-1 text-[#00ffc8]">
              {runId}
            </code>
            . It may not exist on this machine, or you opened the app from the
            wrong folder — run the UI from{" "}
            <code className="rounded bg-white/10 px-1.5">phase6_ui</code> so it
            can see <code className="rounded bg-white/10 px-1.5">data/output</code>
            .
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4 md:justify-start">
            <Link
              href="/"
              className="rounded-full bg-white/10 px-8 py-3 font-dm text-lg font-semibold text-white hover:bg-white/15"
            >
              Dashboard
            </Link>
            <Link
              href="/history"
              className="rounded-full border border-white/20 px-8 py-3 font-dm text-lg font-semibold text-white/80"
            >
              All runs
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 md:space-y-12">
      <Link
        href="/history"
        className="inline-block font-dm text-sm text-[#00ffc8]/85 hover:text-[#00ffc8]"
      >
        ← Archive
      </Link>

      <p className="font-dm text-[11px] uppercase tracking-[0.28em] text-white/40">
        Read-only · {runId}
      </p>

      <PulseMeta pulse={pulse} />

      <div className="grid gap-16 lg:grid-cols-2 lg:gap-20">
        <ThemeBars themes={pulse.top_themes} />
        <QuoteWall quotes={pulse.quotes} />
      </div>

      <ActionStack actions={pulse.actions} />
    </div>
  );
}

import { ControlsBar } from "@/components/ControlsBar";
import { ActionStack } from "@/components/ActionStack";
import { PulseMeta } from "@/components/PulseMeta";
import { QuoteWall } from "@/components/QuoteWall";
import { ThemeBars } from "@/components/ThemeBars";
import { readLatestPulse } from "@/lib/pulses";

export const dynamic = "force-dynamic";

export default function HomePage() {
  let bundle: ReturnType<typeof readLatestPulse> = null;
  try {
    bundle = readLatestPulse();
  } catch {
    bundle = null;
  }

  if (!bundle) {
    return (
      <div className="glass rounded-2xl px-8 py-12 text-center md:px-12">
        <p className="font-syne text-2xl font-bold tracking-tight text-white md:text-3xl">
          No pulse yet
        </p>
        <p className="mt-5 font-dm text-sm text-white/50 md:text-base">
          Run the Python pipeline locally, or add{" "}
          <code className="rounded bg-white/10 px-2 py-1 text-[#00ffc8]">
            public/sample/pulse.json
          </code>
        </p>
      </div>
    );
  }

  const { pulse, runId } = bundle;

  return (
    <>
      <div className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl space-y-3">
          <p className="font-dm text-[11px] font-semibold uppercase tracking-[0.28em] text-[#ff2d92]/90">
            groww · play store
          </p>
          <h1 className="font-syne text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
            Weekly <span className="text-gradient">pulse</span>
          </h1>
          <p className="max-w-xl font-dm text-sm text-white/55 md:text-base">
            Themes, receipts, and what to ship next — from live Play Store
            reviews.
          </p>
        </div>
        <div className="hidden shrink-0 lg:block">
          <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 font-dm text-xs text-white/55">
            Run ID · {runId}
          </div>
        </div>
      </div>

      <ControlsBar defaultRunId={runId} />

      <div className="mt-10 md:mt-12">
        <PulseMeta pulse={pulse} />
      </div>

      <div className="mt-10 grid gap-10 md:mt-12 lg:grid-cols-2 lg:gap-12">
        <ThemeBars themes={pulse.top_themes} />
        <QuoteWall quotes={pulse.quotes} />
      </div>

      <div className="mt-10 md:mt-12">
        <ActionStack actions={pulse.actions} />
      </div>
    </>
  );
}

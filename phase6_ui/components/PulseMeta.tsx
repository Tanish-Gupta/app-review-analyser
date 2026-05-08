import type { PulseData } from "@/lib/types";

export function PulseMeta({ pulse }: { pulse: PulseData }) {
  const fmt = new Intl.DateTimeFormat("en-IN", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const start = fmt.format(new Date(pulse.window_start));
  const end = fmt.format(new Date(pulse.window_end));

  return (
    <div className="glass sticker-ring relative overflow-hidden rounded-2xl p-6 sm:p-8">
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-[#ff2d92]/18 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-12 -left-8 h-36 w-36 rounded-full bg-[#00ffc8]/12 blur-3xl" />
      <p className="font-dm text-[10px] font-semibold uppercase tracking-[0.28em] text-[#00ffc8]/85">
        snapshot
      </p>
      <h1 className="mt-3 font-syne text-2xl font-bold leading-snug tracking-tight text-white sm:text-3xl md:text-4xl">
        {pulse.title}
      </h1>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-white/[0.07] bg-white/[0.03] px-4 py-4">
          <p className="font-dm text-[10px] uppercase tracking-wider text-white/40">
            Reviews
          </p>
          <p className="mt-2 font-syne text-2xl font-bold text-white">
            {pulse.review_count.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.07] bg-white/[0.03] px-4 py-4">
          <p className="font-dm text-[10px] uppercase tracking-wider text-white/40">
            Avg rating
          </p>
          <p className="mt-2 font-syne text-2xl font-bold text-gradient">
            {pulse.avg_rating.toFixed(2)}★
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.07] bg-white/[0.03] px-4 py-4">
          <p className="font-dm text-[10px] uppercase tracking-wider text-white/40">
            Window
          </p>
          <p className="mt-2 font-dm text-sm font-medium leading-snug text-white/75">
            {start} → {end}
          </p>
        </div>
      </div>
    </div>
  );
}

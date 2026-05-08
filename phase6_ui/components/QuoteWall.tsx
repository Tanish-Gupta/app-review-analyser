import type { PulseQuote } from "@/lib/types";

export function QuoteWall({ quotes }: { quotes: PulseQuote[] }) {
  return (
    <div className="space-y-6">
      <h2 className="font-syne text-xl font-bold tracking-tight text-white md:text-2xl">
        In their words
      </h2>
      <ul className="space-y-5">
        {quotes.map((q, idx) => (
          <li
            key={idx}
            className="glass rounded-xl p-5 transition hover:border-[#ff2d92]/25 md:p-6"
          >
            <p className="font-dm text-sm leading-relaxed text-white/85 md:text-base">
              “{q.text}”
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-[#00ffc8]/15 px-3 py-0.5 font-dm text-[11px] font-semibold uppercase tracking-wider text-[#00ffc8]">
                ★ {q.rating}
              </span>
              <span className="font-dm text-xs text-white/40">{q.date}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

import type { PulseTheme } from "@/lib/types";

export function ThemeBars({ themes }: { themes: PulseTheme[] }) {
  return (
    <div className="space-y-6">
      <h2 className="font-syne text-xl font-bold tracking-tight text-white md:text-2xl">
        Top themes
      </h2>
      <ul className="space-y-6">
        {themes.map((t, i) => {
          const vol = Math.round(t.volume_share * 1000) / 10;
          const neg = Math.round(t.negative_share * 1000) / 10;
          return (
            <li key={t.id} className="group">
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-dm text-sm font-medium leading-snug text-white/90 md:text-base">
                  <span className="mr-2 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#ff2d92]/28 to-[#00ffc8]/18 font-syne text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  {t.name}
                </span>
                <span className="shrink-0 font-dm text-xs text-white/45 md:text-sm">
                  {vol}% · {neg}% neg
                </span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-white/[0.06] ring-1 ring-white/[0.08]">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#ff2d92] via-[#ff6bc7] to-[#00ffc8] transition-all duration-700 group-hover:brightness-110"
                  style={{ width: `${Math.min(100, vol)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

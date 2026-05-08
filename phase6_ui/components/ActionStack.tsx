import type { PulseAction } from "@/lib/types";

const ownerColors: Record<string, string> = {
  Product: "from-[#ff2d92]/40 to-[#ff2d92]/10 text-[#ffb3d9]",
  Eng: "from-[#00ffc8]/35 to-[#00ffc8]/10 text-[#9fffee]",
  Support: "from-[#d4ff4d]/35 to-[#d4ff4d]/10 text-[#e8ffb3]",
};

export function ActionStack({ actions }: { actions: PulseAction[] }) {
  return (
    <div className="space-y-6">
      <h2 className="font-syne text-xl font-bold tracking-tight text-white md:text-2xl">
        Next moves
      </h2>
      <ol className="space-y-4">
        {actions.map((a, i) => {
          const chip =
            ownerColors[a.owner] ??
            "from-white/20 to-white/5 text-white/80";
          return (
            <li
              key={i}
              className="glass flex gap-4 rounded-xl p-5 transition hover:border-[#00ffc8]/20 md:gap-5"
            >
              <span className="font-syne text-lg font-bold leading-none text-white/25">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1 space-y-2">
                <span
                  className={`inline-block rounded-full bg-gradient-to-r px-2.5 py-0.5 font-dm text-[10px] font-bold uppercase tracking-widest ${chip}`}
                >
                  {a.owner}
                </span>
                <p className="font-dm text-sm leading-relaxed text-white/80 md:text-base">
                  {a.idea}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

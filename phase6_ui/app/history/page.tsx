import Link from "next/link";
import { getHistoryRunIds } from "@/lib/history";
import { readPulseByRunId } from "@/lib/pulses";

export const dynamic = "force-dynamic";

export default function HistoryPage() {
  const ids = getHistoryRunIds();

  return (
    <div className="space-y-8 md:space-y-10">
      <div className="space-y-3">
        <h1 className="font-syne text-3xl font-bold tracking-tight text-white md:text-4xl">
          Archive
        </h1>
        <p className="max-w-xl font-dm text-sm text-white/45 md:text-base">
          Past pulses — tap to view read-only.
        </p>
      </div>

      <ul className="space-y-4 md:space-y-5">
        {ids.map((id) => {
          const pulse = readPulseByRunId(id);
          const title = pulse?.title ?? id;
          const when = pulse?.generated_at
            ? new Date(pulse.generated_at).toLocaleString()
            : "";
          return (
            <li key={id}>
              <Link
                href={`/history/${encodeURIComponent(id)}`}
                className="glass group flex flex-col gap-2 rounded-xl p-5 transition hover:border-[#00ffc8]/30 sm:flex-row sm:items-center sm:justify-between md:p-6"
              >
                <span className="font-syne text-base font-semibold leading-snug text-white group-hover:text-[#00ffc8] md:text-lg">
                  {title}
                </span>
                <span className="font-dm text-xs text-white/35 md:text-sm">
                  {id}
                  {when ? ` · ${when}` : ""}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>

      {ids.length === 0 && (
        <p className="font-dm text-sm text-white/45">Nothing saved yet.</p>
      )}
    </div>
  );
}

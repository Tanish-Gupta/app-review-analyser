"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const PHASES = [
  "Ingest reviews",
  "Clean & scrub",
  "Discover themes",
  "Classify",
  "Build pulse",
  "Ready",
];

export function RunProgressClient() {
  const [phaseIdx, setPhaseIdx] = useState(0);

  useEffect(() => {
    const t = window.setInterval(() => {
      setPhaseIdx((i) => Math.min(i + 1, PHASES.length - 1));
    }, 900);
    return () => clearInterval(t);
  }, []);

  const pct = ((phaseIdx + 1) / PHASES.length) * 100;

  return (
    <div className="glass rounded-2xl p-6 md:p-8">
      <div className="mb-8 h-3 overflow-hidden rounded-full bg-white/[0.06] ring-1 ring-white/[0.08]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[#ff2d92] via-[#00ffc8] to-[#d4ff4d] transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ol className="space-y-4 md:space-y-5">
        {PHASES.map((label, i) => (
          <li
            key={label}
            className={`flex items-center gap-4 font-dm text-sm transition md:text-base ${
              i <= phaseIdx ? "text-white" : "text-white/25"
            }`}
          >
            <span
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-syne text-xs font-bold ${
                i < phaseIdx
                  ? "bg-[#00ffc8]/25 text-[#00ffc8]"
                  : i === phaseIdx
                    ? "animate-pulse bg-[#ff2d92]/30 text-[#ffb3d9]"
                    : "bg-white/5 text-white/35"
              }`}
            >
              {i < phaseIdx ? "✓" : i + 1}
            </span>
            {label}
          </li>
        ))}
      </ol>

      {phaseIdx >= PHASES.length - 1 && (
        <div className="mt-10 text-center">
          <Link
            href="/"
            className="inline-flex rounded-xl bg-gradient-to-r from-[#d4ff4d] to-[#00ffc8] px-8 py-3 font-syne text-sm font-bold text-black"
          >
            Back to latest pulse
          </Link>
        </div>
      )}
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  /** Latest pulse id shown on the page (informational). */
  defaultRunId: string;
};

function formatFetchError(err: unknown): string {
  const s = String(err);
  if (s.includes("Failed to fetch") || s.includes("NetworkError"))
    return "Network error — check connection, or Vercel/Railway may have timed out (full pipeline can take many minutes).";
  if (s.includes("aborted") || s.includes("AbortError"))
    return "Request was aborted or timed out.";
  return s.slice(0, 400);
}

async function readClientJson(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text();
  if (!text.trim()) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { error: "Bad response", detail: text.slice(0, 400) };
  }
}

function formatDetailField(d: unknown): string {
  if (d == null) return "";
  if (typeof d === "string") return d;
  try {
    return JSON.stringify(d).slice(0, 1200);
  } catch {
    return String(d);
  }
}

function hintForHttpStatus(status: number): string | null {
  if (status === 504 || status === 408)
    return "Gateway/timeout — the pipeline often exceeds Vercel’s serverless limit on Hobby (~10s). Use Vercel Pro (higher maxDuration) or run the heavy job directly on Railway.";
  if (status === 401 || status === 403)
    return "Auth rejected — RAILWAY_API_SECRET on Vercel must exactly match Railway’s variable.";
  if (status === 503)
    return "Misconfiguration — e.g. RAILWAY_API_URL without RAILWAY_API_SECRET.";
  if (status === 501)
    return "Railway not connected — add RAILWAY_API_URL + RAILWAY_API_SECRET in Vercel env, then redeploy.";
  return null;
}

/** Human-readable failure for any /api/* JSON error response. */
function formatApiFailure(res: Response, data: Record<string, unknown>): string {
  const lines: string[] = [];
  lines.push(`HTTP ${res.status}${res.statusText ? ` ${res.statusText}` : ""}`);
  const hint = hintForHttpStatus(res.status);
  if (hint) lines.push(hint);
  if (typeof data.error === "string" && data.error.trim()) lines.push(data.error.trim());
  const detail = formatDetailField(data.detail);
  if (detail) lines.push(detail);
  if (lines.length === 1)
    lines.push("Empty error body — check Vercel → Deployment → Logs for this route.");
  return lines.join("\n").slice(0, 2500);
}

export function ControlsBar({ defaultRunId }: Props) {
  const router = useRouter();
  const [weeks, setWeeks] = useState(12);
  const [mode, setMode] = useState<"draft" | "send">("send");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [forceRefresh, setForceRefresh] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleGenerate() {
    setBusy(true);
    setMsg(null);
    try {
      setMsg("Starting pipeline… This often takes several minutes on Railway.");
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weeks }),
      });
      const data = await readClientJson(res);
      if (!res.ok) {
        setMsg(formatApiFailure(res, data));
        return;
      }
      if (typeof data.runId === "string" && data.runId) {
        setMsg(null);
        router.push(`/runs/${data.runId}`);
      }
    } catch (e) {
      setMsg(formatFetchError(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleEmail() {
    setBusy(true);
    setMsg(null);
    try {
      setMsg(
        "Contacting server… Full ingest + Groq + email can take 5–15+ minutes. Leave this tab open.",
      );
      const res = await fetch("/api/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weeks,
          recipient: email,
          recipientName: name,
          mode,
          forceRefresh,
        }),
      });
      const data = await readClientJson(res);
      if (!res.ok) {
        setMsg(formatApiFailure(res, data));
      } else {
        setMsg(
          (typeof data.message === "string" ? data.message : null) ?? "Done.",
        );
        router.refresh();
      }
    } catch (e) {
      setMsg(formatFetchError(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="glass mb-10 rounded-2xl p-6 md:p-8">
      <p className="font-dm text-xs uppercase tracking-[0.12em] text-white/40">
        Controls · viewing run{" "}
        <span className="text-white/65">{defaultRunId}</span>
      </p>

      <div className="mt-6 grid gap-8 lg:grid-cols-2 lg:gap-10">
        <div className="space-y-6">
          <label className="flex flex-col gap-2 font-dm text-xs font-medium uppercase tracking-wide text-white/45">
            Weeks lookback
            <input
              type="range"
              min={12}
              max={26}
              value={weeks}
              onChange={(e) => setWeeks(Number(e.target.value))}
              className="h-2 w-full max-w-md cursor-pointer accent-[#ff2d92]"
            />
            <span className="font-syne text-xl font-semibold text-[#00ffc8]">
              {weeks} weeks
            </span>
          </label>

          <div className="flex flex-col gap-2 font-dm text-xs font-medium uppercase tracking-wide text-white/45">
            Email mode
            <div className="inline-flex rounded-full bg-black/35 p-1 ring-1 ring-white/10">
              {(["draft", "send"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`rounded-full px-4 py-2 font-dm text-sm font-semibold capitalize transition ${
                    mode === m
                      ? "bg-gradient-to-r from-[#ff2d92] to-[#ff6bc7] text-white shadow-md shadow-[#ff2d92]/20"
                      : "text-white/45 hover:text-white"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <label className="flex cursor-pointer items-start gap-3 font-dm text-sm leading-snug text-white/55">
            <input
              type="checkbox"
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
              className="mt-1 h-4 w-4 shrink-0 rounded border-white/30 accent-[#00ffc8]"
            />
            <span>
              <strong className="text-white/80">Force fresh run</strong> — ignore
              the 24-hour cache and pull latest reviews + rebuild everything before
              sending.
            </span>
          </label>
        </div>

        <div className="flex flex-col justify-end gap-3">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={busy}
            className="inline-flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-[#d4ff4d] via-[#00ffc8] to-[#00c4ff] px-5 py-3 font-syne text-sm font-bold text-black shadow-md transition hover:opacity-95 disabled:opacity-50 sm:w-auto"
          >
            {busy ? "Running pipeline…" : "Generate pulse only"}
          </button>
          <p className="font-dm text-xs text-white/35">
            Runs ingest → themes → pulse (no email). Can take several minutes.
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-5 border-t border-white/[0.06] pt-8 sm:grid-cols-2">
        <label className="flex flex-col gap-2 font-dm text-xs font-medium text-white/45">
          Recipient email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@domain.com"
            className="rounded-xl border border-white/10 bg-black/25 px-4 py-3 font-dm text-sm text-white placeholder:text-white/30 focus:border-[#00ffc8]/45 focus:outline-none focus:ring-1 focus:ring-[#00ffc8]/30"
          />
        </label>
        <label className="flex flex-col gap-2 font-dm text-xs font-medium text-white/45">
          Name for greeting
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Alex"
            className="rounded-xl border border-white/10 bg-black/25 px-4 py-3 font-dm text-sm text-white placeholder:text-white/30 focus:border-[#ff2d92]/45 focus:outline-none focus:ring-1 focus:ring-[#ff2d92]/30"
          />
        </label>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={handleEmail}
          disabled={busy || !email.trim()}
          className="rounded-xl border border-[#ff2d92]/45 bg-[#ff2d92]/10 px-6 py-3 font-dm text-sm font-semibold text-[#ffb3d9] transition hover:bg-[#ff2d92]/18 disabled:opacity-40"
        >
          {busy ? "Working…" : "Fetch latest data & send email"}
        </button>
      </div>
      {msg && (
        <div className="mt-4 rounded-xl border border-white/10 bg-black/30 px-4 py-3">
          <p className="font-dm text-[10px] font-semibold uppercase tracking-wider text-white/40">
            Status
          </p>
          <p className="mt-1 max-w-[min(90vw,48rem)] whitespace-pre-wrap break-words font-dm text-sm leading-relaxed text-[#00ffc8]/90">
            {msg}
          </p>
        </div>
      )}
      <p className="mt-4 font-dm text-xs leading-relaxed text-white/35">
        Sends after running the full pipeline (or reusing a pulse from the last 24
        hours for the same week range, unless “Force fresh run” is checked).
      </p>
    </section>
  );
}

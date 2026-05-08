/** When `RAILWAY_API_URL` + `RAILWAY_API_SECRET` are set, API routes proxy to the Docker API on Railway. */

export function railwayBackendConfigured(): boolean {
  const url = process.env.RAILWAY_API_URL?.trim();
  const secret = process.env.RAILWAY_API_SECRET?.trim();
  return Boolean(url && secret);
}

export function railwayBackendMisconfigured(): boolean {
  const url = process.env.RAILWAY_API_URL?.trim();
  const secret = process.env.RAILWAY_API_SECRET?.trim();
  return Boolean(url && !secret);
}

export async function railwayPost(path: string, body: unknown): Promise<Response> {
  const base = process.env.RAILWAY_API_URL!.replace(/\/$/, "");
  const secret = process.env.RAILWAY_API_SECRET!;
  return fetch(`${base}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${secret}`,
    },
    body: JSON.stringify(body),
  });
}

/** Parse JSON or return a placeholder when Railway/Vercel returns HTML or empty body. */
export async function readJsonSafe(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text();
  if (!text.trim()) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return {
      error: "Non-JSON response from upstream",
      detail: text.slice(0, 800),
    };
  }
}

export function flattenDetail(detail: unknown): string {
  if (detail == null) return "";
  if (typeof detail === "string") return detail;
  try {
    return JSON.stringify(detail).slice(0, 2000);
  } catch {
    return String(detail);
  }
}

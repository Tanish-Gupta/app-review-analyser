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

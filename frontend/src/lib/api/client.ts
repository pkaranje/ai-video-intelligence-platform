import { APIError } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/proxy";

export async function fetchAPI<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? body.message ?? message;
    } catch {
      // ignore parse error
    }
    throw new APIError(message, res.status);
  }
  return res.json() as Promise<T>;
}

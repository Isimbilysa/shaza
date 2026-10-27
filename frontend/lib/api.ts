/**
 * The one place the dashboard talks to the SHAZA API.
 *
 * Two rules it enforces for everything downstream:
 *
 *   1. A failure is returned, never swallowed. A dashboard that renders an empty chart when the
 *      API is down is making a claim about the world ("no data exists") out of a fact about the
 *      network. `fetchSeries` returns a discriminated result so the page has to handle the
 *      difference explicitly.
 *   2. No caching. Stage 1 is one developer and one database; a stale read here would be
 *      indistinguishable from an ingestion bug, which is the most expensive kind of confusion
 *      to debug. Revalidation becomes a real decision in stage 3, when there are enough
 *      viewers for it to matter.
 */

import type { Envelope, Location, Series } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000/api/v1';

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; detail: string };

async function get<T>(path: string, params?: Record<string, string>): Promise<ApiResult<T>> {
  const url = new URL(`${API_BASE}${path}`);
  for (const [key, value] of Object.entries(params ?? {})) {
    url.searchParams.set(key, value);
  }

  let response: Response;
  try {
    response = await fetch(url, { cache: 'no-store' });
  } catch (cause) {
    return {
      ok: false,
      error: 'The SHAZA API did not respond.',
      detail:
        cause instanceof Error
          ? `${cause.message} — is the backend running at ${API_BASE}?`
          : `Unreachable at ${API_BASE}.`,
    };
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body: unknown = await response.json();
      if (body && typeof body === 'object' && 'detail' in body) {
        detail = String((body as { detail: unknown }).detail);
      }
    } catch {
      // A non-JSON error body is itself the useful signal; keep the status code.
    }
    return { ok: false, error: `The API returned ${response.status}.`, detail };
  }

  const envelope = (await response.json()) as Envelope<T>;
  return { ok: true, data: envelope.data };
}

export function fetchLocations(): Promise<ApiResult<Location[]>> {
  return get<Location[]>('/locations');
}

/**
 * One location, one variable. The API groups by (variable, provenance) and may legitimately
 * return several series for a single variable once forecasts sit alongside reanalysis, so this
 * returns the list rather than flattening it. Merging two provenances into one line is exactly
 * the mistake the grouping exists to prevent.
 */
export function fetchSeries(
  slug: string,
  variable: string,
  window?: { start?: string; end?: string },
): Promise<ApiResult<Series[]>> {
  const params: Record<string, string> = { variable };
  if (window?.start) params.start = window.start;
  if (window?.end) params.end = window.end;
  return get<Series[]>(`/observations/${slug}`, params);
}

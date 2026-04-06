import { describeApiFailure } from "@/lib/api-errors";
import type { SearchResponse } from "@/lib/search-types";

/**
 * If `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_API_BASE_URL` is set, the browser calls the API
 * directly (CORS must allow your dev origin).
 *
 * If unset, requests use same-origin `/api/...` and Next.js proxies to the Python server
 * (see `next.config.mjs` → `API_PROXY_TARGET`, default `http://127.0.0.1:8010`).
 */
function directApiBase(): string | null {
  const u =
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return u || null;
}

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const direct = directApiBase();
  if (direct) return `${direct.replace(/\/$/, "")}${p}`;
  return `/api${p}`;
}

/** Shown in error messages so you know which mode is active */
export function apiBaseLabel(): string {
  const direct = directApiBase();
  if (direct) return direct;
  return "/api → http://127.0.0.1:8010 (Next.js proxy)";
}

export type SearchAlgo = "keyword" | "tfidf" | "bm25";

async function readErrorBody(res: Response): Promise<string> {
  let detail = res.statusText || `HTTP ${res.status}`;
  try {
    const j = (await res.json()) as { detail?: unknown };
    if (typeof j.detail === "string") detail = j.detail;
  } catch {
    /* ignore */
  }
  return detail;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const label = apiBaseLabel();
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    throw new Error(describeApiFailure(e, label));
  }

  if (!res.ok) {
    throw new Error(await readErrorBody(res));
  }
  return res.json() as Promise<T>;
}

export async function searchPost(
  algo: SearchAlgo,
  query: string,
  topK = 10
): Promise<SearchResponse> {
  const path =
    algo === "tfidf" ? "tfidf" : algo === "bm25" ? "bm25" : "keyword";
  return postJson<SearchResponse>(apiUrl(`/search/${path}`), {
    query,
    top_k: topK,
  });
}

export async function uploadSnippet(body: {
  text: string;
  doc_id?: string;
  source?: string;
  top_k?: number;
}): Promise<unknown> {
  return postJson(apiUrl("/upload"), {
    text: body.text,
    doc_id: body.doc_id,
    source: body.source ?? "upload",
    top_k: body.top_k ?? 5,
  });
}

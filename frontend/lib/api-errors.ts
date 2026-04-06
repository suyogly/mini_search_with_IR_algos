/**
 * Turn fetch failures (CORS, offline API, wrong URL) into readable UI copy.
 */
export function describeApiFailure(error: unknown, apiBase: string): string {
  const hint = `Routing: ${apiBase}`;

  if (error instanceof TypeError) {
    return [
      "Could not reach the API (network or browser blocked the request).",
      "Start the Python server from the project root: uv run main.py (default port 8010; set API_PORT=8000 if you prefer).",
      "If you use the default Next.js proxy, leave NEXT_PUBLIC_API_* unset; the dev server forwards /api to http://127.0.0.1:8010 (override with API_PROXY_TARGET).",
      "If you set NEXT_PUBLIC_API_URL to call the API directly, use http://127.0.0.1:8010 (and the same port the API listens on).",
      hint,
    ].join("\n\n");
  }

  if (error instanceof DOMException && error.name === "NetworkError") {
    return ["Network error: the request was blocked or the server is unreachable.", hint].join(
      "\n\n"
    );
  }

  if (error instanceof Error) {
    const m = error.message;
    if (/networkerror|failed to fetch|load failed|fetch.*aborted/i.test(m)) {
      return [
        "Network error talking to the API.",
        "Ensure uv run main.py is running on the same port as API_PROXY_TARGET (default 8010).",
        hint,
      ].join("\n\n");
    }
    return m;
  }

  return "Request failed.";
}

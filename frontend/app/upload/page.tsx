"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { uploadSnippet } from "@/lib/api";

export default function UploadPage() {
  const [text, setText] = useState("");
  const [docId, setDocId] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    setMsg(null);
    try {
      const res = (await uploadSnippet({
        text,
        doc_id: docId.trim() || undefined,
      })) as { message?: string; indexed_documents?: number };
      setMsg(
        res.message
          ? `${res.message}${typeof res.indexed_documents === "number" ? ` (${res.indexed_documents} docs indexed)` : ""}`
          : "Uploaded."
      );
      setText("");
      setDocId("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto min-h-screen max-w-lg px-4 py-16">
      <Link
        href="/"
        className="text-sm underline underline-offset-4 hover:text-muted-foreground"
      >
        ← Search
      </Link>
      <h1 className="mt-6 text-2xl font-semibold tracking-tight">Upload snippet</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Text is stored in SQLite and indices are rebuilt on the server.
      </p>

      <form onSubmit={onSubmit} className="mt-10 space-y-6">
        <div className="space-y-2">
          <Label htmlFor="snippet">Snippet</Label>
          <Textarea
            id="snippet"
            required
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste text…"
            disabled={loading}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="docid">Document id (optional)</Label>
          <Input
            id="docid"
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="auto-generated if empty"
            disabled={loading}
          />
        </div>
        <Button type="submit" disabled={loading || !text.trim()}>
          {loading ? "Uploading…" : "Upload"}
        </Button>
      </form>

      {msg ? (
        <p className="mt-6 text-sm text-muted-foreground" role="status">
          {msg}
        </p>
      ) : null}
      {err ? (
        <div
          className="mt-6 rounded-md border border-border bg-muted/50 px-3 py-3 text-sm text-foreground"
          role="alert"
        >
          <p className="font-medium">Something went wrong</p>
          <p className="mt-2 whitespace-pre-line leading-relaxed">{err}</p>
        </div>
      ) : null}
    </div>
  );
}

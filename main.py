from functools import lru_cache
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.rag.preprocessing.normaliser import normalize_documents
from app.rag.retrievers.bm25Search import BM25Retriever
from app.rag.retrievers.keywordSearch import KeywordRetriever
from app.rag.retrievers.tfidfSearch import TfidfRetriever
from app.rag.storage.sqlite_store import SQLiteSnippetStore

app = FastAPI(title="Mini Search API", version="0.1.0")


def _frontend_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50)


class UploadRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text snippet to store")
    doc_id: str | None = Field(default=None, min_length=1)
    source: str = Field(default="upload", min_length=1)
    query: str | None = Field(
        default=None,
        description="Optional query to score after upload. If omitted, uploaded text is used.",
    )
    top_k: int = Field(default=5, ge=1, le=50)


@lru_cache(maxsize=1)
def get_store() -> SQLiteSnippetStore:
    return SQLiteSnippetStore.from_env()


def _load_normalized_documents_from_store() -> list[dict]:
    try:
        raw_documents = get_store().fetch_all_documents()
    except Exception as exc:
        db_path = getattr(get_store(), "db_path", "unknown")
        raise HTTPException(
            status_code=500,
            detail=f"SQLite error while loading snippets from {db_path}: {exc}.",
        ) from exc

    if not raw_documents:
        return []
    return normalize_documents(raw_documents)


@lru_cache(maxsize=1)
def get_retrievers() -> dict[str, object]:
    documents = _load_normalized_documents_from_store()
    return {
        "tfidf": TfidfRetriever(documents),
        "bm25": BM25Retriever(documents),
        "keyword": KeywordRetriever(documents),
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Use POST /upload to store snippets in SQLite, then search with /search/tfidf, /search/bm25, or /search/keyword."
    }


@app.get("/snippets")
def list_snippets() -> dict:
    try:
        snippets = get_store().fetch_all_documents()
    except Exception as exc:
        db_path = getattr(get_store(), "db_path", "unknown")
        raise HTTPException(
            status_code=500,
            detail=f"SQLite error while reading snippets from {db_path}: {exc}.",
        ) from exc

    return {"count": len(snippets), "snippets": snippets}


@app.post("/upload")
def upload_text(payload: UploadRequest) -> dict:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text snippet cannot be blank.")

    doc_id = payload.doc_id.strip() if payload.doc_id else f"snippet-{uuid4().hex[:12]}"
    source = payload.source.strip() or "upload"

    try:
        get_store().upsert_snippet(doc_id=doc_id, content=text, source=source)
    except Exception as exc:
        db_path = getattr(get_store(), "db_path", "unknown")
        raise HTTPException(
            status_code=500,
            detail=f"SQLite error while saving snippet to {db_path}: {exc}.",
        ) from exc

    get_retrievers.cache_clear()
    retrievers = get_retrievers()

    query_text = payload.query.strip() if payload.query and payload.query.strip() else text

    tfidf_results = retrievers["tfidf"].search(query_text, top_k=payload.top_k)
    bm25_results = retrievers["bm25"].search(query_text, top_k=payload.top_k)
    keyword_results = retrievers["keyword"].search(query_text, top_k=payload.top_k)

    indexed_count = len(getattr(retrievers["tfidf"], "documents", []))

    return {
        "message": "Snippet stored in SQLite and vectors recomputed.",
        "uploaded": {"doc_id": doc_id, "source": source},
        "indexed_documents": indexed_count,
        "query_used": query_text,
        "similarity": {
            "tfidf": tfidf_results,
            "bm25": bm25_results,
            "keyword": keyword_results,
        },
    }


@app.post("/reload")
def reload_indices() -> dict[str, str]:
    get_retrievers.cache_clear()
    get_retrievers()
    return {"message": "Retrievers reloaded from SQLite snippets."}


@app.post("/search/tfidf")
def search_tfidf(payload: SearchRequest) -> dict:
    retriever = get_retrievers()["tfidf"]
    results = retriever.search(payload.query, top_k=payload.top_k)
    return {
        "algorithm": "tfidf",
        "query": payload.query,
        "count": len(results),
        "results": results,
    }


@app.post("/search/bm25")
def search_bm25(payload: SearchRequest) -> dict:
    retriever = get_retrievers()["bm25"]
    results = retriever.search(payload.query, top_k=payload.top_k)
    return {
        "algorithm": "bm25",
        "query": payload.query,
        "count": len(results),
        "results": results,
    }


@app.post("/search/keyword")
def search_keyword(payload: SearchRequest) -> dict:
    retriever = get_retrievers()["keyword"]
    results = retriever.search(payload.query, top_k=payload.top_k)
    return {
        "algorithm": "keyword",
        "query": payload.query,
        "count": len(results),
        "results": results,
    }


def main() -> None:
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

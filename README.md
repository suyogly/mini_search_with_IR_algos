## Mini Search with NumPy Retrievers + SQLite

This project stores uploaded text snippets in SQLite and builds in-memory retrievers from that data.

Implemented from scratch (using only NumPy for vector math):
- TF-IDF retriever
- BM25 retriever
- Keyword overlap retriever

## Project Config

Create a project-local `.env.local` file in the repository root:

```dotenv
SQLITE_DB_PATH=app/data/snippets.sqlite3
```

The app reads SQLite settings from `.env.local` by default.

## Run

```bash
/Users/suyogdevkhanal/Projects/mini_search_with_IR_algos/.venv/bin/python main.py
```

## Frontend (Next.js)

Frontend app lives in `frontend/`.

```bash
cd frontend
npm install
npm run dev
```

By default, frontend calls backend at `http://localhost:8000` using:

```dotenv
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## API

### 1) Upload a snippet (stored in SQLite)

`POST /upload`

```json
{
	"text": "Your text snippet here",
	"doc_id": "optional-custom-id",
	"source": "upload",
	"query": "optional query for immediate similarity",
	"top_k": 5
}
```

Response includes immediate similarity results from TF-IDF, BM25, and keyword retrievers.

### 2) Search

`POST /search/tfidf`

`POST /search/bm25`

`POST /search/keyword`

```json
{
	"query": "normalize structure",
	"top_k": 5
}
```

### 3) Rebuild index cache from SQLite

`POST /reload`

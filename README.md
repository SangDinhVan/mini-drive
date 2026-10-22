# Mini Drive - V1

A local-first file manager built from [the project bible](docs/PROJECT_BIBLE_MINI_DRIVE.md).

Vue 3 + TypeScript + Vite on port 5173, FastAPI on port 8000, PostgreSQL metadata on Neon, file bytes in `backend/uploads/`.

## What works

- Select or drop multiple files; sequential uploads with individual success/error states.
- List the latest 100 files with name, type, size and upload date.
- Drive-style sidebar, compact file grid, filename search and photo/other-file filters across the loaded collection.
- Preview verified PNG, JPEG and WebP images; download any file.
- Confirm before deleting; empty/loading/disconnected/error states.
- Default 10 MiB limit per file, bounded multipart requests, random storage keys, safe attachment responses and request IDs.

## Requirements

- Python 3.11 or newer (verified with Python 3.14).
- Node.js 26 recommended; Node.js 22.22.2+ or 24.15+ also satisfy the development tools.
- A Neon PostgreSQL database and its connection string.

## 1. Backend and Neon

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and replace the placeholder `DATABASE_URL` with the connection string from Neon Console. Both `postgresql://` and `postgresql+psycopg://` work; the app uses psycopg and requires TLS. Do not put credentials in the frontend or commit `.env`.

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=10
```

Create the schema, then start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`UPLOAD_DIR` resolves relative to `backend/`, regardless of the current working directory. Without `DATABASE_URL`, the API starts and `/api/health` works, but file endpoints return an actionable 503 error. Health reports process availability, not database health.

API docs: http://127.0.0.1:8000/docs

## 2. Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies relative `/api` requests to `http://127.0.0.1:8000`; no CORS configuration is needed. Keep both processes running.

## Run with Docker Compose

Set `DATABASE_URL` in `backend/.env` as described above. From the project root:

```bash
docker compose up --build -d
docker compose logs -f backend
```

Open http://localhost:8088. Nginx serves the built frontend and proxies `/api/` to the backend container.

On every backend container start, `alembic upgrade head` applies any pending database migrations before Uvicorn starts. Applied migrations are tracked in the database and are not run again. If a migration fails (for example, because Neon is unreachable), the backend exits without starting the API; check its logs, fix the cause, and run `docker compose up -d` again. Migrations run at container startup, not during image build.

This startup sequence assumes one backend container for local use. If you later run multiple backend replicas, run migrations once as a separate deployment step before starting them.

Uploads persist in the `uploads-data` named volume. `docker compose down` keeps it; `docker compose down -v` deletes it. The volume does not back up the metadata stored in Neon.

## Checks

Backend:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use isolated SQLite databases and temporary upload folders; they never connect to Neon or touch your actual uploads. Tests cover lifecycle/persistence, image validation, file limits, traversal names, missing files, database rollback and Alembic upgrade/downgrade. SQLite tests do not replace testing the real Neon connection.

Frontend:

```bash
cd frontend
npm test
npm run build
```

Verified: 23 backend tests, 11 frontend API/component tests, TypeScript checking, production build, and an HTTP smoke test through Vite's proxy all pass. Frontend dependency audit reports zero vulnerabilities. The browser provider was unavailable, so visual desktop/mobile checks remain manual.

After configuring Neon, upload an image and a document, restart both processes, reload, preview/download, and delete the test files. Verify that rows persist on Neon and bytes persist in `backend/uploads/`.

## Scope and limits

This version has no authentication and must stay on your personal machine. Bind to `127.0.0.1`; do not expose it publicly. Local development uses Vite and FastAPI; Docker Compose uses Nginx and FastAPI with the same Neon database. No MinIO or CI/CD is included.

Filesystem and PostgreSQL cannot share a transaction. Upload failures clean up bytes; deletion stages the local file and restores it if the database operation fails. A crash, uncertain database commit, or failed cleanup can still leave orphan bytes. Back up both metadata and uploads together; do not manually remove staged files without checking the database. Reconciliation is a later production concern.

Files that are not verified PNG/JPEG/WebP are served as `application/octet-stream` attachments. Corrupt files presented as supported images return 415. Uploaded HTML and SVG never render inline.

The UI uses Google Fonts when available and has local font fallbacks. Upload state shows waiting/uploading/success/error, without a percentage because the native Fetch API does not expose upload progress.

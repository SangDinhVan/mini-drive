# Mini Drive V1 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the local-first file manager described in the project bible.

**Architecture:** Vue calls relative /api URLs through Vite's proxy. FastAPI separates HTTP, metadata persistence, and local storage; Alembic creates the Neon schema.

**Tech Stack:** Vue 3, TypeScript, Vite, FastAPI, SQLAlchemy 2, Alembic, psycopg, Pillow for verified image previews.

**Spec:** docs/PROJECT_BIBLE_MINI_DRIVE.md

## Global Constraints

- Local processes on 127.0.0.1, ports 5173 and 8000.
- PostgreSQL on Neon, bytes in backend/uploads; no Docker, Nginx, MinIO, auth, or CSS framework.
- Maximum 10 MiB per file by default, enforced while reading actual bytes.
- Preserve /api contract, random storage keys, safe image previews, nosniff.
- Never use customer uploads or an existing Neon database for destructive tests.

## Review Focus

- Database write failure must clean uploaded bytes and restore staged deletions.
- Forged image MIME types must never enable HTML or corrupt image previews.
- Traversal names and oversized streamed content must leave storage clean.
- Restarting must preserve metadata and bytes; tests use an isolated SQLite database only.
- Upload failures must not stop subsequent files; deletion failures must remain retryable.

### Task 1: Backend and migrations

**Files:** backend/app/{api,core,db,schemas,repositories,services}, backend/alembic, backend/tests, backend/requirements*.txt, backend/.env.example.

**Interfaces:** /api/health; POST/GET /api/files; GET /api/files/{id}; GET /api/files/{id}/content?download=1; DELETE /api/files/{id}. DTO: id, name, content_type, size_bytes, created_at, download_url, preview_url.

- [x] Write isolated API tests for lifecycle, persistence, size limits, invalid names, verified previews, missing content, and transaction rollback.
- [x] Run tests before implementation and observe missing app failure.
- [x] Implement settings, SQLAlchemy sessions/model, repository, local storage, file service, DTO, router and safe error handlers.
- [x] Add reversible Alembic migration matching model.
- [x] Run full pytest suite and validate migration on a throwaway database.

### Task 2: Frontend

**Files:** frontend/package.json, configs, src/types/file.ts, src/services/filesApi.ts, src/components/{UploadDropzone,FileGrid,FileCard,ConfirmDeleteDialog}.vue, src/App.vue, src/style.css.

**Interfaces:** FileItem matches backend DTO. Native Fetch API; upload sequentially with per-file states; accessible image/delete dialogs.

- [x] Add API-client tests for multipart, relative URLs, errors, and 204 responses; run before implementation.
- [x] Build responsive single-screen UI with loading, empty, offline, upload and deletion states.
- [x] Run frontend tests, TypeScript check and production build.

### Task 3: Integration and handoff

**Files:** README.md, this plan.

- [x] Verify proxy and upload/download/preview/delete with isolated test data.
- [x] Review implementation against project bible and fix material findings.
- [x] Document Neon setup, local commands, checks and distributed transaction limits.
- [x] Mark completed tasks and report actual verification; real Neon checks require user configuration.

## Execution Notes

- Source directory has no usable git repository; no commits/worktree operations performed.
- Existing project bible is the implementation brief supplied by the user; proceed directly with the authorized build.
- SQLite is confined to tests; production accepts PostgreSQL URLs only.
- Task 1 complete: 23 backend tests pass, including migration/model parity and rollback.
- Task 2 complete: 10 API/component tests pass; vue-tsc and production build pass; npm audit reports zero vulnerabilities.
- Task 3 complete: HTTP smoke test through port 5173 passes using a migrated temporary SQLite database and temporary uploads.
- Review fixed incomplete JPEG decoding, bounded multipart spooling, upload recovery after an initial connection failure, and idempotent UI handling of deleted files.
- Independent reviewer could not start because its provider had no active credentials; performed inline review instead.
- Browser provider unavailable: visual desktop/mobile verification not performed. DOM tests exercise Vue components and dialog state.
- Real Neon migration and restart acceptance remain pending DATABASE_URL configuration.

# PROJECT BIBLE — MINI DRIVE

**Phiên bản:** 1.0  
**Trạng thái:** Thiết kế cho giai đoạn 1 (local-first)  
**Mục tiêu:** Xây dựng ứng dụng quản lý file nhỏ để học frontend, backend, API, database và vòng đời dữ liệu; sau đó mới học Nginx, Docker, MinIO và CI/CD theo từng bước.

---

## 1. Tầm nhìn sản phẩm

Mini Drive là web app cho phép một người dùng tải file từ máy lên server local, xem danh sách, xem trước/tải xuống và xóa file. Mục tiêu là **hiểu và tự triển khai kiến trúc**, không phải sao chép toàn bộ Google Drive.

### Nguyên tắc không được thay đổi trong giai đoạn 1

1. **Không dùng Docker, Docker Compose, Nginx hoặc MinIO** để chạy app ở giai đoạn này.
2. File thật được ghi trên ổ đĩa local trong thư mục `backend/uploads/`.
3. PostgreSQL được cung cấp bởi **Neon** (qua connection string lấy từ Neon Console).
4. Frontend: **Vue 3 + TypeScript + Vite**.
5. Backend: **Python + FastAPI**; dùng SQLAlchemy 2.x và Alembic để làm việc với PostgreSQL.
6. Frontend và backend chạy dưới dạng hai process local độc lập.
7. Bảo mật và cấu trúc code phải đủ rõ để về sau thay local storage bằng MinIO, nhưng **không triển khai MinIO sớm**.

## 2. Phạm vi chức năng

### MVP — cần hoàn thành

- Chọn một hoặc nhiều file để upload.
- Xem trạng thái tải lên (đang tải, thành công, lỗi); với upload nhiều file, cho phép thực hiện tuần tự để đơn giản.
- Xem danh sách file: tên, loại, kích thước, thời gian tải lên.
- Xem trước ảnh (JPG/PNG/WebP) trong giao diện.
- Tải file về máy.
- Xóa file (có hộp thoại xác nhận).
- Hiển thị trạng thái rỗng và thông báo lỗi có ý nghĩa.

### Chưa làm ở MVP

- Đăng nhập, phân quyền, chia sẻ link công khai, thư mục lồng nhau.
- Upload chia mảnh/resumable, đồng bộ nhiều thiết bị, version history.
- Background worker, antivirus, object storage, container hóa, CI/CD.
- Triển khai app public trên Internet.

**Giới hạn sử dụng:** App chỉ chạy trên máy cá nhân phục vụ học tập; không coi API là sẵn sàng cho Internet nếu chưa có xác thực và các lớp bảo vệ bổ sung.

## 3. Stack và nhiệm vụ

| Thành phần | Công nghệ | Nhiệm vụ |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Vite | Hiển thị file, upload, gọi API |
| HTTP client | Fetch API (native) | Gọi backend; giảm dependency |
| Backend | Python + FastAPI | Validate, xử lý HTTP, quản lý file |
| ORM | SQLAlchemy 2.x | Đọc/ghi metadata trong Neon |
| Migration | Alembic | Quản lý schema DB có phiên bản |
| Database | Neon PostgreSQL | Lưu thông tin mô tả file |
| File storage | Local filesystem | Lưu bytes của file trong `backend/uploads/` |
| Dev servers | Vite :5173, FastAPI :8000 | Chạy app local trước Nginx |

## 4. Kiến trúc giai đoạn 1

```text
Browser (http://localhost:5173)
    |
    | GET/POST/DELETE /api/...
    v
Vite dev server (:5173)
    | proxy /api -> http://127.0.0.1:8000
    v
FastAPI (:8000)
    |                         |
    | metadata                | file bytes
    v                         v
Neon PostgreSQL         backend/uploads/
(Cloud database)        (Local filesystem)
```

**Không đồng nhất hai nơi lưu:** Neon **không lưu file**; thư mục uploads **không thay thế cơ sở dữ liệu**.

## 5. Cấu trúc thư mục chuẩn

```text
mini-drive/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── UploadDropzone.vue
│   │   │   ├── FileGrid.vue
│   │   │   ├── FileCard.vue
│   │   │   └── ConfirmDeleteDialog.vue
│   │   ├── services/
│   │   │   └── filesApi.ts
│   │   ├── types/
│   │   │   └── file.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── files.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── file.py
│   │   ├── repositories/
│   │   │   └── file_repository.py
│   │   └── services/
│   │       ├── file_service.py
│   │       └── storage.py
│   ├── uploads/                # FILE THẬT; không commit vào git
│   │   └── .gitkeep
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
│   └── PROJECT_BIBLE.md
├── .gitignore
└── README.md
```

**Các thư mục tương lai (chưa tạo/viết ở giai đoạn 1):** `nginx/`, Dockerfiles, `docker-compose.yml`, `.gitlab-ci.yml`. Sẽ thêm từng thành phần khi học đến nó, thay vì để cấu hình chưa hiểu hoặc chưa dùng.

## 6. Thiết kế dữ liệu

### Bảng `files`

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | UUID, PRIMARY KEY | ID công khai của file |
| `original_name` | TEXT NOT NULL | Tên file ban đầu |
| `storage_key` | TEXT UNIQUE NOT NULL | Tên nội bộ trên ổ đĩa (UUID hoặc chuỗi random) |
| `content_type` | TEXT | MIME type đã xác minh/được xác định |
| `size_bytes` | BIGINT NOT NULL | Kích thước file |
| `created_at` | TIMESTAMPTZ NOT NULL | Thời gian upload |

Không lưu absolute path vào DB. `storage_key` chỉ chứa tên nội bộ hợp lệ, không chứa đường dẫn do client cung cấp.

Ví dụ metadata:

```json
{
  "id": "4cc61d1d-3b65-48c0-9b72-926f5ec51dbf",
  "original_name": "cat.png",
  "storage_key": "d6f6d12b7e7e4ad5a908a9e5fdbf18cc",
  "content_type": "image/png",
  "size_bytes": 153724,
  "created_at": "2026-10-13T08:00:00Z"
}
```

**Lưu ý:** API trả về DTO có `id`, `name`, `content_type`, `size_bytes`, `created_at`, `download_url`, `preview_url` (không lộ `storage_key` nếu không cần).

## 7. Thiết kế API (prefix `/api`)

| Method | Path | Mục đích | Thành công |
|---|---|---|---|
| GET | `/api/health` | Health check | 200 |
| POST | `/api/files` | Upload multipart/form-data, field `file` | 201 |
| GET | `/api/files` | Lấy danh sách file, mới nhất trước | 200 |
| GET | `/api/files/{id}` | Lấy metadata theo ID | 200 |
| GET | `/api/files/{id}/content` | Xem trước/tải nội dung | 200 |
| DELETE | `/api/files/{id}` | Xóa file và metadata | 204 |

- Dùng `Content-Disposition: inline` chỉ cho loại nội dung cho phép preview an toàn (MVP: ảnh PNG/JPG/WebP); với loại khác mặc định attachment.
- Có thể thêm query `?download=1` để ép download.
- Lỗi sử dụng HTTP status chuẩn: 400, 404, 413, 415, 500; không trả stack trace ra client.
- MVP giới hạn **10 MiB/file** (cấu hình qua biến môi trường).
- Danh sách ban đầu có thể giới hạn 100 mục; khi đủ chức năng mới thêm pagination.

## 8. Các luồng quan trọng

### A. Upload

```text
1. Người dùng chọn file trên Vue.
2. Vue POST /api/files (multipart/form-data).
3. FastAPI kiểm tra kích thước, tên, loại file cho preview; không tin tên file từ client để xây đường dẫn.
4. Backend sinh storage_key ngẫu nhiên.
5. Backend ghi file thành bản tạm vào uploads/, sau đó đổi tên atomically trong cùng filesystem.
6. Backend INSERT metadata vào Neon.
7. Nếu INSERT lỗi: dọn file đã ghi và trả lỗi.
8. Backend trả response 201; Vue cập nhật danh sách.
```

Vì filesystem và Neon không có cùng transaction, cần quy tắc dọn file khi lỗi và về sau có thể bổ sung job reconciliation cho file rác.

### B. Xem danh sách và preview

```text
1. Vue GET /api/files.
2. FastAPI SELECT metadata từ Neon.
3. Vue render card.
4. Browser GET /api/files/{id}/content.
5. Backend tìm storage_key bằng id trong Neon, đọc file local và stream về browser.
```

### C. Xóa

```text
1. Vue hiển thị hộp thoại xác nhận.
2. Vue DELETE /api/files/{id}.
3. Backend xác thực ID tồn tại; xử lý xóa file local + row trong Neon.
4. Nếu một bước lỗi, ghi log và trả lỗi rõ ràng; cân nhắc cơ chế dọn/reconcile.
5. Vue cập nhật danh sách.
```

**Quy tắc nghiệp vụ:** Không bao giờ để frontend tự truy cập filesystem hoặc kết nối thẳng Neon.

## 9. Cấu hình môi trường

`backend/.env` chỉ lưu trên máy; **không commit**:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=10
```

- Lấy Neon connection string từ Neon Console. Với SQLAlchemy + psycopg, thay tiền tố `postgresql://` thành `postgresql+psycopg://` nếu cần.
- Với Neon, sử dụng kết nối TLS (`sslmode=require`), không đưa credential vào client Vue.
- `UPLOAD_DIR` được backend resolve tương đối với thư mục backend hoặc đặt absolute path tại runtime; không phụ thuộc vào cwd tùy tiện.
- `.env.example` chỉ lưu placeholder, không chứa mật khẩu thật.

Frontend dùng proxy của Vite trong `vite.config.ts`:

```ts
server: {
  port: 5173,
  proxy: {
    '/api': 'http://127.0.0.1:8000',
  },
},
```

Khi chạy local không cần Nginx, frontend chỉ gọi URL tương đối `/api/...`.

## 10. Thiết kế giao diện

**Màn hình chính duy nhất:** header tên Mini Drive, vùng drag-and-drop/chọn file, thông báo upload, danh sách ảnh/file dạng lưới, nút preview/download/delete. Responsive trên desktop và mobile.

**Các trạng thái cần có:** loading, empty, upload success, upload failed, file not found, server disconnected, deleting.

**TypeScript:** định nghĩa `FileItem` và `ApiError` rõ ràng; UI không tự suy đoán fields JSON.

## 11. Chất lượng và an toàn tối thiểu

- Chạy local trên `127.0.0.1`, không mở dịch vụ ra mạng ngoài khi chưa bổ sung auth.
- Không commit `.env`, `uploads/**` hoặc file chứa thông tin nhạy cảm.
- Giới hạn file 10 MiB, kiểm soát kích thước thực tế khi stream thay vì chỉ tin `Content-Length`.
- Không sử dụng đường dẫn/filename client làm path lưu trữ; chống path traversal.
- Cho preview chỉ một allowlist loại ảnh; cấu hình `X-Content-Type-Options: nosniff`.
- Không render HTML do người dùng upload như trang cùng origin.
- Logging có request ID, lỗi xử lý; tránh log secret hoặc toàn bộ dữ liệu file.
- Tách storage adapter/service đủ để chuyển sang MinIO sau này.

## 12. Kế hoạch triển khai theo từng mốc

### Phase 1 — Local-first, KHÔNG Docker

1. Khởi tạo frontend Vue + TypeScript + Vite.
2. Khởi tạo backend FastAPI, kiểm tra `/api/health`.
3. Kết nối Neon PostgreSQL và chạy migration tạo bảng `files`.
4. Tạo local storage service, upload file vào `uploads/`.
5. Tạo API list/preview/download/delete.
6. Kết nối Vue với API và hoàn thành UI.
7. Test upload, reload, download, delete, trường hợp lỗi.

**Tiêu chí hoàn thành Phase 1:** Sau khi restart frontend/backend, file vẫn còn trong `uploads/`, metadata vẫn còn trên Neon và UI vẫn hiển thị chính xác.

### Phase 2 — Học Nginx (sau MVP)

Thêm `nginx/nginx.conf`; cấu hình `/ -> frontend`, `/api -> backend`. Thực hành location, proxy_pass, header, reverse proxy. Vẫn có thể chạy các process trên host.

### Phase 3 — Học Docker & Docker Compose

Viết Dockerfile frontend/backend, học lệnh build/run, volume bind mount hoặc named volume cho `uploads/`, networking và Compose. Database Neon vẫn ở cloud, không cần container Postgres.

### Phase 4 — Chuyển local storage sang MinIO

Thêm MinIO service và volume; triển khai storage interface để chọn LocalStorage hoặc MinioStorage. Giữ API frontend ổn định; thiết kế di chuyển dữ liệu từ uploads sang MinIO. Khi cần, bổ sung `/image` trong Nginx với truy cập an toàn.

### Phase 5 — GitLab CI/CD

- Merge request: install → lint/typecheck → test → Docker build (không deploy).
- Merge vào default branch: test → build → deploy tới môi trường đã cấu hình.
- Git tag: Docker build và tag image theo version; không mặc định push/deploy nếu challenge không yêu cầu.

**Quan trọng:** Chỉ viết các file cấu hình của phase tiếp theo khi bắt đầu học phase đó.

## 13. Lệnh chạy local (dự kiến sau khi có source code)

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Cổng truy cập: `http://localhost:5173` (UI), `http://127.0.0.1:8000/docs` (FastAPI Swagger UI). Các lệnh chỉ dùng được khi đã tạo mã nguồn trong giai đoạn triển khai.

## 14. Checklist nghiệm thu Phase 1

- [ ] Vue chạy trên 5173; FastAPI chạy trên 8000.
- [ ] Frontend gọi `/api` thông qua Vite proxy.
- [ ] Neon đã có bảng `files` bằng migration.
- [ ] Upload thành công, file thật nằm trong `backend/uploads/`.
- [ ] Reload trang vẫn hiển thị file.
- [ ] Preview ảnh, download file hoạt động.
- [ ] Xóa làm mất metadata và file local.
- [ ] File >10 MiB hoặc tên/path bất thường không gây lỗi hệ thống hoặc ghi ngoài uploads.
- [ ] Không có mật khẩu trong Git repo và không có Docker/Nginx/MinIO trong runtime.

## 15. Nguyên tắc làm việc với coding agent

- Trước mỗi bước, giải thích **mục tiêu, file sẽ tạo/sửa và cách kiểm tra**.
- Hoàn thành và test xong một bước mới chuyển bước tiếp theo.
- Không tự ý đổi stack, thêm authentication, framework CSS, Docker, Nginx hoặc MinIO.
- Giữ API contract ổn định và tránh trộn xử lý HTTP, nghiệp vụ và filesystem vào một file.
- Nếu cần đổi kiến trúc, cập nhật PROJECT_BIBLE trước khi code.
- Không thực hiện thao tác phá hủy dữ liệu trên Neon hoặc thư mục uploads khi chưa được cho phép.

---

**Quyết định hiện tại:** Local storage + Neon PostgreSQL + Vue/TypeScript + FastAPI. Học từng công nghệ, ghép hạ tầng về sau.

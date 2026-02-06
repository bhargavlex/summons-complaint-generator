# Docker Compose – Setup & Troubleshooting

**Use the shared `docker-compose.yml` at project root (lines 1–90). Everyone runs the same file.**

## Quick start

From the **project root** (where `docker-compose.yml` lives):

```bash
docker compose up -d
```

Or explicitly:

```bash
docker compose -f docker-compose.yml up -d
```

- **MySQL**: `localhost:3307` (user `appuser`, password `apppass`, database `appdb`)
- **Redis**: `localhost:6379` (password `redispass`)
- **Backend API**: http://localhost:8000

The backend container will:
1. Wait for MySQL to be ready
2. Run DB init (create tables + seed templates) via `scripts.init_db_mysql`
3. Start uvicorn

---

## Common errors and fixes

### 1. `open ... buildx\.lock: Access is denied`

**Cause**: Docker Desktop or the buildx daemon doesn’t have permission to use its lock file.

**Try**:
- **Restart Docker Desktop** (right‑click tray icon → Restart).
- Run your terminal (or Cursor) **as Administrator** and run `docker compose build` again.
- In Docker Desktop: **Settings → Resources → File sharing** – ensure the project directory (e.g. `D:\New folder\summons-complaint-generator`) is allowed.
- If it still fails, in PowerShell (Admin):  
  `Remove-Item $env:USERPROFILE\.docker\buildx\.lock -ErrorAction SilentlyContinue`  
  then restart Docker Desktop and build again.

---

### 2. `ModuleNotFoundError: No module named 'scripts'` (inside container)

**Cause**: A command was run with the wrong working directory.

**Fix**: Run Python modules from the **backend** context. Inside the backend container the app lives in `/app`, so:

```bash
docker compose exec backend python -m scripts.init_db_mysql
```

If you see this when **building** the image, the Dockerfile is likely running a command from the wrong directory; the image is set up so that `WORKDIR` is `/app` and `scripts` is at `/app/scripts`.

---

### 3. `Access denied for user 'appuser'@'...'` (MySQL)

**Cause**: DB not ready yet, or wrong host/port/password.

**Fix**:
- Backend uses `mysql:3306` **inside** the Docker network (not `localhost:3307`). Compose sets `DATABASE_URL=mysql+pymysql://appuser:apppass@mysql:3306/appdb`. Don’t change the host to `localhost` inside the backend container.
- Ensure MySQL is healthy before the backend starts (Compose `depends_on` + healthcheck). If the backend starts too early, restart: `docker compose restart backend`.
- Verify MySQL:  
  `docker compose exec mysql mysql -u appuser -papppass -e "SELECT 1;" appdb`

---

### 4. Backend exits with “connection refused” to MySQL

**Cause**: Backend started before MySQL was accepting connections.

**Fix**: Entrypoint already waits for `mysql:3306`. If it still fails:
- Increase MySQL `healthcheck` `start_period` in `docker-compose.yml`, or
- Run init manually after MySQL is up:  
  `docker compose up -d mysql`  
  wait ~30s, then  
  `docker compose up -d backend`

---

### 5. `Template file not found` or missing `.docx` in preview

**Cause**: Templates are expected under `backend/templates/` (e.g. `Premises - 1 plt. and 1deft_.docx`). The backend container mounts `./backend:/app`, so `backend/templates/` on the host is `/app/templates/` in the container.

**Fix**: Put your `.docx` templates in `backend/templates/` on the host. If you use a different path, set `TEMPLATE_DIR` in the backend service in `docker-compose.yml` and ensure that path is mounted.

---

### 6. Rebuild after code or Dockerfile changes

```bash
docker compose build backend
docker compose up -d
```

To rebuild with no cache:

```bash
docker compose build --no-cache backend
docker compose up -d
```

---

### 7. Run DB init manually (e.g. after first deploy)

```bash
docker compose exec backend python -m scripts.init_db_mysql
```

---

### 8. View backend logs

```bash
docker compose logs -f backend
```

---

## Summary of what runs in Docker

| Step | What happens |
|------|----------------|
| `docker compose up` | Starts MySQL (port 3307), Redis (6379), backend (8000). |
| Backend entrypoint | Waits for `mysql:3306`, runs `scripts.init_db_mysql`, then starts uvicorn. |
| Init script | Uses `DATABASE_URL` from env; creates tables and seeds templates (no SQLite patch). |

If you hit an error not listed here, check `docker compose logs backend` and the exact message for connection, file, or module errors.

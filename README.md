# Summons & Complaint Generator

How to run the app (backend + frontend, with database).

---

## Option 1: Docker (backend + MySQL + Redis)

Use Docker for the database and backend; run the frontend locally.

### 1. Start MySQL, Redis, and Backend

From the **project root**:

```bash
docker-compose up -d mysql redis backend
```

- **Backend**: http://localhost:8000  
- **MySQL**: port 3307 (host) → 3306 (container)  
- **Redis**: port 6379  

### 2. Seed the database (first time only)

Connect to the backend container and run the init script:

```bash
docker exec -it fastapi_server python -m app.db.init_db
```

Or, if you run the backend **locally** (see Option 2), from the `backend` folder:

```bash
cd backend
python setup_db.py
# or: python -m app.db.init_db
```

### 3. Run the frontend

From the **project root**:

```bash
cd frontend
npm install
npm run dev
```

- **Frontend**: http://localhost:3000 (Vite proxies `/api` to http://localhost:8000)

### 4. Use the app

1. Open http://localhost:3000  
2. Choose **Firm** and **Case Category** (from DB)  
3. Optionally upload files, then **Proceed to Extraction**  
4. On the extraction screen: edit fields, refresh preview, download DOCX  

---

## Option 2: Run backend and frontend locally (no Docker backend)

You still need **MySQL** and **Redis** (via Docker or installed locally).

### 1. Start MySQL and Redis (Docker)

```bash
docker-compose up -d mysql redis
```

Set env so the backend talks to MySQL on the host:

- **Windows (PowerShell)**:
  ```powershell
  $env:DATABASE_URL = "mysql+pymysql://appuser:apppass@localhost:3307/appdb"
  ```
- **Linux/macOS**:
  ```bash
  export DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb
  ```

(If MySQL is on 3306, use `localhost:3306` and the right user/password/database.)

### 2. Backend (from project root)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
python setup_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **API**: http://localhost:8000  
- **Docs**: http://localhost:8000/docs  

### 3. Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

- **App**: http://localhost:3000  

---

## Quick reference

| What              | Command / URL                                      |
|-------------------|----------------------------------------------------|
| Backend API       | http://localhost:8000                              |
| API docs          | http://localhost:8000/docs                         |
| Firms endpoint    | GET http://localhost:8000/api/v1/firms            |
| Case types        | GET http://localhost:8000/api/v1/case-types        |
| Frontend          | http://localhost:3000 (after `npm run dev`)        |
| Seed DB (Docker)  | `docker exec -it fastapi_server python -m app.db.init_db` |
| Seed DB (local)   | `cd backend && python setup_db.py`                 |

---

## Troubleshooting

- **"Not Found" for firms/case types**  
  - Backend must be running and DB seeded: run `setup_db.py` or `python -m app.db.init_db` once.

- **Database connection errors**  
  - With Docker MySQL: use `DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb` (port **3307** on host).  
  - Ensure MySQL and Redis are up: `docker-compose ps`.

- **Frontend can’t reach API**  
  - Vite proxy sends `/api` to port 8000. Start the backend first and confirm http://localhost:8000/health returns `{"status":"healthy"}`.

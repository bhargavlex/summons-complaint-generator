# Database Requirements for Preview Generation

## ⚠️ Database is REQUIRED

The preview generation feature **absolutely requires** a database connection because it needs to:

1. **Query Sessions** - Get session by UUID
2. **Get Template** - Retrieve the template file path from the database
3. **Get Field Values** - Fetch all field values (extracted/manual) for the session
4. **Map Placeholders** - Use TemplateField records to map placeholders to values

**Without a database, the preview endpoint will fail.**

## Database Setup Options

### Option 1: Using Docker (Recommended)

**Start MySQL via Docker:**
```bash
# From project root
docker-compose up -d mysql

# Wait ~30 seconds for MySQL to be ready
```

**Important Port Note:**
- Docker MySQL is exposed on port **3307** (not 3306)
- Update your `.env` file to use port 3307 when running locally

**Create/Update `backend/.env`:**
```env
# For local development (connecting to Docker MySQL)
DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redispass
REDIS_DB=0
DEBUG=True
```

### Option 2: Local MySQL Installation

If you have MySQL installed locally on port 3306:

**Create `backend/.env`:**
```env
# For local MySQL (default port)
DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3306/appdb
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redispass
REDIS_DB=0
DEBUG=True
```

## Quick Setup Checklist

1. **Start MySQL** (Docker or local)
   ```bash
   # Docker:
   docker-compose up -d mysql
   
   # Or use your local MySQL installation
   ```

2. **Create `.env` file** in `backend/` directory with correct port:
   - Docker MySQL: port **3307**
   - Local MySQL: port **3306**

3. **Initialize Database:**
   ```bash
   cd backend
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   
   python -m app.db.init_db
   ```

4. **Verify Database Connection:**
   ```bash
   # Test connection
   python -c "from app.db.base import engine; engine.connect(); print('✓ Database connected!')"
   ```

## Port Configuration Summary

| Setup | MySQL Host | Port | DATABASE_URL |
|-------|-----------|------|--------------|
| Docker (local dev) | localhost | 3307 | `mysql+pymysql://appuser:apppass@localhost:3307/appdb` |
| Docker (in container) | mysql | 3306 | `mysql+pymysql://appuser:apppass@mysql:3306/appdb` |
| Local MySQL | localhost | 3306 | `mysql+pymysql://appuser:apppass@localhost:3306/appdb` |

## Running the Server

### With Docker (Full Stack)
```bash
# From project root
docker-compose up backend
```
This automatically:
- Starts MySQL on port 3307 (exposed)
- Starts Redis
- Starts backend with correct DATABASE_URL (`mysql:3306`)

### Without Docker (Local Development)
```bash
# 1. Start MySQL (Docker or local)
docker-compose up -d mysql  # If using Docker

# 2. Start backend locally
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting Database Connection

### Error: "Can't connect to MySQL server"
- **Check MySQL is running:**
  ```bash
  # Docker:
  docker ps | grep mysql
  # Should show mysql_server running
  
  # Local:
  # Check your MySQL service is running
  ```

- **Check port in `.env`:**
  - Docker MySQL: port **3307**
  - Local MySQL: port **3306**

- **Test connection manually:**
  ```bash
  # Docker MySQL:
  mysql -h localhost -P 3307 -u appuser -papppass appdb
  
  # Local MySQL:
  mysql -h localhost -P 3306 -u appuser -papppass appdb
  ```

### Error: "Unknown database 'appdb'"
- Run database initialization:
  ```bash
  python -m app.db.init_db
  ```

### Error: "Access denied"
- Check username/password in `.env` matches MySQL setup
- Default: `appuser` / `apppass`

## What the Preview Service Needs from Database

When you call `/api/v1/sessions/{uuid}/preview`, the service:

1. **Queries `sessions` table** → Gets session by UUID
2. **Queries `templates` table** → Gets template file path
3. **Queries `field_values` table** → Gets all values for the session
4. **Queries `template_fields` table** → Maps placeholders to field keys
5. **Merges values** → Creates preview DOCX file

All of this requires an active database connection!

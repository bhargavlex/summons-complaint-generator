# Preview Editor - Complete Setup Guide

This guide walks you through setting up and accessing the Interactive Preview Editor from scratch.

## Prerequisites

- Docker and Docker Compose installed
- A web browser (Chrome, Firefox, Edge, etc.)

## Step-by-Step Instructions

### Step 1: Start Docker Containers

Open a terminal/PowerShell in the project root directory and start all services:

```bash
docker-compose up -d
```

This will start:
- MySQL database (port 3307)
- Redis (port 6379)
- FastAPI backend (port 8000)

**Wait ~30 seconds** for MySQL to fully initialize.

**Verify containers are running:**
```bash
docker ps
```

You should see:
- `mysql_server` - Up (healthy)
- `redis_server` - Up
- `fastapi_server` - Up

---

### Step 2: Configure Database Connection

Create the `.env` file in the `backend` directory:

**File:** `backend/.env`

```env
DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb
```

**Important:** Use port `3307` (not 3306) because Docker maps MySQL's internal port 3306 to host port 3307.

---

### Step 3: Initialize Database

Initialize the database with tables and seed data:

```bash
docker exec fastapi_server python -m app.db.init_db
```

**Expected output:**
```
Creating database tables...
✓ Tables created successfully

Seeding law firms...
✓ Firm already exists: COHAN LAW, PLLC (ID: 1)
✓ Firm already exists: Smith & Associates (ID: 2)

Seeding case types...
✓ Case type already exists: Premises Liability (ID: 1)
...

✅ Database initialization complete!
```

---

### Step 4: Create a Test Session

Create a test session with sample field values:

```bash
docker exec fastapi_server python -m scripts.test_preview
```

**Expected output:**
```
============================================================
Testing Preview Generation
============================================================

1. Creating test session with field values...
Using template: Premises Liability - 1 Plt. and 1 Deft. (ID: 1)
Created test session: <session-uuid> (ID: 1)
Found 20 template fields
Created 20 field values for session <session-uuid>

2. Testing preview generation...
✓ Preview generated successfully: /app/previews/session_<session-uuid>_preview.docx
✓ Preview file exists: /app/previews/session_<session-uuid>_preview.docx (XXXXX bytes)

============================================================
✓ All tests passed!
Session UUID: <session-uuid>
Preview endpoint: GET /api/v1/sessions/<session-uuid>/preview
============================================================
```

**Note the Session UUID** from the output - you'll need it in the next step.

---

### Step 5: Get Session UUID (Alternative Method)

If you need to get the session UUID later, use:

```bash
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid); db.close()"
```

This will output the UUID of the most recent session.

---

### Step 6: Access the Preview Editor in Browser

Open your web browser and navigate to:

```
http://localhost:8000/api/v1/sessions/<session-uuid>/preview/edit
```

**Replace `<session-uuid>`** with the actual UUID from Step 4.

**Example:**
```
http://localhost:8000/api/v1/sessions/df4fefc0-fb27-40b6-9f0f-64078d220dec/preview/edit
```

---

### Step 7: Verify the Editor is Working

You should see:

1. **Header** with:
   - "📄 Preview Editor" title
   - "⬇️ Download DOCX" button
   - "🔄 Regenerate Preview" button

2. **Left Panel** - "📝 Field Values":
   - List of all editable fields
   - Each field shows:
     - Display name
     - Badge (Manual/Extracted)
     - Input field with current value
     - Placeholder and field key

3. **Right Panel** - "👁️ Preview":
   - Status message showing preview is ready
   - "Download to View" button

---

## Quick Test Workflow

1. **Edit a field:**
   - Click on any field input
   - Change the value (e.g., change "John Doe" to "Jane Smith")
   - Wait ~500ms (auto-saves)
   - See green success message: "Field updated successfully. Preview updated on server."

2. **Download the preview:**
   - Click "⬇️ Download DOCX" button
   - File downloads: `session_<uuid>_preview.docx`
   - Open in Microsoft Word to verify changes

3. **Regenerate preview manually:**
   - Click "🔄 Regenerate Preview" button
   - See status message: "Preview regenerated successfully"
   - Download again to see updated file

---

## Troubleshooting

### Container not starting

**Check logs:**
```bash
docker logs fastapi_server
docker logs mysql_server
```

**Restart containers:**
```bash
docker-compose restart
```

### Database connection error

**Verify `.env` file exists:**
```bash
cat backend/.env
```

**Check MySQL is healthy:**
```bash
docker ps | grep mysql
```

**Reinitialize database:**
```bash
docker exec fastapi_server python -m app.db.init_db
```

### No sessions found

**Create a test session:**
```bash
docker exec fastapi_server python -m scripts.test_preview
```

### Preview editor shows 404

**Verify session UUID is correct:**
```bash
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid if s else 'No sessions'); db.close()"
```

**Check server is running:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Template not found error

**Verify template files exist:**
```bash
docker exec fastapi_server ls -la /app/templates/
```

**Check database has templates:**
```bash
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Template; db = SessionLocal(); t = db.query(Template).first(); print(f'Template: {t.name if t else \"None\"} - Path: {t.file_path if t else \"N/A\"}'); db.close()"
```

---

## Complete Command Reference

### Start Everything
```bash
# Start all services
docker-compose up -d

# Wait for MySQL (30 seconds)
Start-Sleep -Seconds 30

# Initialize database
docker exec fastapi_server python -m app.db.init_db

# Create test session
docker exec fastapi_server python -m scripts.test_preview

# Get session UUID
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid); db.close()"
```

### Stop Everything
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker logs fastapi_server -f
docker logs mysql_server -f
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker restart fastapi_server
```

---

## API Endpoints Reference

### Preview Editor (HTML)
```
GET http://localhost:8000/api/v1/sessions/{session_uuid}/preview/edit
```

### Download Preview (DOCX)
```
GET http://localhost:8000/api/v1/sessions/{session_uuid}/preview
```

### Get All Fields (JSON)
```
GET http://localhost:8000/api/v1/sessions/{session_uuid}/fields
```

### Update Field Value
```
PATCH http://localhost:8000/api/v1/sessions/{session_uuid}/fields/{field_value_id}
Content-Type: application/json

{
  "value": "New Value"
}
```

### Regenerate Preview (No Download)
```
POST http://localhost:8000/api/v1/sessions/{session_uuid}/preview/regenerate
```

---

## Next Steps

1. **Edit field values** in the browser
2. **See real-time updates** (preview regenerates automatically)
3. **Download DOCX** when ready
4. **Open in Word** to verify merged values

---

## Summary

1. ✅ `docker-compose up -d` - Start services
2. ✅ Create `backend/.env` with database URL
3. ✅ `docker exec fastapi_server python -m app.db.init_db` - Initialize DB
4. ✅ `docker exec fastapi_server python -m scripts.test_preview` - Create session
5. ✅ Open browser: `http://localhost:8000/api/v1/sessions/{uuid}/preview/edit`
6. ✅ Edit fields and download preview!

**That's it!** You're ready to use the Interactive Preview Editor. 🎉

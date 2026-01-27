# Preview Feature Testing Guide

Complete guide for testing the preview generation functionality, including setup, test scripts, API testing, and the interactive preview editor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup (Docker)](#quick-setup-docker)
3. [Testing Methods](#testing-methods)
4. [Interactive Preview Editor](#interactive-preview-editor)
5. [Test Scripts](#test-scripts)
6. [API Testing](#api-testing)
7. [Testing Checklist](#testing-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker and Docker Compose** installed
- **MySQL Database** (via Docker or local)
- **Web Browser** for testing the interactive editor

---

## Quick Setup (Docker)

### Step 1: Start Services

```bash
# Start all services (MySQL, Redis, FastAPI)
docker-compose up -d

# Wait ~30 seconds for MySQL to initialize
```

### Step 2: Configure Database

Create `backend/.env` file:

```env
DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb
```

**Important:** Use port `3307` (not 3306) when connecting to Docker MySQL from host.

### Step 3: Initialize Database

```bash
docker exec fastapi_server python -m app.db.init_db
```

**Expected Output:**
```
Creating database tables...
✓ Tables created successfully
Seeding law firms...
Seeding case types...
✅ Database initialization complete!
```

### Step 4: Verify Server is Running

```bash
# Check health
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Or open in browser
# http://localhost:8000/docs (API documentation)
```

---

## Testing Methods

### Method 1: Quick Test Script (Recommended)

Creates a test session and generates a preview:

```bash
docker exec fastapi_server python -m scripts.test_preview
```

**What it does:**
- Creates a test session with sample field values
- Generates a preview file
- Displays the session UUID for further testing

**Expected Output:**
```
============================================================
Testing Preview Generation
============================================================

1. Creating test session with field values...
Using template: Premises Liability - 1 Plt. and 1 Deft. (ID: 1)
Created test session: <uuid> (ID: 1)
Found 20 template fields
Created 20 field values for session <uuid>

2. Testing preview generation...
✓ Preview generated successfully: /app/previews/session_<uuid>_preview.docx
✓ Preview file exists: /app/previews/session_<uuid>_preview.docx (XXXXX bytes)

============================================================
✓ All tests passed!
Session UUID: <uuid>
Preview endpoint: GET /api/v1/sessions/<uuid>/preview
============================================================
```

**Note the Session UUID** - you'll need it for other tests!

---

## Test Scripts

### 1. Basic Preview Test

```bash
# Create test session and generate preview
docker exec fastapi_server python -m scripts.test_preview
```

### 2. Simple API Endpoint Test

```bash
# Test the preview API endpoint
docker exec fastapi_server python -m scripts.test_preview_simple <session_uuid>
```

**What it tests:**
- HTTP status code (200)
- Content-Type header
- File download
- File size

### 3. Complete Test Suite

```bash
# Run comprehensive tests (download, overwrite, error handling)
docker exec fastapi_server python -m scripts.test_preview_complete
```

**What it tests:**
- ✅ **Test 1:** Basic preview download
- ✅ **Test 2:** Overwrite functionality (updates DB, regenerates, verifies overwrite)
- ✅ **Test 3:** Error handling (invalid session UUID → 404)

**Expected Output:**
```
============================================================
Complete Preview Feature Test
============================================================

Test 1: Basic Preview Download
✓ Test 1 PASSED

Testing Overwrite Functionality
✓ Test 2 PASSED

Test 3: Error Handling (Invalid Session)
✓ Test 3 PASSED

✅ All tests passed!
```

---

## Interactive Preview Editor

### Access the Editor

1. **Get a session UUID:**
   ```bash
   docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid if s else 'No sessions'); db.close()"
   ```

2. **Open in browser:**
   ```
   http://localhost:8000/api/v1/sessions/<session_uuid>/preview/edit
   ```

### Features to Test

- ✅ **View all fields** - See all field values in editable form
- ✅ **Edit field values** - Change values and see auto-save (500ms debounce)
- ✅ **Real-time preview update** - Preview regenerates automatically on server
- ✅ **Download DOCX** - Click "Download DOCX" button to get the file
- ✅ **Manual regenerate** - Click "Regenerate Preview" button

### Testing Workflow

1. Open the editor in browser
2. Edit a field value (e.g., change "John Doe" to "Jane Smith")
3. Wait ~500ms - see success message: "Field updated successfully. Preview updated on server."
4. Click "⬇️ Download DOCX" to download the updated file
5. Open in Microsoft Word to verify the change

---

## API Testing

### Get Session UUID

```bash
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid); db.close()"
```

### Test Preview Download

#### Using Browser
Simply navigate to:
```
http://localhost:8000/api/v1/sessions/<session_uuid>/preview
```
The browser will download the preview file automatically.

#### Using curl
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/<session_uuid>/preview" \
  --output preview.docx
```

#### Using PowerShell
```powershell
$sessionUuid = "<session_uuid>"
$url = "http://localhost:8000/api/v1/sessions/$sessionUuid/preview"
Invoke-WebRequest -Uri $url -OutFile "preview.docx"
```

#### Using Python
```python
import requests

session_uuid = "<your-session-uuid>"
response = requests.get(f"http://localhost:8000/api/v1/sessions/{session_uuid}/preview")

if response.status_code == 200:
    with open("preview.docx", "wb") as f:
        f.write(response.content)
    print("Preview downloaded successfully!")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Test Field Update API

```bash
# Update a field value
curl -X PATCH "http://localhost:8000/api/v1/sessions/<session_uuid>/fields/<field_value_id>" \
  -H "Content-Type: application/json" \
  -d '{"value": "New Value"}'
```

### Test Preview Regeneration (No Download)

```bash
# Regenerate preview without downloading
curl -X POST "http://localhost:8000/api/v1/sessions/<session_uuid>/preview/regenerate"
```

---

## Testing Checklist

### Setup & Prerequisites
- [ ] Docker containers are running (`docker ps`)
- [ ] Database initialized (`docker exec fastapi_server python -m app.db.init_db`)
- [ ] `.env` file exists with correct `DATABASE_URL`
- [ ] Server is accessible (`curl http://localhost:8000/health`)

### Basic Functionality
- [ ] Test script creates session successfully
- [ ] Preview file is generated
- [ ] Preview file contains merged values (not placeholders)
- [ ] Preview file can be opened in Microsoft Word
- [ ] File size is reasonable (~30-50KB for typical document)

### Overwrite Functionality
- [ ] First preview generation creates file correctly
- [ ] Editing a field and regenerating overwrites the file
- [ ] Overwritten file has updated values
- [ ] File timestamp is updated on overwrite

### API Endpoints
- [ ] `GET /api/v1/sessions/{uuid}/preview` returns file (200)
- [ ] `GET /api/v1/sessions/{uuid}/fields` returns JSON list
- [ ] `PATCH /api/v1/sessions/{uuid}/fields/{id}` updates value
- [ ] `POST /api/v1/sessions/{uuid}/preview/regenerate` regenerates without download
- [ ] `GET /api/v1/sessions/{uuid}/preview/edit` shows HTML editor

### Error Handling
- [ ] Invalid session UUID returns 404
- [ ] Missing template file shows proper error
- [ ] Database connection errors are handled gracefully
- [ ] Proper error messages are displayed

### Interactive Editor
- [ ] Editor page loads without errors
- [ ] All fields are displayed and editable
- [ ] Field updates save automatically (500ms debounce)
- [ ] Preview regenerates on server when field is updated
- [ ] Download button works correctly
- [ ] Status messages appear (success/error)
- [ ] Manual/Extracted badges update correctly

---

## Verify Preview File

### Check File Exists

```bash
# Inside Docker container
docker exec fastapi_server ls -lh /app/previews/

# Should show: session_<uuid>_preview.docx
```

### Verify Content

1. **Download the preview file** (via browser or API)
2. **Open in Microsoft Word**
3. **Check that:**
   - All placeholders (like `«Plaintiff_name_»`) are replaced with actual values
   - Merged values match what's in the database
   - No placeholders remain in the document
   - Formatting is preserved

---

## Troubleshooting

### Error: "Session not found" (404)

**Causes:**
- Session UUID is incorrect
- Session doesn't exist in database
- Database connection issue

**Solutions:**
```bash
# Verify session exists
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).filter(SessionModel.uuid == '<uuid>').first(); print('Found' if s else 'Not found'); db.close()"

# Create a new test session
docker exec fastapi_server python -m scripts.test_preview
```

### Error: "Template file not found" (500)

**Causes:**
- Template file path in database is incorrect
- Template file doesn't exist at specified location
- `TEMPLATE_DIR` setting is wrong

**Solutions:**
```bash
# Check template path in database
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Template; db = SessionLocal(); t = db.query(Template).first(); print(f'Path: {t.file_path if t else \"No template\"}'); db.close()"

# Check if file exists
docker exec fastapi_server ls -la /app/templates/
```

### Error: "Preview file generation failed"

**Causes:**
- `PREVIEW_DIR` is not writable
- Missing field values
- Template merge field mismatch

**Solutions:**
```bash
# Check preview directory permissions
docker exec fastapi_server ls -ld /app/previews/

# Check server logs
docker logs fastapi_server --tail 50

# Verify field values exist
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel, FieldValue; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); fv_count = db.query(FieldValue).filter(FieldValue.session_id == s.id).count() if s else 0; print(f'Field values: {fv_count}'); db.close()"
```

### Preview file is empty or has placeholders

**Causes:**
- Field values don't exist in database
- Placeholder names don't match between template and database
- `final_value` is None for some fields

**Solutions:**
```bash
# Check field values
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel, FieldValue; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); fvs = db.query(FieldValue).filter(FieldValue.session_id == s.id).all() if s else []; print(f'Total fields: {len(fvs)}'); [print(f'{fv.template_field.field_key if fv.template_field else \"N/A\"}: {fv.final_value}') for fv in fvs[:5]]; db.close()"
```

### Database Connection Error

**Causes:**
- MySQL container not running
- Wrong port in `DATABASE_URL`
- `.env` file missing or incorrect

**Solutions:**
```bash
# Check MySQL is running
docker ps | grep mysql

# Verify .env file
cat backend/.env

# Should show: DATABASE_URL=mysql+pymysql://appuser:apppass@localhost:3307/appdb

# Restart MySQL if needed
docker restart mysql_server
```

### Import Errors

**Causes:**
- Dependencies not installed
- Wrong Python environment
- Missing modules

**Solutions:**
```bash
# Install dependencies
docker exec fastapi_server pip install -r /app/requirements.txt

# Check Python path
docker exec fastapi_server python -c "import sys; print(sys.path)"
```

---

## API Endpoints Reference

### Preview Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sessions/{uuid}/preview` | Download preview DOCX file |
| `GET` | `/api/v1/sessions/{uuid}/preview/edit` | Interactive preview editor (HTML) |
| `POST` | `/api/v1/sessions/{uuid}/preview/regenerate` | Regenerate preview (no download) |

### Field Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sessions/{uuid}/fields` | Get all field values (JSON) |
| `PATCH` | `/api/v1/sessions/{uuid}/fields/{id}` | Update a field value |

### Status Codes

- `200` - Success
- `404` - Session/Field not found
- `400` - Invalid request data
- `500` - Server error (check logs)

---

## API Documentation

Once the server is running, view interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Test Results Summary

✅ **All Core Tests Pass:**
- Basic preview generation
- File download functionality
- Overwrite behavior
- Error handling
- Interactive editor
- Field value updates
- Real-time preview regeneration

---

## Next Steps

After verifying all tests pass:

1. **Test with real data** - Use actual document extraction results
2. **Test edge cases** - Empty values, special characters, long text
3. **Performance testing** - Multiple concurrent requests
4. **Integration testing** - With frontend application
5. **User acceptance testing** - With actual users

---

## Quick Reference Commands

```bash
# Start services
docker-compose up -d

# Initialize database
docker exec fastapi_server python -m app.db.init_db

# Create test session
docker exec fastapi_server python -m scripts.test_preview

# Get session UUID
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid); db.close()"

# Run complete test suite
docker exec fastapi_server python -m scripts.test_preview_complete

# Check server logs
docker logs fastapi_server --tail 50

# Stop services
docker-compose down
```

---

**For detailed setup instructions, see:** `PREVIEW_EDITOR_SETUP_GUIDE.md`  
**For functionality explanation, see:** `PREVIEW_FUNCTIONALITY_EXPLAINED.md`

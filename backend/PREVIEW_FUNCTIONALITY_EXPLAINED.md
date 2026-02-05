# Preview Functionality - Complete Explanation

## Overview

The preview functionality generates a DOCX file by merging field values from the database into a Word template. This allows users to see how their extracted or manually entered data will appear in the final document before generating the official version.

---

## Architecture & Data Flow

### 1. **Database Structure**

The preview system relies on these key database models:

```
Session
├── uuid (string) - Unique identifier for the session
├── template_id → Template
└── field_values → FieldValue[]

Template
├── id
├── file_path (string) - Path to the .docx template file
└── fields → TemplateField[]

TemplateField
├── id
├── placeholder (string) - e.g., "«Plaintiff_name_»"
├── field_key (string) - e.g., "plaintiff_name"
└── display_name (string)

FieldValue
├── id
├── session_id → Session
├── template_field_id → TemplateField
├── extracted_value (string) - Value from LLM extraction
├── manual_value (string) - User override (takes priority)
└── final_value (property) - Returns manual_value if set, else extracted_value
```

**Key Concept**: `FieldValue.final_value` is a property that prioritizes `manual_value` over `extracted_value`. This ensures user edits always take precedence.

---

## 2. **Preview Generation Flow**

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. API Request                                                  │
│    GET /api/v1/sessions/{session_uuid}/preview                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. API Endpoint (preview.py)                                    │
│    - Validates session exists (404 if not found)                │
│    - Creates PreviewService instance                            │
│    - Calls preview_service.generate_preview(session)            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. PreviewService.generate_preview()                            │
│                                                                 │
│    a) Get Session's Template                                    │
│       - session.template → Template model                       │
│       - Validates template exists                               │
│                                                                 │
│    b) Build Preview File Path                                   │
│       - Location: {PREVIEW_DIR}/session_{uuid}_preview.docx     │
│       - Creates directory if it doesn't exist                   │
│       - Example: ./previews/session_abc123_preview.docx         │
│                                                                 │
│    c) Fetch All Field Values                                    │
│       - Query: FieldValue WHERE session_id = session.id         │
│       - Gets all field values for this session                 │
│                                                                 │
│    d) Build Merge Dictionary                                    │
│       For each FieldValue:                                       │
│         - Get template_field.placeholder (e.g., "«Name_»")     │
│         - Remove « and » → "Name_"                              │
│         - Get field_value.final_value                           │
│         - Map: {"Name_": "John Doe"}                            │
│                                                                 │
│    e) Resolve Template Path                                     │
│       - Handles absolute/relative paths                         │
│       - Checks TEMPLATE_DIR if relative                         │
│       - Validates file exists                                   │
│                                                                 │
│    f) Merge & Write                                             │
│       - Open template with MailMerge                            │
│       - Merge all values: doc.merge(**values_dict)             │
│       - Write to preview path (overwrites if exists)            │
│       - Return absolute path string                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Return File Response                                         │
│    - FileResponse with correct MIME type                        │
│    - Browser downloads the file automatically                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. **Key Implementation Details**

### Placeholder Cleaning

Templates use placeholders like `«Plaintiff_name_»`, but `MailMerge` expects field names without the `«` and `»` characters:

```python
# Template has: «Plaintiff_name_»
# MailMerge needs: Plaintiff_name_

placeholder = template_field.placeholder  # "«Plaintiff_name_»"
merge_field_name = placeholder.replace('«', '').replace('»', '')  # "Plaintiff_name_"
```

### Value Priority (final_value)

The `FieldValue` model has a `final_value` property that ensures user edits take priority:

```python
@property
def final_value(self):
    """Returns manual_value if set, otherwise extracted_value"""
    return self.manual_value if self.manual_value else self.extracted_value
```

**Why this matters**: If a user manually edits a field value, that edit should appear in the preview, not the original extracted value.

### Overwrite Behavior

The preview file is **always overwritten** on each generation:

```python
# Same filename every time
preview_filename = f"session_{session.uuid}_preview.docx"

# MailMerge.write() automatically overwrites existing files
doc.write(str(preview_path))
```

This ensures:
- Only one preview file per session exists
- Updated field values are reflected immediately
- No accumulation of old preview files

### Template Path Resolution

The `_resolve_template_path()` method handles multiple path scenarios:

1. **Absolute path**: Use directly if it exists
2. **Relative path**: Try relative to backend directory
3. **Template directory**: Use `TEMPLATE_DIR` setting if relative path fails

This flexibility allows templates to be stored in different locations.

---

## 4. **Testing Strategy**

We use a **three-tier testing approach**:

### Tier 1: Unit/Service Testing (`test_preview.py`)

**Purpose**: Test the core `PreviewService` logic directly (no HTTP layer)

**What it does**:
1. Creates a test session with sample field values
2. Calls `PreviewService.generate_preview()` directly
3. Verifies the preview file is created and has content

**Usage**:
```bash
docker exec fastapi_server python -m scripts.test_preview
```

**Output**:
- Creates a session with UUID
- Generates preview file
- Reports success/failure
- Provides session UUID for API testing

**When to use**: Testing the service logic in isolation, debugging merge issues

---

### Tier 2: API Endpoint Testing (`test_preview_simple.py`)

**Purpose**: Test the HTTP API endpoint end-to-end

**What it does**:
1. Makes HTTP GET request to `/api/v1/sessions/{uuid}/preview`
2. Downloads the DOCX file
3. Verifies response status, content type, and file size

**Usage**:
```bash
docker exec fastapi_server python -m scripts.test_preview_simple <session_uuid>
```

**Output**:
- HTTP status code (200 = success)
- Content-Type header
- File size
- Saved file location

**When to use**: Verifying the API endpoint works correctly, testing from external tools

---

### Tier 3: Comprehensive Integration Testing (`test_preview_complete.py`)

**Purpose**: Test all aspects including overwrite behavior and error handling

**What it tests**:

#### Test 1: Basic Download
- Downloads preview file successfully
- Verifies file exists and has content
- Checks HTTP 200 status

#### Test 2: Overwrite Functionality
- Downloads first preview
- Updates a field value in the database
- Downloads second preview
- Verifies:
  - Same filename (overwritten, not duplicated)
  - File timestamp updated
  - File size may change (if content changed)

#### Test 3: Error Handling
- Tests invalid session UUID
- Verifies 404 response
- Checks error message format

**Usage**:
```bash
docker exec fastapi_server python -m scripts.test_preview_complete
```

**Output**:
- Detailed test results for each scenario
- Pass/fail status for each test
- Summary of all tests

**When to use**: Full regression testing, verifying overwrite behavior, testing error cases

---

## 5. **Testing Workflow Example**

### Complete Testing Session

```bash
# Step 1: Create test data
docker exec fastapi_server python -m scripts.test_preview
# Output: Session UUID: 780b3c1b-895a-48ee-a0fc-863d7a2dcd7c

# Step 2: Test API endpoint
docker exec fastapi_server python -m scripts.test_preview_simple 780b3c1b-895a-48ee-a0fc-863d7a2dcd7c
# Output: ✓ Preview downloaded successfully

# Step 3: Run comprehensive tests
docker exec fastapi_server python -m scripts.test_preview_complete
# Output: ✓ All tests passed!
```

### Manual Browser Testing

1. Get session UUID:
   ```bash
   docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid); db.close()"
   ```

2. Open in browser:
   ```
   http://localhost:8000/api/v1/sessions/{session_uuid}/preview
   ```

3. Browser automatically downloads the preview file

4. Open in Microsoft Word to verify merged values

---

## 6. **Error Handling**

The preview system handles several error scenarios:

### Session Not Found (404)
```python
if not session:
    raise HTTPException(status_code=404, detail=f"Session not found: {session_uuid}")
```

### Template File Not Found (500)
```python
except FileNotFoundError as e:
    raise HTTPException(status_code=500, detail=f"Template file not found: {str(e)}")
```

### Session Has No Template (400)
```python
if not session.template:
    raise ValueError(f"Session {session.uuid} has no associated template")
```

### Missing Field Values
- Empty values are converted to empty strings: `value if value is not None else ""`
- Missing fields in the merge dictionary result in empty placeholders in the output

---

## 7. **Configuration**

Preview behavior is controlled by settings in `app/core/config.py`:

```python
TEMPLATE_DIR: str = "./templates"  # Where template files are stored
PREVIEW_DIR: str = "./previews"    # Where preview files are generated
```

These can be overridden via `.env` file or environment variables.

---

## 8. **File Locations**

### In Docker Container
- **Templates**: `/app/templates/`
- **Previews**: `/app/previews/`
- **Generated files**: `/app/previews/session_{uuid}_preview.docx`

### On Host Machine
- **Templates**: `backend/templates/`
- **Previews**: `backend/previews/`

---

## 9. **Key Technologies**

- **FastAPI**: Web framework for the API endpoint
- **SQLAlchemy**: ORM for database queries
- **docx-mailmerge2** (`MailMerge`): Library for merging data into DOCX templates
- **pathlib.Path**: Modern path handling
- **FileResponse**: FastAPI's file download response type

---

## 10. **Common Issues & Solutions**

### Issue: Preview file has placeholders instead of values
**Cause**: Field values not found or `final_value` is None
**Solution**: Check that `FieldValue` records exist for the session and have non-null values

### Issue: 404 Error
**Cause**: Session UUID doesn't exist in database
**Solution**: Verify session exists: `SELECT * FROM sessions WHERE uuid = '...'`

### Issue: Template file not found
**Cause**: Template path in database doesn't match actual file location
**Solution**: Check `templates.file_path` in database and verify file exists

### Issue: Preview not updating after field edit
**Cause**: Preview file cached or not regenerated
**Solution**: Preview is overwritten on each request - make sure you're calling the endpoint again

---

## Summary

The preview functionality provides a seamless way to preview merged documents:

1. **Data Flow**: Session → Field Values → Merge Dictionary → MailMerge → Preview File
2. **Priority**: Manual values override extracted values
3. **Overwrite**: Each generation overwrites the previous preview
4. **Testing**: Three-tier approach (service, API, comprehensive)
5. **Error Handling**: Comprehensive error messages for debugging

The system is designed to be reliable, testable, and user-friendly, ensuring users always see the most up-to-date preview of their document.

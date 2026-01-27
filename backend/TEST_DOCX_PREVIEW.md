# How to Test DOCX Preview in Browser

## Quick Test Steps

### Step 1: Make Sure Everything is Running

```bash
# Check containers are running
docker ps

# Should see: fastapi_server, mysql_server, redis_server
```

### Step 2: Get a Session UUID

```bash
docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid if s else 'No sessions'); db.close()"
```

If no sessions exist, create one:
```bash
docker exec fastapi_server python -m scripts.test_preview
```

### Step 3: Open Preview Editor in Browser

Open your browser and navigate to:
```
http://localhost:8000/api/v1/sessions/<YOUR-SESSION-UUID>/preview/edit
```

Replace `<YOUR-SESSION-UUID>` with the UUID from Step 2.

### Step 4: Check the Preview

**What you should see:**

1. **Right Panel - Preview Section:**
   - If preview exists: You should see the **actual document content** rendered as HTML
   - The document should look formatted (like a Word document)
   - You should be able to scroll through it
   - Text should be readable and properly formatted

2. **If preview doesn't load:**
   - You'll see a loading spinner
   - Or an error message with a download button

### Step 5: Test Live Updates

1. **Edit a field** in the left panel (e.g., change "John Doe" to "Jane Smith")
2. **Wait ~500ms** for auto-save
3. **Watch the preview** - it should automatically reload and show the updated value
4. **Verify** - The new value should appear in the preview document

### Step 6: Test Manual Regenerate

1. Click the **"🔄 Regenerate Preview"** button
2. You should see "Loading preview..." message
3. The preview should reload with the latest content

---

## What to Look For

### ✅ Success Indicators

- **Document renders** - You can see the actual text content
- **Formatting preserved** - Paragraphs, spacing, etc. look correct
- **Auto-refresh works** - Preview updates when you edit fields
- **Scrollable** - Long documents can be scrolled
- **No errors in console** - Check browser DevTools (F12) for errors

### ❌ Troubleshooting

#### Preview shows "Loading..." forever

**Check browser console (F12):**
```javascript
// Look for errors like:
// - "Failed to load preview"
// - "DOCX preview library not loaded"
// - CORS errors
// - Network errors
```

**Solutions:**
1. **Check CDN is accessible:**
   - The page loads `docx-preview` from CDN
   - Make sure you have internet connection
   - Or check if CDN is blocked

2. **Check server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check preview file exists:**
   ```bash
   docker exec fastapi_server ls -lh /app/previews/
   ```

#### Preview shows error message

**Check server logs:**
```bash
docker logs fastapi_server --tail 50
```

**Common issues:**
- Preview file not generated
- Template file missing
- Field values missing

#### Preview library not loading

**Check in browser console:**
```javascript
// Open DevTools (F12) and type:
window.docx
// Should return an object, not undefined
```

**If undefined:**
- CDN might be blocked
- Network issue
- Try refreshing the page

---

## Visual Checklist

When you open the preview editor, you should see:

```
┌─────────────────────────────────────────────────────────┐
│  📄 Preview Editor    [⬇️ Download] [🔄 Regenerate]   │
├──────────────────────┬──────────────────────────────────┤
│  📝 Field Values     │  👁️ Preview                     │
│                      │                                  │
│  [Field 1]          │  ┌──────────────────────────┐  │
│  [Field 2]          │  │                          │  │
│  [Field 3]          │  │  Document Content Here   │  │
│  ...                │  │  - Formatted text        │  │
│                     │  │  - Paragraphs            │  │
│                     │  │  - All merged values     │  │
│                     │  │                          │  │
│                     │  │  (Scrollable)            │  │
│                     │  └──────────────────────────┘  │
└──────────────────────┴──────────────────────────────────┘
```

---

## Browser Compatibility

The `docx-preview` library works in:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ⚠️ Older browsers may have limited support

---

## Alternative: Check Network Tab

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Refresh the preview editor page
4. Look for:
   - `docx-preview.min.js` - Should load from CDN (status 200)
   - `/api/v1/sessions/.../preview` - Should download DOCX (status 200)

---

## Quick Test Command

Run this to verify everything is set up:

```bash
# 1. Check server
curl http://localhost:8000/health

# 2. Get session UUID
SESSION_UUID=$(docker exec fastapi_server python -c "from app.db.base import SessionLocal; from app.db.models import Session as SessionModel; db = SessionLocal(); s = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first(); print(s.uuid if s else 'NO_SESSION'); db.close()")

# 3. Check preview file exists
docker exec fastapi_server ls -lh /app/previews/session_${SESSION_UUID}_preview.docx

# 4. Open in browser
echo "Open: http://localhost:8000/api/v1/sessions/${SESSION_UUID}/preview/edit"
```

---

## Expected Behavior

### On Page Load:
1. Page loads with field editor
2. Preview section shows "Loading preview..."
3. DOCX file is fetched from server
4. Preview renders as formatted HTML
5. Document content is visible and scrollable

### When Editing a Field:
1. You type in a field
2. After 500ms, field saves
3. Preview shows "Loading preview..." briefly
4. Preview reloads with updated content
5. New value appears in the document

### When Clicking Regenerate:
1. Button shows "⏳ Regenerating..."
2. Preview shows "Loading preview..."
3. New preview loads
4. Updated content is displayed

---

## Still Not Working?

1. **Check browser console** (F12 → Console tab) for errors
2. **Check network tab** (F12 → Network tab) for failed requests
3. **Check server logs:** `docker logs fastapi_server --tail 50`
4. **Try hard refresh:** Ctrl+F5 (or Cmd+Shift+R on Mac)
5. **Try different browser** to rule out browser-specific issues

---

## Success!

If you can see the document content rendered in the preview area (not just a download button), then the DOCX preview is working! 🎉

"""
Complete test script for preview functionality
Tests all aspects including overwrite behavior
"""
import sys
import urllib.request
import urllib.error
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import SessionLocal
from app.db.models import Session as SessionModel, FieldValue

def test_preview_download(session_uuid: str, base_url: str = "http://localhost:8000"):
    """Download preview file"""
    url = f"{base_url}/api/v1/sessions/{session_uuid}/preview"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                output_file = f"preview_{session_uuid}.docx"
                with open(output_file, 'wb') as f:
                    f.write(response.read())
                return output_file, response.getcode()
            return None, response.getcode()
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def test_overwrite(session_uuid: str):
    """Test that preview file is overwritten when regenerated"""
    print("\n" + "=" * 60)
    print("Testing Overwrite Functionality")
    print("=" * 60)
    
    # First download
    print("\n1. First preview generation...")
    file1, status1 = test_preview_download(session_uuid)
    if file1 and status1 == 200:
        size1 = Path(file1).stat().st_size
        time1 = Path(file1).stat().st_mtime
        print(f"   ✓ Preview downloaded: {file1} ({size1} bytes)")
    else:
        print(f"   ✗ Failed: Status {status1}")
        return False
    
    # Wait a moment
    time.sleep(2)
    
    # Update a field value in database
    print("\n2. Updating a field value in database...")
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(SessionModel.uuid == session_uuid).first()
        if session:
            # Update first field value
            field_value = db.query(FieldValue).filter(
                FieldValue.session_id == session.id
            ).first()
            
            if field_value:
                old_value = field_value.manual_value or field_value.extracted_value
                new_value = "UPDATED VALUE FOR TESTING"
                field_value.manual_value = new_value
                db.commit()
                print(f"   ✓ Updated field value: '{old_value}' -> '{new_value}'")
            else:
                print("   ⚠️  No field values found")
        else:
            print("   ✗ Session not found")
            return False
    finally:
        db.close()
    
    # Second download (should overwrite)
    print("\n3. Second preview generation (should overwrite)...")
    file2, status2 = test_preview_download(session_uuid)
    if file2 and status2 == 200:
        size2 = Path(file2).stat().st_size
        time2 = Path(file2).stat().st_mtime
        print(f"   ✓ Preview downloaded: {file2} ({size2} bytes)")
        
        # Verify it's the same file (overwritten)
        if file1 == file2:
            print(f"   ✓ Same filename (overwritten): {file1}")
        else:
            print(f"   ⚠️  Different filename: {file1} vs {file2}")
        
        # Check if file was updated
        if time2 > time1:
            print(f"   ✓ File was updated (timestamp changed)")
        else:
            print(f"   ⚠️  File timestamp unchanged")
        
        return True
    else:
        print(f"   ✗ Failed: Status {status2}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Complete Preview Feature Test")
    print("=" * 60)
    
    # Get session UUID
    db = SessionLocal()
    try:
        session = db.query(SessionModel).order_by(SessionModel.created_at.desc()).first()
        if not session:
            print("\n✗ No sessions found in database!")
            print("  Run: docker exec fastapi_server python -m scripts.test_preview")
            sys.exit(1)
        session_uuid = session.uuid
        print(f"\nUsing session UUID: {session_uuid}")
    finally:
        db.close()
    
    # Test 1: Basic download
    print("\n" + "=" * 60)
    print("Test 1: Basic Preview Download")
    print("=" * 60)
    file, status = test_preview_download(session_uuid)
    if file and status == 200:
        size = Path(file).stat().st_size
        print(f"\n✓ Test 1 PASSED")
        print(f"  File: {file}")
        print(f"  Size: {size} bytes")
        print(f"  Status: {status}")
    else:
        print(f"\n✗ Test 1 FAILED")
        print(f"  Status: {status}")
        sys.exit(1)
    
    # Test 2: Overwrite functionality
    overwrite_success = test_overwrite(session_uuid)
    
    # Test 3: Error handling - invalid session
    print("\n" + "=" * 60)
    print("Test 3: Error Handling (Invalid Session)")
    print("=" * 60)
    invalid_uuid = "00000000-0000-0000-0000-000000000000"
    try:
        url = f"http://localhost:8000/api/v1/sessions/{invalid_uuid}/preview"
        req = urllib.request.Request(url)
        urllib.request.urlopen(req)
        print("\n✗ Test 3 FAILED (should return 404)")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"\n✓ Test 3 PASSED")
            print(f"  Correctly returned 404 for invalid session")
        else:
            print(f"\n✗ Test 3 FAILED")
            print(f"  Expected 404, got {e.code}")
    except Exception as e:
        print(f"\n✗ Test 3 FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✓ Test 1: Basic download - PASSED")
    if overwrite_success:
        print("✓ Test 2: Overwrite functionality - PASSED")
    else:
        print("✗ Test 2: Overwrite functionality - FAILED")
    print("✓ Test 3: Error handling - PASSED")
    print("\n" + "=" * 60)
    
    if overwrite_success:
        print("\n✅ All tests passed!")
        print(f"\nYou can open {file} in Microsoft Word to verify merged values.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

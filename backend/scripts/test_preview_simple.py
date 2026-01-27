"""
Simple test script for preview endpoint (no external dependencies)
"""
import sys
import urllib.request
import urllib.error
from pathlib import Path

def test_preview_endpoint(session_uuid: str, base_url: str = "http://localhost:8000"):
    """Test the preview endpoint"""
    url = f"{base_url}/api/v1/sessions/{session_uuid}/preview"
    
    print("=" * 60)
    print("Testing Preview API Endpoint")
    print("=" * 60)
    print(f"\nSession UUID: {session_uuid}")
    print(f"URL: {url}\n")
    
    try:
        print("Making request...")
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'N/A')
            content_length = response.headers.get('Content-Length', 'N/A')
            
            print(f"✓ Status Code: {status_code}")
            print(f"✓ Content-Type: {content_type}")
            print(f"✓ Content-Length: {content_length} bytes")
            
            # Save the file
            output_file = f"preview_{session_uuid}.docx"
            with open(output_file, 'wb') as f:
                f.write(response.read())
            
            file_size = Path(output_file).stat().st_size
            print(f"\n✓ Preview downloaded successfully!")
            print(f"  File: {output_file}")
            print(f"  Size: {file_size} bytes")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"\n✗ HTTP Error: {e.code}")
        print(f"  {e.reason}")
        if e.code == 404:
            print("\n  Session not found. Make sure:")
            print("  1. The session UUID is correct")
            print("  2. Run: docker exec fastapi_server python -m scripts.test_preview")
        return False
    except urllib.error.URLError as e:
        print(f"\n✗ Connection Error: {e.reason}")
        print("  Make sure the server is running at", base_url)
        return False
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        session_uuid = sys.argv[1]
    else:
        session_uuid = "780b3c1b-895a-48ee-a0fc-863d7a2dcd7c"
        print(f"Using default session UUID: {session_uuid}\n")
    
    success = test_preview_endpoint(session_uuid)
    sys.exit(0 if success else 1)

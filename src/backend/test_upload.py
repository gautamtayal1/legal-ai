#!/usr/bin/env python3
"""
Simple test script for document upload functionality.
Run this to test S3 upload and database persistence without a frontend.
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid

load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000/api"

def create_test_file():
    """Create a simple test PDF file for uploading."""
    test_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
269
%%EOF"""
    
    test_file_path = "test_document.pdf"
    with open(test_file_path, "wb") as f:
        f.write(test_content)
    return test_file_path

def test_document_upload():
    """Test document upload functionality."""
    print("🧪 Testing Document Upload...")
    
    # Create test file
    test_file_path = create_test_file()
    
    try:
        # Upload document
        with open(test_file_path, "rb") as f:
            files = {
                "file": (test_file_path, f, "application/pdf")
            }
            data = {
                "message_id": "test-message-123",
                "user_id": "test-user-456"
            }
            
            response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"   📄 Document ID: {result['id']}")
            print(f"   📁 Filename: {result['filename']}")
            print(f"   🔗 S3 URL: {result['document_url']}")
            print(f"   📊 File size: {result['file_size']} bytes")
            return result
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_list_documents():
    """Test listing documents."""
    print("\n📋 Testing Document List...")
    
    try:
        response = requests.get(f"{BASE_URL}/documents/")
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Found {len(documents)} documents")
            for doc in documents:
                print(f"   📄 {doc['filename']} (ID: {doc['id']})")
            return documents
        else:
            print(f"❌ List failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_health_check():
    """Test if the API is running."""
    print("🏥 Testing API Health...")
    
    try:
        response = requests.get(f"http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Start it with: cd src/backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Document Upload Tests...\n")
    
    # Check if API is running
    if not test_health_check():
        exit(1)
    
    # Test upload
    upload_result = test_document_upload()
    
    # Test listing
    test_list_documents()
    
    print("\n✨ Tests completed!")
    
    # Instructions
    print("\n📝 To run more tests:")
    print("   python test_upload.py")
    print("\n🔧 To start the backend server:")
    print("   cd src/backend && python main.py") 
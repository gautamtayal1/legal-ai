#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        if package_name:
            importlib.import_module(package_name)
        else:
            importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

def main():
    """Test all critical dependencies."""
    print("Testing dependencies...")
    print("=" * 50)
    
    # Core dependencies
    core_deps = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pydantic",
        "alembic"
    ]
    
    # AWS dependencies
    aws_deps = [
        "boto3",
        "aioboto3",
        "aiobotocore",
        "aiohttp",
        "yarl",
        "multidict",
        "async_timeout",
        "propcache"
    ]
    
    # Document processing
    doc_deps = [
        "PyPDF2",
        "pdfplumber", 
        "docx",
        "chardet",
        "PIL",
        "fitz",
        "aiofiles"
    ]
    
    # AI/ML dependencies
    ai_deps = [
        "openai",
        "langchain",
        "tiktoken",
        "chromadb"
    ]
    
    # Test all dependencies
    all_deps = core_deps + aws_deps + doc_deps + ai_deps
    
    failed_imports = []
    
    for dep in all_deps:
        if not test_import(dep):
            failed_imports.append(dep)
    
    print("=" * 50)
    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        sys.exit(1)
    else:
        print("✅ All dependencies imported successfully!")
        
    # Test specific critical imports
    print("\nTesting critical application imports...")
    try:
        from utils.s3_service import upload_file
        print("✅ S3 service imported successfully")
    except Exception as e:
        print(f"❌ S3 service import failed: {e}")
        sys.exit(1)
        
    try:
        from api.routers import documents
        print("✅ Documents router imported successfully")
    except Exception as e:
        print(f"❌ Documents router import failed: {e}")
        sys.exit(1)
        
    print("✅ All critical imports successful!")

if __name__ == "__main__":
    main() 
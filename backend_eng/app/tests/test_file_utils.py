import pytest
import os
import shutil
from fastapi import UploadFile
from unittest.mock import MagicMock, patch
from app.utils.file_utils import (
    ensure_upload_dirs,
    save_upload_file,
    save_pdf_file,
    save_photo_file,
    generate_inspection_pdf,
    PDF_UPLOAD_DIR,
    PHOTO_UPLOAD_DIR
)


@pytest.fixture(scope="function")
def cleanup_upload_dirs():
    """Clean up upload directories after tests"""
    yield
    if os.path.exists(PDF_UPLOAD_DIR):
        shutil.rmtree(PDF_UPLOAD_DIR)
    if os.path.exists(PHOTO_UPLOAD_DIR):
        shutil.rmtree(PHOTO_UPLOAD_DIR)


def test_ensure_upload_dirs(cleanup_upload_dirs):
    """Test that upload directories are created"""
    # Remove directories if they exist
    if os.path.exists(PDF_UPLOAD_DIR):
        shutil.rmtree(PDF_UPLOAD_DIR)
    if os.path.exists(PHOTO_UPLOAD_DIR):
        shutil.rmtree(PHOTO_UPLOAD_DIR)
    
    # Call the function
    ensure_upload_dirs()
    
    # Check that directories exist
    assert os.path.exists(PDF_UPLOAD_DIR)
    assert os.path.exists(PHOTO_UPLOAD_DIR)


@pytest.mark.asyncio
async def test_save_upload_file(cleanup_upload_dirs):
    """Test saving an uploaded file"""
    # Create a mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"
    # Use a coroutine for read method
    async def mock_read():
        return b"test content"
    mock_file.read = mock_read
    
    # Call the function
    file_path = await save_upload_file(mock_file, PDF_UPLOAD_DIR)
    
    # Check that the file was saved
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
        assert content == b"test content"


@pytest.mark.asyncio
async def test_save_pdf_file(cleanup_upload_dirs):
    """Test saving a PDF file"""
    # Create a mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    # Use a coroutine for read method
    async def mock_read():
        return b"%PDF-1.5\ntest pdf content"
    mock_file.read = mock_read
    
    # Call the function
    file_path = await save_pdf_file(mock_file)
    
    # Check that the file was saved in the PDF directory
    assert os.path.exists(file_path)
    assert file_path.startswith(PDF_UPLOAD_DIR)
    with open(file_path, "rb") as f:
        content = f.read()
        assert content == b"%PDF-1.5\ntest pdf content"


@pytest.mark.asyncio
async def test_save_photo_file(cleanup_upload_dirs):
    """Test saving a photo file"""
    # Create a mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    # Use a coroutine for read method
    async def mock_read():
        return b"test image content"
    mock_file.read = mock_read
    
    # Call the function
    file_path = await save_photo_file(mock_file)
    
    # Check that the file was saved in the photo directory
    assert os.path.exists(file_path)
    assert file_path.startswith(PHOTO_UPLOAD_DIR)
    with open(file_path, "rb") as f:
        content = f.read()
        assert content == b"test image content"


def test_generate_inspection_pdf(cleanup_upload_dirs):
    """Test generating an inspection PDF"""
    # Create mock inspection data
    class MockInspection:
        def __init__(self):
            self.subproject_name = "Test Subproject"
            self.inspection_form_name = "Test Form"
            self.inspection_date = "2025-04-29"
            self.location = "Test Location"
            self.timing = "檢驗停留點"
            self.result = "合格"
            self.remark = "Test remark"
    
    # Create mock photos data (empty list for simplicity)
    photos_data = []
    
    # Call the function
    file_path = generate_inspection_pdf(MockInspection(), photos_data)
    
    # Check that the PDF was generated
    assert os.path.exists(file_path)
    assert file_path.startswith(PDF_UPLOAD_DIR)
    assert file_path.endswith(".pdf")
    
    # Basic check that it's a PDF file
    with open(file_path, "rb") as f:
        content = f.read()
        assert content.startswith(b"%PDF")

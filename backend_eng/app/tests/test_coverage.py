import pytest
import os
import io
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from app.main import app
from app.db.database import get_db
from app.utils.file_utils import generate_inspection_pdf
from app.models.models import Project, ConstructionInspection, InspectionPhoto
from sqlalchemy.orm import Session
from PIL import Image

client = TestClient(app)

# 測試 PDF 上傳功能 (inspections.py 行 55-68)
def test_upload_inspection_pdf(client, db: Session):
    """Test uploading a PDF for an inspection"""
    # 創建一個專案
    project_data = {
        "name": "PDF Test Project",
        "location": "Test Location",
        "contractor": "Test Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "owner": "test_owner"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    # 創建一個檢查
    inspection_data = {
        "project_id": project_id,
        "subproject_name": "PDF Test Subproject",
        "inspection_form_name": "PDF Test Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "檢驗停留點",
        "result": "合格",
        "remark": "PDF test remark"
    }
    create_response = client.post("/api/inspections/", json=inspection_data)
    inspection_id = create_response.json()["id"]
    
    # 模擬 PDF 檔案上傳
    with patch('app.api.inspections.save_pdf_file') as mock_save_pdf:
        mock_save_pdf.return_value = "app/static/uploads/pdfs/test.pdf"
        
        # 創建一個測試 PDF 檔案
        test_file = io.BytesIO(b"PDF test content")
        
        # 上傳 PDF
        response = client.post(
            f"/api/inspections/{inspection_id}/upload-pdf",
            files={"file": ("test.pdf", test_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inspection_id
        assert data["pdf_path"] == "app/static/uploads/pdfs/test.pdf"
        mock_save_pdf.assert_called_once()

# 測試 PDF 生成功能 (inspections.py 行 77-91)
def test_generate_inspection_pdf(client, db: Session):
    """Test generating a PDF report for an inspection"""
    # 創建一個專案
    project_data = {
        "name": "PDF Gen Test Project",
        "location": "Test Location",
        "contractor": "Test Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "owner": "test_owner"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    # 創建一個檢查
    inspection_data = {
        "project_id": project_id,
        "subproject_name": "PDF Gen Test Subproject",
        "inspection_form_name": "PDF Gen Test Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "檢驗停留點",
        "result": "合格",
        "remark": "PDF gen test remark"
    }
    create_response = client.post("/api/inspections/", json=inspection_data)
    inspection_id = create_response.json()["id"]
    
    # 模擬 PDF 生成
    with patch('app.api.inspections.generate_inspection_pdf') as mock_generate_pdf:
        mock_generate_pdf.return_value = "app/static/uploads/pdfs/generated_test.pdf"
        
        # 生成 PDF
        response = client.post(f"/api/inspections/{inspection_id}/generate-pdf")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inspection_id
        assert data["pdf_path"] == "app/static/uploads/pdfs/generated_test.pdf"
        mock_generate_pdf.assert_called_once()

# 測試照片 API 的更新功能 (photos.py 行 25-41)
def test_update_photo(client, db: Session):
    """Test updating a photo via API"""
    # 創建一個專案
    project_data = {
        "name": "Photo Update Test Project",
        "location": "Test Location",
        "contractor": "Test Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "owner": "test_owner"
    }
    create_response = client.post("/api/projects/", json=project_data)
    project_id = create_response.json()["id"]
    
    # 創建一個檢查
    inspection_data = {
        "project_id": project_id,
        "subproject_name": "Photo Update Test Subproject",
        "inspection_form_name": "Photo Update Test Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "檢驗停留點",
        "result": "合格",
        "remark": "Photo update test remark"
    }
    create_response = client.post("/api/inspections/", json=inspection_data)
    inspection_id = create_response.json()["id"]
    
    # 模擬照片上傳
    with patch('app.api.photos.save_photo_file') as mock_save_photo:
        mock_save_photo.return_value = "app/static/uploads/photos/test.jpg"
        
        # 創建一個測試照片檔案
        test_file = io.BytesIO(b"Photo test content")
        
        # 上傳照片
        response = client.post(
            "/api/photos/",
            data={
                "inspection_id": str(inspection_id),
                "capture_date": str(date.today()),
                "caption": "Test Caption"
            },
            files={"file": ("test.jpg", test_file, "image/jpeg")}
        )
        
        assert response.status_code == 201
        photo_id = response.json()["id"]
        
        # 更新照片
        update_data = {
            "inspection_id": inspection_id,
            "photo_path": "app/static/uploads/photos/test.jpg",
            "capture_date": str(date.today()),
            "caption": "Updated Caption"
        }
        
        response = client.put(f"/api/photos/{photo_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == photo_id
        assert data["caption"] == "Updated Caption"

# 測試 file_utils.py 中的 generate_inspection_pdf 函數 (行 75-84)
def test_generate_inspection_pdf_function():
    """Test the generate_inspection_pdf function directly"""
    # 直接模擬 generate_inspection_pdf 函數
    with patch('app.utils.file_utils.uuid.uuid4') as mock_uuid, \
         patch('app.utils.file_utils.os.path.join') as mock_join, \
         patch('app.utils.file_utils.ensure_upload_dirs') as mock_ensure_dirs, \
         patch('app.utils.file_utils.SimpleDocTemplate') as mock_doc, \
         patch('app.utils.file_utils.getSampleStyleSheet') as mock_styles, \
         patch('app.utils.file_utils.Paragraph') as mock_para, \
         patch('app.utils.file_utils.Spacer') as mock_spacer, \
         patch('app.utils.file_utils.RLImage') as mock_image, \
         patch('app.utils.file_utils.os.path.exists') as mock_exists:
        
        # 設置模擬返回值
        mock_uuid.return_value = "test-uuid"
        mock_join.return_value = "app/static/uploads/pdfs/inspection_test-uuid.pdf"
        mock_ensure_dirs.return_value = None
        mock_doc.return_value = MagicMock()
        mock_styles.return_value = {'Title': MagicMock(), 'Normal': MagicMock(), 'Heading2': MagicMock()}
        mock_para.return_value = MagicMock()
        mock_spacer.return_value = MagicMock()
        mock_image.return_value = MagicMock()
        mock_exists.return_value = True
        
        # 創建測試資料
        inspection = MagicMock()
        inspection.subproject_name = "Test Subproject"
        inspection.inspection_form_name = "Test Form"
        inspection.inspection_date = date.today()
        inspection.location = "Test Location"
        inspection.timing = "檢驗停留點"
        inspection.result = "合格"
        inspection.remark = "Test remark"
        
        # 測試無照片的情況
        from app.utils.file_utils import generate_inspection_pdf
        pdf_path = generate_inspection_pdf(inspection, [])
        assert pdf_path == "app/static/uploads/pdfs/inspection_test-uuid.pdf"
        mock_ensure_dirs.assert_called_once()
        
        # 測試有照片的情況
        photo = MagicMock()
        photo.photo_path = "app/static/uploads/photos/test.jpg"
        photo.caption = "Test Caption"
        photo.capture_date = date.today()
        
        pdf_path = generate_inspection_pdf(inspection, [photo])
        assert pdf_path == "app/static/uploads/pdfs/inspection_test-uuid.pdf"
        mock_exists.assert_called_with("app/static/uploads/photos/test.jpg")

# 測試 main.py 中未覆蓋的行 (43-44)
def test_main_app_directories():
    """Test the directory creation in main.py"""
    # 模擬 os.makedirs 函數
    with patch('os.makedirs') as mock_makedirs:
        # 重新導入 main 模組以觸發目錄創建
        import importlib
        import app.main
        importlib.reload(app.main)
        
        # 驗證 os.makedirs 被調用了兩次，一次用於 pdfs 目錄，一次用於 photos 目錄
        assert mock_makedirs.call_count >= 2
        # 驗證調用參數
        mock_makedirs.assert_any_call("app/static/uploads/pdfs", exist_ok=True)
        mock_makedirs.assert_any_call("app/static/uploads/photos", exist_ok=True)

# 測試 crud.py 中未覆蓋的行 (68-71, 94-99)
def test_crud_edge_cases(db: Session):
    """Test edge cases in CRUD operations"""
    from app.services import crud
    
    # 測試 update_inspection 當找不到檢查時
    with pytest.raises(HTTPException) as excinfo:
        crud.update_inspection(db, 999, None)
    assert excinfo.value.status_code == 404
    
    # 測試 update_photo 當找不到照片時
    with pytest.raises(HTTPException) as excinfo:
        crud.update_photo(db, 999, None)
    assert excinfo.value.status_code == 404

# 測試 crud.py 中的 delete_inspection 函數 (68-71)
def test_delete_inspection(db: Session):
    """Test the delete_inspection function in crud.py"""
    from app.services import crud
    from app.models.models import Project, ConstructionInspection
    
    # 創建測試資料
    project = Project(
        name="Delete Test Project",
        location="Test Location",
        contractor="Test Contractor",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        owner="test_owner"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    inspection = ConstructionInspection(
        project_id=project.id,
        subproject_name="Delete Test Subproject",
        inspection_form_name="Delete Test Form",
        inspection_date=date.today(),
        location="Test Location",
        timing="檢驗停留點",
        result="合格",
        remark="Delete test remark"
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    
    # 測試刪除功能
    deleted_inspection = crud.delete_inspection(db, inspection.id)
    assert deleted_inspection.id == inspection.id
    assert deleted_inspection.subproject_name == "Delete Test Subproject"
    
    # 確認已從資料庫中刪除
    result = db.query(ConstructionInspection).filter(ConstructionInspection.id == inspection.id).first()
    assert result is None

# 測試 projects.py 中未覆蓋的行 (30, 35)
def test_project_api_edge_cases(client):
    """Test edge cases in project API"""
    # 測試更新不存在的專案
    update_data = {
        "name": "Updated Project",
        "location": "Updated Location",
        "contractor": "Updated Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=60)),
        "owner": "test_owner"
    }
    response = client.put("/api/projects/999", json=update_data, headers={"owner": "test_owner"})
    assert response.status_code == 404
    
    # 測試刪除不存在的專案
    response = client.delete("/api/projects/999", headers={"owner": "test_owner"})
    assert response.status_code == 404

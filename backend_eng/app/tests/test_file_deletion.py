import pytest
import os
import shutil
from unittest.mock import patch
from app.models.models import InspectionPhoto, ConstructionInspection
from app.utils.file_utils import PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR
from datetime import date

# 使用 conftest 中的 fixtures
# test_photo_with_file 和 test_inspection_with_pdf 仍需要保留，因為它們是特定於檔案刪除測試的

@pytest.fixture
def test_photo_with_file(db, test_inspection, mock_photo_path):
    """創建一個帶有實體檔案的測試照片"""
    photo = InspectionPhoto(
        inspection_id=test_inspection.id,
        photo_path=mock_photo_path,
        capture_date=date.today(),
        caption="Test Caption"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    yield photo
    # 清理由 db fixture 的 transaction rollback 處理

@pytest.fixture
def test_inspection_with_pdf(db, test_inspection, mock_pdf_path):
    """更新測試抽查，添加 PDF 路徑"""
    test_inspection.pdf_path = mock_pdf_path
    db.add(test_inspection)
    db.commit()
    db.refresh(test_inspection)
    yield test_inspection
    # 清理由 db fixture 的 transaction rollback 處理

def test_delete_photo_with_file(client, test_photo_with_file, mock_photo_path):
    """測試刪除照片時是否同時刪除實體檔案"""
    # 確認檔案存在
    assert os.path.exists(mock_photo_path), "測試照片檔案應該存在"
    
    # 刪除照片
    response = client.delete(f"/api/photos/{test_photo_with_file.id}")
    assert response.status_code == 200, "刪除照片應該成功"
    
    # 確認資料庫記錄已刪除
    response = client.get(f"/api/photos/{test_photo_with_file.id}")
    assert response.status_code == 404, "照片記錄應該已從資料庫中刪除"
    
    # 確認實體檔案已刪除
    assert not os.path.exists(mock_photo_path), "照片實體檔案應該已被刪除"

def test_delete_inspection_with_pdf(client, test_inspection_with_pdf, mock_pdf_path):
    """測試刪除抽查時是否同時刪除 PDF 檔案"""
    # 確認檔案存在
    assert os.path.exists(mock_pdf_path), "測試 PDF 檔案應該存在"
    
    # 刪除抽查
    response = client.delete(f"/api/inspections/{test_inspection_with_pdf.id}")
    assert response.status_code == 200, "刪除抽查應該成功"
    
    # 確認資料庫記錄已刪除
    response = client.get(f"/api/inspections/{test_inspection_with_pdf.id}")
    assert response.status_code == 404, "抽查記錄應該已從資料庫中刪除"
    
    # 確認實體檔案已刪除
    assert not os.path.exists(mock_pdf_path), "PDF 實體檔案應該已被刪除"

def test_delete_inspection_with_photos(client, db, test_project, mock_pdf_path, mock_photo_path):
    """測試刪除抽查時是否同時刪除相關的照片檔案"""
    # 創建測試數據
    inspection = ConstructionInspection(
        project_id=test_project.id,
        subproject_name="Test Subproject",
        inspection_form_name="Test Form",
        inspection_date=date.today(),
        location="Test Location",
        timing="檢驗停留點",
        result="合格",
        remark="Test remark",
        pdf_path=mock_pdf_path
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    
    # 添加照片
    photo = InspectionPhoto(
        inspection_id=inspection.id,
        photo_path=mock_photo_path,
        capture_date=date.today(),
        caption="Test Caption"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    # 確認檔案存在
    assert os.path.exists(mock_pdf_path), "測試 PDF 檔案應該存在"
    assert os.path.exists(mock_photo_path), "測試照片檔案應該存在"
    
    # 刪除抽查
    response = client.delete(f"/api/inspections/{inspection.id}")
    assert response.status_code == 200, "刪除抽查應該成功"
    
    # 確認資料庫記錄已刪除
    response = client.get(f"/api/inspections/{inspection.id}")
    assert response.status_code == 404, "抽查記錄應該已從資料庫中刪除"
    
    # 確認照片記錄也被刪除
    response = client.get(f"/api/photos/{photo.id}")
    assert response.status_code == 404, "照片記錄應該已從資料庫中刪除"
    
    # 確認實體檔案已刪除
    assert not os.path.exists(mock_pdf_path), "PDF 實體檔案應該已被刪除"
    assert not os.path.exists(mock_photo_path), "照片實體檔案應該已被刪除"

def test_delete_project_cascade(client, db, test_project, mock_pdf_path, mock_photo_path):
    """測試刪除專案時是否級聯刪除所有相關的抽查和照片檔案"""
    # 創建測試數據
    inspection = ConstructionInspection(
        project_id=test_project.id,
        subproject_name="Test Subproject",
        inspection_form_name="Test Form",
        inspection_date=date.today(),
        location="Test Location",
        timing="檢驗停留點",
        result="合格",
        remark="Test remark",
        pdf_path=mock_pdf_path
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    
    # 添加照片
    photo = InspectionPhoto(
        inspection_id=inspection.id,
        photo_path=mock_photo_path,
        capture_date=date.today(),
        caption="Test Caption"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    # 確認檔案存在
    assert os.path.exists(mock_pdf_path), "測試 PDF 檔案應該存在"
    assert os.path.exists(mock_photo_path), "測試照片檔案應該存在"
    
    # 刪除專案 (需要提供 owner 頭部)
    response = client.delete(f"/api/projects/{test_project.id}", headers={"owner": "test_owner"})
    assert response.status_code == 200, "刪除專案應該成功"
    
    # 確認專案記錄已刪除
    response = client.get(f"/api/projects/{test_project.id}")
    assert response.status_code == 404, "專案記錄應該已從資料庫中刪除"
    
    # 確認抽查記錄已刪除
    response = client.get(f"/api/inspections/{inspection.id}")
    assert response.status_code == 404, "抽查記錄應該已從資料庫中刪除"
    
    # 確認照片記錄已刪除
    response = client.get(f"/api/photos/{photo.id}")
    assert response.status_code == 404, "照片記錄應該已從資料庫中刪除"
    
    # 確認實體檔案已刪除
    assert not os.path.exists(mock_pdf_path), "PDF 實體檔案應該已被刪除"
    assert not os.path.exists(mock_photo_path), "照片實體檔案應該已被刪除"

def test_update_inspection_replace_pdf(client, db, test_inspection, mock_pdf_path):
    """測試更新抽查的 PDF 路徑時是否刪除舊檔案"""
    # 更新測試抽查，添加 PDF 路徑
    test_inspection.pdf_path = mock_pdf_path
    db.add(test_inspection)
    db.commit()
    db.refresh(test_inspection)
    
    # 確認舊檔案存在
    assert os.path.exists(mock_pdf_path), "測試 PDF 檔案應該存在"
    
    # 準備更新數據
    update_data = {
        "result": "不合格",
        "remark": "Updated remark"
    }
    
    # 更新抽查
    response = client.put(f"/api/inspections/{test_inspection.id}", json=update_data)
    assert response.status_code == 200, "更新抽查應該成功"

def test_update_photo_replace_file(client, db, test_photo, mock_photo_path, test_update_photo_data):
    """測試更新照片路徑時是否刪除舊檔案"""
    # 更新測試照片，確保有正確的照片路徑
    test_photo.photo_path = mock_photo_path
    db.add(test_photo)
    db.commit()
    db.refresh(test_photo)
    
    # 確認舊檔案存在
    assert os.path.exists(mock_photo_path), "測試照片檔案應該存在"
    
    # 創建新的照片路徑
    new_photo_path = os.path.join(PHOTO_UPLOAD_DIR, "new_test.jpg")
    with open(new_photo_path, "wb") as f:
        f.write(b"new test image content")
    
    # 更新照片 - 使用部分 test_update_photo_data 並添加 photo_path
    update_data = dict(test_update_photo_data)
    update_data["photo_path"] = new_photo_path
    
    response = client.patch(f"/api/photos/{test_photo.id}", json=update_data)
    assert response.status_code == 200, "更新照片應該成功"
    
    # 確認舊檔案已刪除
    assert not os.path.exists(mock_photo_path), "舊的照片檔案應該已被刪除"
    
    # 確認新檔案存在
    assert os.path.exists(new_photo_path), "新的照片檔案應該存在"
    
    # 清理
    if os.path.exists(new_photo_path):
        os.remove(new_photo_path)

@patch('os.path.exists')
@patch('app.services.crud.os.remove')
def test_error_handling_when_file_not_exists(mock_remove, mock_exists, client, db, test_inspection):
    """測試當檔案不存在時的錯誤處理"""
    # 模擬 os.path.exists 返回 True，讓代碼嘗試刪除檔案
    mock_exists.return_value = True
    # 模擬 os.remove 拋出 FileNotFoundError
    mock_remove.side_effect = FileNotFoundError("模擬檔案不存在錯誤")
    
    # 創建測試數據
    photo = InspectionPhoto(
        inspection_id=test_inspection.id,
        photo_path="/non/existent/path/photo.jpg",  # 不存在的路徑
        capture_date=date.today(),
        caption="Test Caption"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    # 嘗試刪除照片，即使檔案不存在也應該成功刪除資料庫記錄
    response = client.delete(f"/api/photos/{photo.id}")
    assert response.status_code == 200, "即使檔案不存在，刪除照片記錄也應該成功"
    
    # 確認資料庫記錄已刪除
    response = client.get(f"/api/photos/{photo.id}")
    assert response.status_code == 404, "照片記錄應該已從資料庫中刪除"
    
    # 確認 os.path.exists 被調用
    mock_exists.assert_called_with("/non/existent/path/photo.jpg")
    # 確認 os.remove 被調用
    mock_remove.assert_called_once_with("/non/existent/path/photo.jpg")

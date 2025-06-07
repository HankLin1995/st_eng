import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.database import Base
from app.main import app
from app.db.database import get_db
import os
import sys
import shutil
from datetime import date, timedelta
from app.models.models import Project, ConstructionInspection, InspectionPhoto
from app.schemas import schemas

os.makedirs("app/data", exist_ok=True)  

# 使用記憶體資料庫來加速測試
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# 創建測試引擎和 session factory
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 只創建一次表格，提高測試速度
@pytest.fixture(scope="session")
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(create_tables):
    # 連接到資料庫並開始事務
    connection = engine.connect()
    transaction = connection.begin()
    
    # 綁定 session 到這個連接
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        # 回滾事務而不是刪除表格，這樣更快
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db):
    # 覆蓋 get_db 依賴項以使用測試資料庫
    def override_get_db():
        try:
            yield db
        finally:
            pass  # 不在這裡關閉，由 db fixture 處理
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 重置依賴項覆蓋
    app.dependency_overrides = {}

# 設置測試用的上傳目錄
TEST_PDF_DIR = "app/static/test_uploads/pdfs"
TEST_PHOTO_DIR = "app/static/test_uploads/photos"

@pytest.fixture(scope="module", autouse=True)
def setup_test_dirs():
    """設置測試目錄並在測試結束後清理"""
    # 創建測試目錄
    os.makedirs(TEST_PDF_DIR, exist_ok=True)
    os.makedirs(TEST_PHOTO_DIR, exist_ok=True)
    
    yield
    
    # 清理測試目錄
    if os.path.exists(TEST_PDF_DIR):
        shutil.rmtree(TEST_PDF_DIR)
    if os.path.exists(TEST_PHOTO_DIR):
        shutil.rmtree(TEST_PHOTO_DIR)

@pytest.fixture
def mock_pdf_path():
    """創建一個測試用的 PDF 檔案並返回路徑"""
    pdf_path = os.path.join(TEST_PDF_DIR, "test_inspection.pdf")
    
    # 創建一個空的 PDF 檔案
    with open(pdf_path, "wb") as f:
        f.write(b"Test PDF content")
    
    yield pdf_path
    
    # 測試後清理（如果檔案還存在）
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

@pytest.fixture
def mock_photo_path():
    """創建一個測試用的照片檔案並返回路徑"""
    photo_path = os.path.join(TEST_PHOTO_DIR, "test_photo.jpg")
    
    # 創建一個空的照片檔案
    with open(photo_path, "wb") as f:
        f.write(b"Test photo content")
    
    yield photo_path
    
    # 測試後清理（如果檔案還存在）
    if os.path.exists(photo_path):
        os.remove(photo_path)

@pytest.fixture
def test_project_data():
    """返回用於創建測試專案的資料"""
    return {
        "name": "Test Project",
        "location": "Test Location",
        "contractor": "Test Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "owner": "test_owner"
    }

@pytest.fixture
def test_inspection_data(test_project_id):
    """返回用於創建測試抽查的資料"""
    return {
        "project_id": test_project_id,
        "subproject_name": "Test Subproject",
        "inspection_form_name": "Test Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "檢驗停留點",
        "result": "合格",
        "remark": "Test remark"
    }

@pytest.fixture
def test_project(db):
    """創建一個測試用的專案"""
    project = Project(
        name="Test Project",
        location="Test Location",
        contractor="Test Contractor",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        owner="test_owner"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    yield project
    # 清理由 db fixture 的 transaction rollback 處理

@pytest.fixture
def test_project_id(test_project):
    """返回測試專案的 ID"""
    return test_project.id

@pytest.fixture
def test_inspection(db, test_project_id, mock_pdf_path=None):
    """創建一個測試用的抽查"""
    inspection = ConstructionInspection(
        project_id=test_project_id,
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
    yield inspection
    # 清理由 db fixture 的 transaction rollback 處理

@pytest.fixture
def test_inspection_id(test_inspection):
    """返回測試抽查的 ID"""
    return test_inspection.id

@pytest.fixture
def test_photo(db, test_inspection_id, mock_photo_path):
    """創建一個測試用的照片"""
    photo = InspectionPhoto(
        inspection_id=test_inspection_id,
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
def test_photo_id(test_photo):
    """返回測試照片的 ID"""
    return test_photo.id

@pytest.fixture
def create_project_via_api(client, test_project_data):
    """通過 API 創建專案並返回專案 ID"""
    response = client.post("/api/projects/", json=test_project_data)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
def create_inspection_via_api(client, create_project_via_api):
    """通過 API 創建抽查並返回抽查 ID"""
    inspection_data = {
        "project_id": create_project_via_api,
        "subproject_name": "Test Subproject",
        "inspection_form_name": "Test Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "檢驗停留點",
        "result": "合格",
        "remark": "Test remark"
    }
    response = client.post("/api/inspections/", json=inspection_data)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
def test_spot_check_data(test_project_id):
    """返回用於創建測試隨機抽查的資料"""
    return {
        "project_id": test_project_id,
        "subproject_name": "Test Subproject",
        "inspection_form_name": "Spot Check Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "隨機抽查",
        "result": "合格",
        "remark": "Spot check remark"
    }

@pytest.fixture
def create_spot_check_via_api(client, create_project_via_api):
    """通過 API 創建隨機抽查並返回抽查 ID"""
    spot_check_data = {
        "project_id": create_project_via_api,
        "subproject_name": "Test Subproject",
        "inspection_form_name": "Spot Check Form",
        "inspection_date": str(date.today()),
        "location": "Test Location",
        "timing": "隨機抽查",
        "result": "合格",
        "remark": "Spot check remark"
    }
    response = client.post("/api/inspections/", json=spot_check_data)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
def mock_photo_bytes():
    """創建一個測試用的照片字節數據"""
    import io
    return io.BytesIO(b"fake image content")

@pytest.fixture
def photo_form_data(test_inspection_id):
    """返回用於創建測試照片的表單數據"""
    return {
        "inspection_id": str(test_inspection_id),
        "capture_date": str(date.today()),
        "caption": "Test Caption"
    }

@pytest.fixture
def create_photo_via_api(client, create_inspection_via_api, mock_photo_bytes):
    """通過 API 創建照片並返回照片 ID"""
    photo_data = {
        "inspection_id": str(create_inspection_via_api),
        "capture_date": str(date.today()),
        "caption": "Test Caption"
    }
    files = {
        "file": ("test_photo.jpg", mock_photo_bytes, "image/jpeg")
    }
    response = client.post("/api/photos/", data=photo_data, files=files)
    assert response.status_code == 201
    return response.json()["id"]

@pytest.fixture
def test_update_inspection_data():
    """返回用於更新測試抽查的資料"""
    return {
        "subproject_name": "Updated Subproject",
        "inspection_form_name": "Updated Form",
        "inspection_date": str(date.today() + timedelta(days=1)),
        "location": "Updated Location",
        "timing": "施工中",
        "result": "不合格",
        "remark": "Updated remark"
    }

@pytest.fixture
def test_update_photo_data():
    """返回用於更新測試照片的資料"""
    return {
        "capture_date": str(date.today() + timedelta(days=1)),
        "caption": "Updated Caption"
    }

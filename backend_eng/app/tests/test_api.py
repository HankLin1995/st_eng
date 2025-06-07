import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import json
from app.main import app
import io

def test_read_main(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Construction Inspection API"}

# Project API tests
def test_create_project(client, test_project_data):
    """Test creating a project via API"""
    response = client.post("/api/projects/", json=test_project_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_project_data["name"]
    assert data["location"] == test_project_data["location"]
    assert data["contractor"] == test_project_data["contractor"]
    assert "id" in data

def test_read_projects(client, test_project_data):
    """Test reading all projects via API"""
    # Create a project first
    client.post("/api/projects/", json=test_project_data)
    
    # Get all projects
    response = client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(project["name"] == test_project_data["name"] for project in data)

def test_read_project(client, create_project_via_api):
    """Test reading a specific project via API"""
    project_id = create_project_via_api
    
    # Get the project
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert "inspections" in data

def test_project_owner_validation(client, create_project_via_api, test_project_data):
    """Test project owner validation in API"""
    project_id = create_project_via_api
    owner = test_project_data["owner"]
    
    # Test with correct owner header
    response = client.get(f"/api/projects/{project_id}", headers={"owner": owner})
    assert response.status_code == 200
    
    # Test with incorrect owner header
    response = client.get(f"/api/projects/{project_id}", headers={"owner": "wrong_owner"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]
    
    # Test update with correct owner header
    update_data = {
        "name": "Updated via API",
        "location": "Updated Location",
        "contractor": "Updated Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=45)),
        "owner": "new_owner"  # Owner can be changed if the current owner approves
    }
    response = client.put(f"/api/projects/{project_id}", json=update_data, headers={"owner": owner})
    assert response.status_code == 200
    
    # Test update with incorrect owner header
    response = client.put(f"/api/projects/{project_id}", json=update_data, headers={"owner": "wrong_owner"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]
    
    # Test delete with incorrect owner header
    response = client.delete(f"/api/projects/{project_id}", headers={"owner": "wrong_owner"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_get_projects_by_owner(client, test_project_data):
    """Test getting projects filtered by owner via API"""
    # Create first project with test_owner
    client.post("/api/projects/", json=test_project_data)
    
    # Create second project with different_owner
    different_owner_project = {
        "name": "Different Owner Project",
        "location": "Different Location",
        "contractor": "Different Contractor",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=30)),
        "owner": "different_owner"
    }
    client.post("/api/projects/", json=different_owner_project)
    
    # Get projects with test_owner header
    response = client.get("/api/projects/", headers={"owner": test_project_data["owner"]})
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 1
    assert all(project["owner"] == test_project_data["owner"] for project in projects)
    
    # Get projects with different_owner header
    response = client.get("/api/projects/", headers={"owner": "different_owner"})
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 1
    assert all(project["owner"] == "different_owner" for project in projects)

def test_get_project_storage_info(client, create_project_via_api, test_project_data):
    """Test getting project storage info"""
    project_id = create_project_via_api
    owner = test_project_data["owner"]
    
    # Test with correct owner header
    response = client.get(f"/api/projects/{project_id}/storage", headers={"owner": owner})
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert "total_size_bytes" in data
    assert "file_count" in data
    
    # Test with incorrect owner header
    response = client.get(f"/api/projects/{project_id}/storage", headers={"owner": "wrong_owner"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]
    
    # Test without owner header (should still work as owner is optional for this endpoint)
    response = client.get(f"/api/projects/{project_id}/storage")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id

def test_delete_project(client, create_project_via_api, test_project_data):
    """Test deleting a project via API"""
    project_id = create_project_via_api
    owner = test_project_data["owner"]
    
    # Delete the project with correct owner header
    response = client.delete(f"/api/projects/{project_id}", headers={"owner": owner})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    
    # Verify the project was deleted
    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 404

# Inspection API tests
def test_create_inspection(client, create_project_via_api, test_inspection_data):
    """Test creating an inspection via API"""
    project_id = create_project_via_api
    
    # Update project_id in test_inspection_data
    inspection_data = test_inspection_data.copy()
    inspection_data["project_id"] = project_id
    
    response = client.post("/api/inspections/", json=inspection_data)
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project_id
    assert data["subproject_name"] == inspection_data["subproject_name"]
    assert "id" in data

def test_read_inspections(client, create_inspection_via_api):
    """Test reading all inspections via API"""
    # Get all inspections
    response = client.get("/api/inspections/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    # Get inspections filtered by project_id
    project_id = client.get(f"/api/inspections/{create_inspection_via_api}").json()["project_id"]
    response = client.get(f"/api/inspections/?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(inspection["project_id"] == project_id for inspection in data)

def test_update_inspection(client, create_inspection_via_api, test_update_inspection_data):
    """Test updating an inspection via API"""
    inspection_id = create_inspection_via_api
    
    # Update the inspection
    response = client.put(f"/api/inspections/{inspection_id}", json=test_update_inspection_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inspection_id
    assert data["result"] == test_update_inspection_data["result"]
    
    # Verify the inspection was updated
    response = client.get(f"/api/inspections/{inspection_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == test_update_inspection_data["result"]

def test_update_inspection_preserve_pdf_path(client, create_inspection_via_api):
    """Test that pdf_path is preserved when not included in the update request"""
    inspection_id = create_inspection_via_api
    
    # Upload a PDF file to the inspection
    pdf_bytes = io.BytesIO(b"fake pdf content")
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    upload_response = client.post(f"/api/inspections/{inspection_id}/upload-pdf", files=files)
    assert upload_response.status_code == 200
    
    # Get the inspection to verify the pdf_path
    response = client.get(f"/api/inspections/{inspection_id}")
    assert response.status_code == 200
    inspection_data = response.json()
    pdf_path = inspection_data["pdf_path"]
    assert pdf_path is not None
    
    # Update the inspection without including pdf_path
    update_data = {
        "result": "不合格",
        "remark": "Updated without PDF path"
    }
    response = client.put(f"/api/inspections/{inspection_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify that the pdf_path is still preserved
    assert data["result"] == "不合格"
    assert data["remark"] == "Updated without PDF path"
    assert data["pdf_path"] == pdf_path, "pdf_path should not be changed when not included in update"

def test_delete_inspection(client, create_inspection_via_api):
    """Test deleting an inspection via API"""
    inspection_id = create_inspection_via_api
    
    # Delete the inspection
    response = client.delete(f"/api/inspections/{inspection_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == inspection_id
    
    # Verify the inspection was deleted
    response = client.get(f"/api/inspections/{inspection_id}")
    assert response.status_code == 404

def test_delete_spot_check(client, create_spot_check_via_api, mock_photo_bytes):
    """Test deleting a spot check inspection via API"""
    spot_check_id = create_spot_check_via_api
    
    # Verify the spot check was created
    response = client.get(f"/api/inspections/{spot_check_id}")
    assert response.status_code == 200
    assert response.json()["timing"] == "隨機抽查"
    
    # Add photos to the spot check using the API
    # Create first photo
    photo1_data = {
        "inspection_id": str(spot_check_id),
        "capture_date": str(date.today()),
        "caption": "Spot Check Photo 1"
    }
    files1 = {
        "file": ("photo1.jpg", mock_photo_bytes, "image/jpeg")
    }
    photo1_response = client.post("/api/photos/", data=photo1_data, files=files1)
    assert photo1_response.status_code == 201
    
    # Create second photo
    photo2_data = {
        "inspection_id": str(spot_check_id),
        "capture_date": str(date.today()),
        "caption": "Spot Check Photo 2"
    }
    files2 = {
        "file": ("photo2.jpg", mock_photo_bytes, "image/jpeg")
    }
    photo2_response = client.post("/api/photos/", data=photo2_data, files=files2)
    assert photo2_response.status_code == 201
    
    # Verify photos were added
    response = client.get(f"/api/photos/?inspection_id={spot_check_id}")
    assert response.status_code == 200
    photos_data = response.json()
    assert len(photos_data) == 2
    
    # Delete the spot check
    delete_response = client.delete(f"/api/inspections/{spot_check_id}")
    assert delete_response.status_code == 200
    deleted_data = delete_response.json()
    assert deleted_data["id"] == spot_check_id
    assert deleted_data["timing"] == "隨機抽查"
    
    # Verify the spot check was deleted
    response = client.get(f"/api/inspections/{spot_check_id}")
    assert response.status_code == 404
    
    # Verify the photos were also deleted (cascade delete)
    response = client.get(f"/api/photos/?inspection_id={spot_check_id}")
    assert response.status_code == 200
    assert len(response.json()) == 0

# Photo API tests
def test_read_photos(client, create_inspection_via_api):
    """Test reading all photos via API"""
    inspection_id = create_inspection_via_api
    
    # Get all photos
    response = client.get("/api/photos/")
    assert response.status_code == 200
    
    # Get photos filtered by inspection_id
    response = client.get(f"/api/photos/?inspection_id={inspection_id}")
    assert response.status_code == 200

def test_read_photo(client, create_photo_via_api, create_inspection_via_api):
    """Test reading a specific photo via API"""
    photo_id = create_photo_via_api
    inspection_id = create_inspection_via_api
    
    # Get the photo
    response = client.get(f"/api/photos/{photo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == photo_id
    assert data["inspection_id"] == inspection_id
    assert "photo_path" in data
    assert "caption" in data

def test_delete_photo(client, create_photo_via_api):
    """Test deleting a photo via API"""
    photo_id = create_photo_via_api
    
    # Delete the photo
    response = client.delete(f"/api/photos/{photo_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(f"/api/photos/{photo_id}")
    assert response.status_code == 404

def test_patch_photo_caption_and_date(client, create_photo_via_api, test_update_photo_data):
    """Test partial update (PATCH) of photo caption and date only"""
    photo_id = create_photo_via_api
    
    # PATCH 只更新日期和描述
    patch_resp = client.patch(f"/api/photos/{photo_id}", json=test_update_photo_data)
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    
    # 驗證只有指定欄位被更新
    assert patched["caption"] == test_update_photo_data["caption"]
    assert patched["capture_date"] == test_update_photo_data["capture_date"]

# Add tests for error handling
def test_get_nonexistent_project(client):
    """Test getting a non-existent project"""
    response = client.get("/api/projects/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"

def test_get_nonexistent_inspection(client):
    """Test getting a non-existent inspection"""
    response = client.get("/api/inspections/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Inspection not found"

def test_get_nonexistent_photo(client):
    """Test getting a non-existent photo"""
    response = client.get("/api/photos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Photo not found"

# Test validation errors
def test_create_project_validation_error(client):
    """Test creating a project with invalid data"""
    # Missing required fields
    project_data = {
        "name": "Test Project"
    }
    response = client.post("/api/projects/", json=project_data)
    assert response.status_code == 422

def test_create_inspection_validation_error(client, create_project_via_api):
    """Test creating an inspection with invalid data"""
    # Missing required fields
    inspection_data = {
        "project_id": create_project_via_api
    }
    response = client.post("/api/inspections/", json=inspection_data)
    assert response.status_code == 422

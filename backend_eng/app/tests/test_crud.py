import pytest
from fastapi import HTTPException
from datetime import date, timedelta
from app.services.crud import (
    get_projects, get_project, create_project, update_project, delete_project,
    get_inspections, get_inspection, create_inspection, update_inspection, delete_inspection,
    get_photos, get_photo, create_photo, update_photo, delete_photo,
    get_projects_by_owner
)
from app.schemas import schemas
from app.models.models import Project, ConstructionInspection, InspectionPhoto

# Project CRUD tests
def test_create_project(db, test_project_data):
    """Test creating a project"""
    project_data = schemas.ProjectCreate(**test_project_data)
    
    project = create_project(db, project_data)
    assert project.id is not None
    assert project.name == test_project_data["name"]
    assert project.location == test_project_data["location"]
    assert project.contractor == test_project_data["contractor"]
    assert project.start_date == date.fromisoformat(test_project_data["start_date"])
    assert project.end_date == date.fromisoformat(test_project_data["end_date"])
    assert project.owner == test_project_data["owner"]

def test_get_project(db, test_project):
    """Test getting a project by ID"""
    # Get the project
    project = get_project(db, test_project.id)
    assert project.id == test_project.id
    assert project.name == test_project.name

def test_get_project_not_found(db):
    """Test getting a non-existent project"""
    with pytest.raises(HTTPException) as excinfo:
        get_project(db, 999)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Project not found"

def test_get_projects(db, test_project_data):
    """Test getting all projects"""
    # Create some projects
    project_data1 = schemas.ProjectCreate(**test_project_data)
    project_data2 = schemas.ProjectCreate(
        name="Test Project 2",
        location="Test Location 2",
        contractor="Test Contractor 2",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=60),
        owner="test_owner_2"
    )
    
    create_project(db, project_data1)
    create_project(db, project_data2)
    
    # Get all projects
    projects = get_projects(db)
    assert len(projects) >= 2
    project_names = [p.name for p in projects]
    assert test_project_data["name"] in project_names
    assert "Test Project 2" in project_names

def test_get_projects_by_owner(db, test_project_data):
    """Test getting projects by owner"""
    # Create projects with different owners
    project_data1 = schemas.ProjectCreate(**test_project_data)  # Owner: test_owner
    
    project_data2 = schemas.ProjectCreate(
        name="Test Project 2",
        location="Test Location 2",
        contractor="Test Contractor 2",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=60),
        owner="different_owner"
    )
    
    create_project(db, project_data1)
    create_project(db, project_data2)
    
    # Get projects by owner
    projects = get_projects_by_owner(db, owner="test_owner")
    assert len(projects) >= 1
    assert all(p.owner == "test_owner" for p in projects)
    
    # Get projects by different owner
    projects = get_projects_by_owner(db, owner="different_owner")
    assert len(projects) >= 1
    assert all(p.owner == "different_owner" for p in projects)

def test_update_project(db, test_project):
    """Test updating a project"""
    # Update the project
    updated_data = schemas.ProjectCreate(
        name="Updated Project",
        location="Updated Location",
        contractor="Updated Contractor",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=45),
        owner="updated_owner"
    )
    
    updated_project = update_project(db, test_project.id, updated_data)
    assert updated_project.id == test_project.id
    assert updated_project.name == "Updated Project"
    assert updated_project.location == "Updated Location"
    assert updated_project.contractor == "Updated Contractor"
    assert updated_project.end_date == date.today() + timedelta(days=45)
    assert updated_project.owner == "updated_owner"

def test_delete_project(db, test_project):
    """Test deleting a project"""
    # Delete the project
    deleted_project = delete_project(db, test_project.id)
    assert deleted_project.id == test_project.id
    
    # Verify it's deleted
    with pytest.raises(HTTPException) as excinfo:
        get_project(db, test_project.id)
    assert excinfo.value.status_code == 404

# Inspection CRUD tests
def test_create_inspection(db, test_project_id, test_inspection_data):
    """Test creating an inspection"""
    # Create inspection
    inspection_data = schemas.InspectionCreate(**test_inspection_data)
    
    inspection = create_inspection(db, inspection_data)
    assert inspection.id is not None
    assert inspection.project_id == test_project_id
    assert inspection.subproject_name == test_inspection_data["subproject_name"]
    assert inspection.timing == test_inspection_data["timing"]
    assert inspection.result == test_inspection_data["result"]

def test_get_inspection(db, test_inspection):
    """Test getting an inspection by ID"""
    # Get the inspection
    inspection = get_inspection(db, test_inspection.id)
    assert inspection.id == test_inspection.id
    assert inspection.subproject_name == test_inspection.subproject_name

def test_update_inspection(db, test_inspection, test_update_inspection_data):
    """Test updating an inspection"""
    # Update the inspection
    updated_data = schemas.InspectionUpdate(**test_update_inspection_data)
    
    updated_inspection = update_inspection(db, test_inspection.id, updated_data)
    assert updated_inspection.id == test_inspection.id
    assert updated_inspection.result == test_update_inspection_data["result"]
    assert updated_inspection.remark == test_update_inspection_data["remark"]

def test_delete_inspection(db, test_inspection):
    """Test deleting an inspection"""
    # Delete the inspection
    deleted_inspection = delete_inspection(db, test_inspection.id)
    assert deleted_inspection.id == test_inspection.id
    
    # Verify it's deleted
    with pytest.raises(HTTPException) as excinfo:
        get_inspection(db, test_inspection.id)
    assert excinfo.value.status_code == 404

# Photo CRUD tests
def test_create_photo(db, test_inspection_id):
    """Test creating a photo"""
    # Create photo
    photo_data = schemas.PhotoCreate(
        inspection_id=test_inspection_id,
        photo_path="/path/to/photo.jpg",
        capture_date=date.today(),
        caption="Test Caption"
    )
    
    photo = create_photo(db, photo_data)
    assert photo.id is not None
    assert photo.inspection_id == test_inspection_id
    assert photo.photo_path == "/path/to/photo.jpg"
    assert photo.caption == "Test Caption"

def test_get_photos_by_inspection(db, test_inspection_id):
    """Test getting photos by inspection ID"""
    # Create some photos
    photo_data1 = schemas.PhotoCreate(
        inspection_id=test_inspection_id,
        photo_path="/path/to/photo1.jpg",
        capture_date=date.today(),
        caption="Test Caption 1"
    )
    photo_data2 = schemas.PhotoCreate(
        inspection_id=test_inspection_id,
        photo_path="/path/to/photo2.jpg",
        capture_date=date.today(),
        caption="Test Caption 2"
    )
    
    create_photo(db, photo_data1)
    create_photo(db, photo_data2)
    
    # Get photos by inspection ID
    photos = get_photos(db, inspection_id=test_inspection_id)
    assert len(photos) >= 2
    photo_captions = [p.caption for p in photos]
    assert "Test Caption 1" in photo_captions
    assert "Test Caption 2" in photo_captions

def test_get_photo(db, test_photo):
    """Test getting a photo by ID"""
    # Get the photo
    photo = get_photo(db, test_photo.id)
    assert photo.id == test_photo.id
    assert photo.caption == test_photo.caption

def test_update_photo(db, test_photo, test_update_photo_data):
    """Test updating a photo"""
    # Update the photo
    updated_data = schemas.PhotoUpdate(**test_update_photo_data)
    
    updated_photo = update_photo(db, test_photo.id, updated_data)
    assert updated_photo.id == test_photo.id
    assert updated_photo.caption == test_update_photo_data["caption"]
    assert updated_photo.capture_date == date.fromisoformat(test_update_photo_data["capture_date"])

def test_delete_photo(db, test_photo):
    """Test deleting a photo"""
    # Delete the photo
    deleted_photo = delete_photo(db, test_photo.id)
    assert deleted_photo.id == test_photo.id
    
    # Verify it's deleted
    with pytest.raises(HTTPException) as excinfo:
        get_photo(db, test_photo.id)
    assert excinfo.value.status_code == 404

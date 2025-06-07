import pytest
from datetime import date, datetime, timedelta
from app.models.models import Project, ConstructionInspection, InspectionPhoto

def test_project_model(db):
    """Test creating a Project model instance"""
    # Create test data
    project = Project(
        name="Test Project",
        location="Test Location",
        contractor="Test Contractor",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        owner="test_owner"
    )
    
    # Add to database
    db.add(project)
    db.commit()
    
    # Query and verify
    db_project = db.query(Project).filter(Project.name == "Test Project").first()
    assert db_project is not None
    assert db_project.name == "Test Project"
    assert db_project.location == "Test Location"
    assert db_project.contractor == "Test Contractor"
    assert db_project.start_date == date.today()
    assert db_project.end_date == date.today() + timedelta(days=30)
    assert db_project.owner == "test_owner"

def test_construction_inspection_model(db):
    """Test creating a ConstructionInspection model instance"""
    # Create a project first
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
    
    # Create inspection
    inspection = ConstructionInspection(
        project_id=project.id,
        subproject_name="Test Subproject",
        inspection_form_name="Test Form",
        inspection_date=date.today(),
        location="Test Inspection Location",
        timing="檢驗停留點",
        result="合格",
        remark="Test remark",
        pdf_path="/path/to/pdf"
    )
    
    # Add to database
    db.add(inspection)
    db.commit()
    
    # Query and verify
    db_inspection = db.query(ConstructionInspection).filter(
        ConstructionInspection.subproject_name == "Test Subproject"
    ).first()
    
    assert db_inspection is not None
    assert db_inspection.project_id == project.id
    assert db_inspection.subproject_name == "Test Subproject"
    assert db_inspection.inspection_form_name == "Test Form"
    assert db_inspection.inspection_date == date.today()
    assert db_inspection.location == "Test Inspection Location"
    assert db_inspection.timing == "檢驗停留點"
    assert db_inspection.result == "合格"
    assert db_inspection.remark == "Test remark"
    assert db_inspection.pdf_path == "/path/to/pdf"
    assert db_inspection.created_at is not None
    assert db_inspection.updated_at is not None

def test_inspection_photo_model(db):
    """Test creating an InspectionPhoto model instance"""
    # Create a project first
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
    
    # Create inspection
    inspection = ConstructionInspection(
        project_id=project.id,
        subproject_name="Test Subproject",
        inspection_form_name="Test Form",
        inspection_date=date.today(),
        location="Test Inspection Location",
        timing="檢驗停留點",
        result="合格",
        remark="Test remark"
    )
    db.add(inspection)
    db.commit()
    
    # Create photo
    photo = InspectionPhoto(
        inspection_id=inspection.id,
        photo_path="/path/to/photo.jpg",
        capture_date=date.today(),
        caption="Test Caption"
    )
    
    # Add to database
    db.add(photo)
    db.commit()
    
    # Query and verify
    db_photo = db.query(InspectionPhoto).filter(
        InspectionPhoto.inspection_id == inspection.id
    ).first()
    
    assert db_photo is not None
    assert db_photo.inspection_id == inspection.id
    assert db_photo.photo_path == "/path/to/photo.jpg"
    assert db_photo.capture_date == date.today()
    assert db_photo.caption == "Test Caption"

def test_relationships(db):
    """Test the relationships between models"""
    # Create a project
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
    
    # Create inspection
    inspection = ConstructionInspection(
        project_id=project.id,
        subproject_name="Test Subproject",
        inspection_form_name="Test Form",
        inspection_date=date.today(),
        location="Test Inspection Location",
        timing="檢驗停留點",
        result="合格",
        remark="Test remark"
    )
    db.add(inspection)
    db.commit()
    
    # Create photos
    photo1 = InspectionPhoto(
        inspection_id=inspection.id,
        photo_path="/path/to/photo1.jpg",
        capture_date=date.today(),
        caption="Test Caption 1"
    )
    
    photo2 = InspectionPhoto(
        inspection_id=inspection.id,
        photo_path="/path/to/photo2.jpg",
        capture_date=date.today(),
        caption="Test Caption 2"
    )
    
    db.add(photo1)
    db.add(photo2)
    db.commit()
    
    # Test project -> inspections relationship
    db_project = db.query(Project).filter(Project.id == project.id).first()
    assert len(db_project.inspections) == 1
    assert db_project.inspections[0].id == inspection.id
    
    # Test inspection -> project relationship
    db_inspection = db.query(ConstructionInspection).filter(
        ConstructionInspection.id == inspection.id
    ).first()
    assert db_inspection.project.id == project.id
    
    # Test inspection -> photos relationship
    assert len(db_inspection.photos) == 2
    photo_paths = [p.photo_path for p in db_inspection.photos]
    assert "/path/to/photo1.jpg" in photo_paths
    assert "/path/to/photo2.jpg" in photo_paths
    
    # Test photo -> inspection relationship
    db_photo = db.query(InspectionPhoto).filter(
        InspectionPhoto.id == photo1.id
    ).first()
    assert db_photo.inspection.id == inspection.id

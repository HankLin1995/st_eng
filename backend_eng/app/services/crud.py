from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.models import Project, ConstructionInspection, InspectionPhoto
from app.schemas import schemas
from datetime import date
import os

# Project CRUD operations
def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Project).offset(skip).limit(limit).all()

def get_projects_by_owner(db: Session, owner: str, skip: int = 0, limit: int = 100):
    """Get projects filtered by owner"""
    return db.query(Project).filter(Project.owner == owner).offset(skip).limit(limit).all()

def get_project(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: int, project: schemas.ProjectCreate):
    db_project = get_project(db, project_id)
    for key, value in project.model_dump().items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int):
    db_project = get_project(db, project_id)
    
    # Get all inspections for this project to delete their files
    inspections = db.query(ConstructionInspection).filter(ConstructionInspection.project_id == project_id).all()
    for inspection in inspections:
        # Delete inspection files (including associated photos)
        delete_inspection(db, inspection.id)
    
    db.delete(db_project)
    db.commit()
    return db_project

# Inspection CRUD operations
def get_inspections(db: Session, skip: int = 0, limit: int = 100, project_id: Optional[int] = None):
    query = db.query(ConstructionInspection)
    if project_id:
        query = query.filter(ConstructionInspection.project_id == project_id)
    return query.offset(skip).limit(limit).all()

def get_inspection(db: Session, inspection_id: int):
    inspection = db.query(ConstructionInspection).filter(ConstructionInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return inspection

def create_inspection(db: Session, inspection: schemas.InspectionCreate):
    db_inspection = ConstructionInspection(**inspection.model_dump())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def update_inspection(db: Session, inspection_id: int, inspection_update: schemas.InspectionUpdate):
    db_inspection = get_inspection(db, inspection_id)
    
    # If updating the PDF path and there's an existing PDF, delete the old one
    update_data = inspection_update.model_dump(exclude_unset=True)
    if 'pdf_path' in update_data and update_data['pdf_path'] is not None and db_inspection.pdf_path:
        if os.path.exists(db_inspection.pdf_path):
            try:
                os.remove(db_inspection.pdf_path)
            except (OSError, PermissionError) as e:
                # Log the error but continue with the update
                print(f"Error deleting PDF file {db_inspection.pdf_path}: {e}")
    
    for key, value in update_data.items():
        setattr(db_inspection, key, value)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def delete_inspection(db: Session, inspection_id: int):
    db_inspection = get_inspection(db, inspection_id)
    
    # Delete the PDF file if it exists
    if db_inspection.pdf_path and os.path.exists(db_inspection.pdf_path):
        try:
            os.remove(db_inspection.pdf_path)
        except (OSError, PermissionError) as e:
            # Log the error but continue with the deletion
            print(f"Error deleting PDF file {db_inspection.pdf_path}: {e}")
    
    # Get all photos for this inspection to delete their files
    photos = db.query(InspectionPhoto).filter(InspectionPhoto.inspection_id == inspection_id).all()
    for photo in photos:
        # Delete photo files
        if photo.photo_path and os.path.exists(photo.photo_path):
            try:
                os.remove(photo.photo_path)
            except (OSError, PermissionError) as e:
                # Log the error but continue with the deletion
                print(f"Error deleting photo file {photo.photo_path}: {e}")
    
    db.delete(db_inspection)
    db.commit()
    return db_inspection

# Photo CRUD operations
def get_photos(db: Session, skip: int = 0, limit: int = 100, inspection_id: Optional[int] = None):
    query = db.query(InspectionPhoto)
    if inspection_id:
        query = query.filter(InspectionPhoto.inspection_id == inspection_id)
    return query.offset(skip).limit(limit).all()

def get_photo(db: Session, photo_id: int):
    photo = db.query(InspectionPhoto).filter(InspectionPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo

def create_photo(db: Session, photo: schemas.PhotoCreate):
    db_photo = InspectionPhoto(**photo.model_dump())
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo

def update_photo(db: Session, photo_id: int, photo_update: schemas.PhotoUpdate):
    db_photo = get_photo(db, photo_id)
    
    # If updating the photo path and there's an existing photo, delete the old one
    update_data = photo_update.model_dump(exclude_unset=True)
    if 'photo_path' in update_data and update_data['photo_path'] is not None and db_photo.photo_path:
        if os.path.exists(db_photo.photo_path):
            try:
                os.remove(db_photo.photo_path)
            except (OSError, PermissionError) as e:
                # Log the error but continue with the update
                print(f"Error deleting photo file {db_photo.photo_path}: {e}")
    
    for key, value in update_data.items():
        setattr(db_photo, key, value)
    db.commit()
    db.refresh(db_photo)
    return db_photo

def delete_photo(db: Session, photo_id: int):
    db_photo = get_photo(db, photo_id)
    
    # Delete the photo file if it exists
    if db_photo.photo_path and os.path.exists(db_photo.photo_path):
        try:
            os.remove(db_photo.photo_path)
        except (OSError, PermissionError) as e:
            # Log the error but continue with the deletion
            print(f"Error deleting photo file {db_photo.photo_path}: {e}")
    
    db.delete(db_photo)
    db.commit()
    return db_photo

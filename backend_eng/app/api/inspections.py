from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.database import get_db
from app.services import crud
from app.schemas import schemas
from app.utils.file_utils import save_pdf_file, generate_inspection_pdf

router = APIRouter()

@router.post("/inspections/", response_model=schemas.Inspection, status_code=status.HTTP_201_CREATED)
async def create_inspection(inspection: schemas.InspectionCreate, db: Session = Depends(get_db)):
    """Create a new inspection"""
    return crud.create_inspection(db=db, inspection=inspection)

@router.get("/inspections/", response_model=List[schemas.Inspection])
def read_inspections(
    skip: int = 0, 
    limit: int = 100, 
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all inspections, optionally filtered by project_id"""
    inspections = crud.get_inspections(db, skip=skip, limit=limit, project_id=project_id)
    return inspections

@router.get("/inspections/{inspection_id}", response_model=schemas.InspectionWithPhotos)
def read_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """Get a specific inspection by ID with its photos"""
    inspection = crud.get_inspection(db, inspection_id=inspection_id)
    return inspection

@router.put("/inspections/{inspection_id}", response_model=schemas.Inspection)
def update_inspection(
    inspection_id: int, 
    inspection_update: schemas.InspectionUpdate, 
    db: Session = Depends(get_db)
):
    """Update an inspection result and remarks"""
    return crud.update_inspection(db=db, inspection_id=inspection_id, inspection_update=inspection_update)

@router.delete("/inspections/{inspection_id}", response_model=schemas.Inspection)
def delete_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """Delete an inspection"""
    return crud.delete_inspection(db=db, inspection_id=inspection_id)

@router.post("/inspections/{inspection_id}/upload-pdf", response_model=schemas.Inspection)
async def upload_inspection_pdf(
    inspection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF for an inspection"""
    inspection = crud.get_inspection(db, inspection_id=inspection_id)
    
    # Save the PDF file
    pdf_path = await save_pdf_file(file)
    
    # Update the inspection with the PDF path
    inspection_update = schemas.InspectionUpdate(
        result=inspection.result,
        remark=inspection.remark,
        pdf_path=pdf_path
    )
    
    updated_inspection = crud.update_inspection(db, inspection_id, inspection_update)
    return updated_inspection

@router.post("/inspections/{inspection_id}/generate-pdf", response_model=schemas.Inspection)
async def generate_inspection_report(
    inspection_id: int,
    db: Session = Depends(get_db)
):
    """Generate a PDF report with inspection data and photos"""
    # Get the inspection and its photos
    inspection = crud.get_inspection(db, inspection_id=inspection_id)
    photos = crud.get_photos(db, inspection_id=inspection_id)
    
    # Generate the PDF
    pdf_path = generate_inspection_pdf(inspection, photos)
    
    # Update the inspection with the PDF path
    inspection_update = schemas.InspectionUpdate(
        result=inspection.result,
        remark=inspection.remark,
        pdf_path=pdf_path
    )
    
    updated_inspection = crud.update_inspection(db, inspection_id, inspection_update)
    return updated_inspection

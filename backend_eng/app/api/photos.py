from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.database import get_db
from app.services import crud
from app.schemas import schemas
from app.utils.file_utils import save_photo_file

router = APIRouter()

@router.post("/photos/", response_model=schemas.Photo, status_code=status.HTTP_201_CREATED)
async def create_photo(
    inspection_id: int = Form(...),
    capture_date: date = Form(...),
    caption: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new photo for an inspection"""
    # Verify the inspection exists
    inspection = crud.get_inspection(db, inspection_id=inspection_id)
    
    # Save the photo file
    photo_path = await save_photo_file(file)
    
    # Create the photo record
    photo_data = schemas.PhotoCreate(
        inspection_id=inspection_id,
        photo_path=photo_path,
        capture_date=capture_date,
        caption=caption
    )
    
    return crud.create_photo(db=db, photo=photo_data)

@router.get("/photos/", response_model=List[schemas.Photo])
def read_photos(
    skip: int = 0, 
    limit: int = 100, 
    inspection_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all photos, optionally filtered by inspection_id"""
    photos = crud.get_photos(db, skip=skip, limit=limit, inspection_id=inspection_id)
    return photos

@router.get("/photos/{photo_id}", response_model=schemas.Photo)
def read_photo(photo_id: int, db: Session = Depends(get_db)):
    """Get a specific photo by ID"""
    photo = crud.get_photo(db, photo_id=photo_id)
    return photo

@router.put("/photos/{photo_id}", response_model=schemas.Photo)
def update_photo(
    photo_id: int, 
    photo_update: schemas.PhotoUpdate, 
    db: Session = Depends(get_db)
):
    """Update a photo's metadata"""
    return crud.update_photo(db=db, photo_id=photo_id, photo_update=photo_update)

@router.patch("/photos/{photo_id}", response_model=schemas.Photo)
def partial_update_photo(
    photo_id: int,
    photo_update: schemas.PhotoUpdate,
    db: Session = Depends(get_db)
):
    """Partially update a photo's metadata (date, caption, etc.)"""
    return crud.update_photo(db=db, photo_id=photo_id, photo_update=photo_update)

@router.delete("/photos/{photo_id}", response_model=schemas.Photo)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo"""
    return crud.delete_photo(db=db, photo_id=photo_id)

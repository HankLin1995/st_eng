from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# Project schemas
class ProjectBase(BaseModel):
    name: str
    location: str
    contractor: str
    start_date: date
    end_date: date
    owner: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Inspection schemas
class InspectionBase(BaseModel):
    project_id: int
    subproject_name: str
    inspection_form_name: str
    inspection_date: date
    location: str
    timing: str
    result: Optional[str] = None
    remark: Optional[str] = None

class InspectionCreate(InspectionBase):
    pass

class InspectionUpdate(BaseModel):
    result: str
    remark: Optional[str] = None
    pdf_path: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class Inspection(InspectionBase):
    id: int
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Photo schemas
class PhotoBase(BaseModel):
    inspection_id: int
    photo_path: str
    capture_date: date
    caption: Optional[str] = None

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(BaseModel):
    photo_path: Optional[str] = None
    capture_date: Optional[date] = None
    caption: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class Photo(PhotoBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Response schemas
class InspectionWithPhotos(Inspection):
    photos: List[Photo] = []
    
    model_config = ConfigDict(from_attributes=True)

class ProjectWithInspections(Project):
    inspections: List[Inspection] = []
    
    model_config = ConfigDict(from_attributes=True)

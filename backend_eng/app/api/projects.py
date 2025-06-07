from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.services import crud
from app.schemas import schemas
from app.utils.file_utils import calculate_project_files_size

router = APIRouter()

@router.post("/projects/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    return crud.create_project(db=db, project=project)

@router.get("/projects/", response_model=List[schemas.Project])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    owner: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get all projects, optionally filtered by owner"""
    if owner:
        projects = crud.get_projects_by_owner(db, owner=owner, skip=skip, limit=limit)
    else:
        projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/projects/{project_id}", response_model=schemas.ProjectWithInspections)
def read_project(
    project_id: int, 
    owner: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get a specific project by ID with its inspections"""
    project = crud.get_project(db, project_id=project_id)
    
    # If owner is provided, verify it matches the project owner
    if owner and project.owner != owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not the owner of this project"
        )
    
    return project

@router.get("/projects/{project_id}/storage")
def get_project_storage_info(
    project_id: int, 
    owner: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    獲取特定專案的靜態檔案大小資訊
    
    Args:
        project_id: 專案ID
        owner: 專案擁有者 (可選)
        db: 資料庫會話
        
    Returns:
        包含專案靜態檔案大小資訊的字典
    """
    # 檢查專案是否存在
    project = crud.get_project(db, project_id=project_id)
    
    # If owner is provided, verify it matches the project owner
    if owner and project.owner != owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not the owner of this project"
        )
    
    # 計算專案相關的靜態檔案大小
    storage_info = calculate_project_files_size(db, project_id)
    return storage_info

@router.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int, 
    project: schemas.ProjectCreate, 
    owner: str = Header(...),
    db: Session = Depends(get_db)
):
    """Update a project"""
    # Get the existing project
    existing_project = crud.get_project(db, project_id=project_id)
    
    # Verify owner matches
    if existing_project.owner != owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not the owner of this project"
        )
    
    return crud.update_project(db=db, project_id=project_id, project=project)

@router.delete("/projects/{project_id}", response_model=schemas.Project)
def delete_project(
    project_id: int, 
    owner: str = Header(...),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    # Get the existing project
    existing_project = crud.get_project(db, project_id=project_id)
    
    # Verify owner matches
    if existing_project.owner != owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not the owner of this project"
        )
    
    return crud.delete_project(db=db, project_id=project_id)

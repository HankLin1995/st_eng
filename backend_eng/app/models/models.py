from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class TimingEnum(enum.Enum):
    INSPECTION_POINT = "檢驗停留點"
    RANDOM_CHECK = "隨機抽查"

class ResultEnum(enum.Enum):
    PASS = "合格"
    FAIL = "不合格"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    contractor = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    owner = Column(String(100), nullable=False)
    
    inspections = relationship("ConstructionInspection", back_populates="project")

class ConstructionInspection(Base):
    __tablename__ = "construction_inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    subproject_name = Column(String(200), nullable=False)
    inspection_form_name = Column(String(200), nullable=False)
    inspection_date = Column(Date, nullable=False)
    location = Column(String(200), nullable=False)
    timing = Column(String(20), nullable=False)
    result = Column(String(20), nullable=False)
    remark = Column(Text, nullable=True)
    pdf_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="inspections")
    photos = relationship("InspectionPhoto", back_populates="inspection", cascade="all, delete-orphan")

class InspectionPhoto(Base):
    __tablename__ = "inspection_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("construction_inspections.id"), nullable=False)
    photo_path = Column(String(255), nullable=False)
    capture_date = Column(Date, nullable=False)
    caption = Column(String(255), nullable=True)
    
    inspection = relationship("ConstructionInspection", back_populates="photos")

import os
import uuid
from fastapi import UploadFile
from typing import List
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session

# Base directories for uploads
PDF_UPLOAD_DIR = "app/static/uploads/pdfs"
PHOTO_UPLOAD_DIR = "app/static/uploads/photos"

def ensure_upload_dirs():
    """Ensure upload directories exist"""
    os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)
    os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)

async def save_upload_file(upload_file: UploadFile, directory: str) -> str:
    """Save an uploaded file to the specified directory and return the file path"""
    ensure_upload_dirs()
    
    # Generate a unique filename
    filename = f"{uuid.uuid4()}_{upload_file.filename}"
    file_path = os.path.join(directory, filename)
    
    # Write the file
    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    return file_path

async def save_pdf_file(upload_file: UploadFile) -> str:
    """Save an uploaded PDF file and return the file path"""
    return await save_upload_file(upload_file, PDF_UPLOAD_DIR)

async def save_photo_file(upload_file: UploadFile) -> str:
    """Save an uploaded photo file and return the file path"""
    return await save_upload_file(upload_file, PHOTO_UPLOAD_DIR)

def calculate_project_files_size(db: Session, project_id: int) -> dict:
    """
    Calculate the total size of static files related to a specific project.
    
    Args:
        db: Database session
        project_id: ID of the project
        
    Returns:
        Dictionary with storage information for the project
    """
    from app.models.models import Project, ConstructionInspection, InspectionPhoto
    
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {
            "error": "Project not found",
            "project_id": project_id,
            "total_size_bytes": 0,
            "total_size_formatted": "0 B",
            "file_count": 0,
            "exists": False
        }
    
    # Initialize counters
    total_size = 0
    file_count = 0
    pdf_files = []
    photo_files = []
    
    # Get all inspections for the project
    inspections = db.query(ConstructionInspection).filter(ConstructionInspection.project_id == project_id).all()
    
    # Collect PDF paths
    for inspection in inspections:
        if inspection.pdf_path and os.path.exists(inspection.pdf_path):
            pdf_files.append(inspection.pdf_path)
            file_size = os.path.getsize(inspection.pdf_path)
            total_size += file_size
            file_count += 1
    
    # Get all photos for the inspections
    for inspection in inspections:
        photos = db.query(InspectionPhoto).filter(InspectionPhoto.inspection_id == inspection.id).all()
        for photo in photos:
            if photo.photo_path and os.path.exists(photo.photo_path):
                photo_files.append(photo.photo_path)
                file_size = os.path.getsize(photo.photo_path)
                total_size += file_size
                file_count += 1
    
    # Format the size for human readability
    size_formatted = format_file_size(total_size)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_size_bytes": total_size,
        "total_size_formatted": size_formatted,
        "file_count": file_count,
        "pdf_count": len(pdf_files),
        "photo_count": len(photo_files),
        "exists": True,
        "details": {
            "pdf_files": pdf_files,
            "photo_files": photo_files
        }
    }

def format_file_size(size_in_bytes: int) -> str:
    """
    Format file size from bytes to human-readable format
    
    Args:
        size_in_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0 or unit == 'TB':
            if unit == 'B':
                return f"{size_in_bytes} {unit}"
            else:
                return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0

def generate_inspection_pdf(inspection_data, photos_data):
    """Generate a PDF with inspection data and photos"""
    # Create a unique filename for the PDF
    filename = f"inspection_{uuid.uuid4()}.pdf"
    file_path = os.path.join(PDF_UPLOAD_DIR, filename)
    
    # Ensure directory exists
    ensure_upload_dirs()
    
    # Create the PDF document
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add inspection details
    elements.append(Paragraph(f"工程抽查表", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"分項工程名稱: {inspection_data.subproject_name}", styles['Normal']))
    elements.append(Paragraph(f"抽查表名稱: {inspection_data.inspection_form_name}", styles['Normal']))
    elements.append(Paragraph(f"檢查日期: {inspection_data.inspection_date}", styles['Normal']))
    elements.append(Paragraph(f"檢查位置: {inspection_data.location}", styles['Normal']))
    elements.append(Paragraph(f"抽查時機: {inspection_data.timing}", styles['Normal']))
    elements.append(Paragraph(f"抽查結果: {inspection_data.result}", styles['Normal']))
    
    if inspection_data.remark:
        elements.append(Paragraph(f"備註: {inspection_data.remark}", styles['Normal']))
    
    elements.append(Spacer(1, 24))
    
    # Add photos if available
    if photos_data:
        elements.append(Paragraph("現場照片", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        for photo in photos_data:
            if os.path.exists(photo.photo_path):
                img = RLImage(photo.photo_path, width=400, height=300)
                elements.append(img)
                elements.append(Paragraph(f"說明: {photo.caption if photo.caption else '無'}", styles['Normal']))
                elements.append(Paragraph(f"拍攝日期: {photo.capture_date}", styles['Normal']))
                elements.append(Spacer(1, 12))
    
    # Build the PDF
    doc.build(elements)
    
    return file_path

def merge_inspection_pdf_with_photos(inspection_pdf_path: str, photos: List[dict]) -> str:
    """
    合併抽查表單 PDF 與照片，生成一個新的 PDF 文件
    
    第一頁：原始的抽查表單 PDF
    第二頁：照片排版，每排最多 3 張照片，帶框框 + 日期 + 說明
    
    Args:
        inspection_pdf_path: 抽查表單 PDF 的路徑
        photos: 照片列表，每個照片包含 photo_path, capture_date, caption
        
    Returns:
        生成的 PDF 文件路徑
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle, Paragraph, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from PyPDF2 import PdfReader, PdfWriter
    import io
    import os
    import uuid
    
    # 確保上傳目錄存在
    ensure_upload_dirs()
    
    # 生成臨時文件名
    temp_photos_pdf = os.path.join(PDF_UPLOAD_DIR, f"temp_photos_{uuid.uuid4()}.pdf")
    output_pdf_path = os.path.join(PDF_UPLOAD_DIR, f"merged_{uuid.uuid4()}.pdf")
    
    # 創建照片頁面的 PDF
    doc = SimpleDocTemplate(temp_photos_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # 添加標題
    elements.append(Paragraph("抽查照片", styles['Heading1']))
    
    # 將照片分組，每行最多 3 張
    photo_rows = []
    current_row = []
    
    for photo in photos:
        if len(current_row) == 3:
            photo_rows.append(current_row)
            current_row = []
        
        # 添加照片及其說明
        img = Image(photo['photo_path'], width=150, height=150)
        caption = f"{photo['caption']} ({photo['capture_date']})"
        current_row.append([img, Paragraph(caption, styles['Normal'])])
    
    # 添加最後一行（如果有）
    if current_row:
        # 如果最後一行不足 3 張，添加空單元格
        while len(current_row) < 3:
            current_row.append(['', ''])
        photo_rows.append(current_row)
    
    # 創建照片表格
    for row in photo_rows:
        # 創建一個 3 列的表格，每列包含照片和說明
        photo_table_data = []
        photo_cells = []
        caption_cells = []
        
        for cell in row:
            if isinstance(cell[0], Image):
                photo_cells.append(cell[0])
                caption_cells.append(cell[1])
            else:
                photo_cells.append('')
                caption_cells.append('')
        
        photo_table_data.append(photo_cells)
        photo_table_data.append(caption_cells)
        
        table = Table(photo_table_data, colWidths=[180, 180, 180])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        elements.append(table)
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # 生成照片頁面 PDF
    doc.build(elements)
    
    # 合併原始 PDF 和照片頁面 PDF
    pdf_writer = PdfWriter()
    
    # 添加原始 PDF 的所有頁面
    with open(inspection_pdf_path, 'rb') as f:
        pdf_reader = PdfReader(f)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_writer.add_page(page)
    
    # 添加照片頁面 PDF 的所有頁面
    with open(temp_photos_pdf, 'rb') as f:
        pdf_reader = PdfReader(f)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            pdf_writer.add_page(page)
    
    # 寫入合併後的 PDF
    with open(output_pdf_path, 'wb') as f:
        pdf_writer.write(f)
    
    # 刪除臨時文件
    if os.path.exists(temp_photos_pdf):
        os.remove(temp_photos_pdf)
    
    return output_pdf_path

def generate_inspection_pdf(inspection, photos_data=None) -> str:
    """Generate a PDF with inspection data and photos"""
    # Create a unique filename for the PDF
    filename = f"inspection_{uuid.uuid4()}.pdf"
    file_path = os.path.join(PDF_UPLOAD_DIR, filename)
    
    # Ensure directory exists
    ensure_upload_dirs()
    
    # Create the PDF document
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add inspection details
    elements.append(Paragraph(f"工程抽查表", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"分項工程名稱: {inspection.subproject_name}", styles['Normal']))
    elements.append(Paragraph(f"抽查表名稱: {inspection.inspection_form_name}", styles['Normal']))
    elements.append(Paragraph(f"檢查日期: {inspection.inspection_date}", styles['Normal']))
    elements.append(Paragraph(f"檢查位置: {inspection.location}", styles['Normal']))
    elements.append(Paragraph(f"抽查時機: {inspection.timing}", styles['Normal']))
    elements.append(Paragraph(f"抽查結果: {inspection.result}", styles['Normal']))
    
    if inspection.remark:
        elements.append(Paragraph(f"備註: {inspection.remark}", styles['Normal']))
    
    elements.append(Spacer(1, 24))
    
    # Add photos if available
    if photos_data:
        elements.append(Paragraph("現場照片", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        for photo in photos_data:
            if os.path.exists(photo.photo_path):
                img = RLImage(photo.photo_path, width=400, height=300)
                elements.append(img)
                elements.append(Paragraph(f"說明: {photo.caption if photo.caption else '無'}", styles['Normal']))
                elements.append(Paragraph(f"拍攝日期: {photo.capture_date}", styles['Normal']))
                elements.append(Spacer(1, 12))
    
    # Build the PDF
    doc.build(elements)
    
    return file_path
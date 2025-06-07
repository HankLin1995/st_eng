from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from datetime import datetime

from api import API_BASE_URL

# with open("data.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

def generate_pdf(data):
    """生成 PDF 報表，返回 PDF 的 bytes 以便用於 Streamlit 的 download_button"""
    # 註冊中文字型
    import io
    
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansTC-Regular.ttf")
    pdfmetrics.registerFont(TTFont('NotoSansTC', font_path))
    chinese_font = 'NotoSansTC'

    # 使用 BytesIO 而不是實體文件
    buffer = io.BytesIO()

    # 創建 PDF 文件
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)

    # 獲取樣式並創建中文樣式
    styles = getSampleStyleSheet()

    # 如果找到中文字型，則創建中文樣式
    if chinese_font:
        # 標題樣式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName=chinese_font,
            fontSize=20,
            alignment=1,  # 置中
            spaceAfter=12
        ))

        # 副標題樣式
        styles.add(ParagraphStyle(
            name='ChineseSubTitle',
            parent=styles['Title'],
            fontName=chinese_font,
            fontSize=14,
            alignment=2,  # 置中
            spaceAfter=12
        ))

        # 一般文字樣式
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName=chinese_font,
            fontSize=12,
            leading=14,
            spaceAfter=6
        ))

    # 使用中文樣式或備用樣式
    title_style = styles['ChineseTitle'] if chinese_font else styles['Title']
    sub_title_style = styles['ChineseSubTitle'] if chinese_font else styles['Normal']
    normal_style = styles['ChineseNormal'] if chinese_font else styles['Normal']

    # 創建內容元素列表
    elements = []

    # 標題與基本資料
    elements.append(Paragraph(f"<b>抽查紀錄表照片</b>", title_style))
    #放在最右邊
    elements.append(Paragraph(f"抽查表名稱: {data.get('inspection_form_name', '')}", sub_title_style))

    # 定義表格的資料（合併所有照片內容）
    table_data = []
    for idx, photo in enumerate(data["photos"], 1):
        # 設定每行的高度
        row_heights = [1* cm, 1 * cm, 8* cm]  # 不同的行高
        
        # 表格資料放 metadata + 圖片
        table_data.append([Paragraph("拍攝日期", normal_style), Paragraph(photo["capture_date"], normal_style)])
        table_data.append([Paragraph("說明", normal_style), Paragraph(photo["caption"], normal_style)])
        table_data.append([Paragraph("圖片", normal_style), Image(f"{API_BASE_URL}/{photo['photo_path']}", width=8 * cm, height=8 * cm, kind='proportional')])

    # 創建單一表格並設定樣式
    table = Table(table_data, colWidths=[3 * cm, 12 * cm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),  # 設定邊框
        ("VALIGN", (0, 0), (-1, -1), "TOP"),  # 垂直對齊
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),  # 設定背景顏色
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),  # 水平對齊
    ]))

    elements.append(table)

    # 建立 PDF
    try:
        doc.build(elements)
        # 獲取 PDF 的 bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        print(f"生成 PDF 時發生錯誤: {e}")
        return None

def merge_multiple_pdfs(pdf_files_list):
    """
    合併多個 PDF 檔案
    
    Args:
        pdf_files_list: 一個列表，每個元素是一個元組 (pdf_bytes, is_from_url)
                      - pdf_bytes: 如果 is_from_url 為 True，則是 URL 字串；否則是 PDF 的 bytes
                      - is_from_url: 布林值，表示 pdf_bytes 是 URL 還是 bytes
    
    Returns:
        bytes: 合併後的 PDF 檔案的 bytes
    """
    import io
    import requests
    from PyPDF2 import PdfReader, PdfWriter
    
    # 創建一個 PDF writer 對象
    merger = PdfWriter()
    
    # 遍歷所有 PDF 檔案
    for pdf_content, is_from_url in pdf_files_list:
        try:
            # 根據內容類型處理 PDF
            if is_from_url:
                # 如果是 URL，下載 PDF 檔案
                if pdf_content.startswith('http'):
                    response = requests.get(pdf_content)
                    if response.status_code == 200:
                        pdf = PdfReader(io.BytesIO(response.content))
                    else:
                        print(f"下載 PDF 失敗，跳過此檔案。狀態碼: {response.status_code}")
                        continue
                else:
                    # 本地檔案路徑
                    try:
                        pdf = PdfReader(pdf_content)
                    except:
                        print(f"讀取本地 PDF 失敗，跳過此檔案: {pdf_content}")
                        continue
            else:
                # 如果是 bytes 內容
                pdf = PdfReader(io.BytesIO(pdf_content))
            
            # 添加所有頁面
            for page in pdf.pages:
                merger.add_page(page)
                
        except Exception as e:
            print(f"處理 PDF 時發生錯誤: {e}")
            continue
    
    # 如果沒有成功添加任何頁面
    if len(merger.pages) == 0:
        return None
    
    # 將合併後的 PDF 寫入 BytesIO 對象
    output = io.BytesIO()
    merger.write(output)
    
    # 返回合併後的 PDF 的 bytes
    return output.getvalue()

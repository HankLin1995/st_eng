import streamlit as st
import pypdfium2 as pdfium
import datetime
import os
import requests
from io import BytesIO

from api import get_projects, get_inspections, get_inspection, update_inspection, upload_inspection_pdf, upload_photo

if "photos" not in st.session_state:
    st.session_state.photos = []  # 用來儲存多張照片的列表
if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None  # 用來儲存上傳的 PDF 檔案
if "selected_inspection_id" not in st.session_state:
    st.session_state.selected_inspection_id = None  # 儲存選中的抽查表ID
if "inspection_data" not in st.session_state:
    st.session_state.inspection_data = None  # 儲存抽查表資料

# API 基礎 URL，預設為 localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 從URL獲取PDF並初始化
def initialize_pdf_from_url(pdf_url):
    """從URL獲取PDF檔案並初始化"""
    try:
        response = requests.get(pdf_url)
        if response.status_code == 200:
            pdf_bytes = BytesIO(response.content)
            pdf = pdfium.PdfDocument(pdf_bytes)
            total_pages = len(pdf)
            pdf_images = {i: pdf[i].render(scale=2).to_pil() for i in range(total_pages)}
            return total_pages, pdf_images
        else:
            st.error(f"❌ 無法獲取PDF: HTTP {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"❌ PDF 初始化錯誤: {e}")
        return None, None

# 顯示 PDF 頁面
def display_pdf_page(total_pages, pdf_images):
    """顯示目前頁面"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0

    current_page = st.session_state.current_page
    if 0 <= current_page < total_pages:
        image_to_show = pdf_images[current_page]
        st.image(image_to_show, caption=f"📄 頁數 {current_page + 1} / {total_pages}")

# 分頁控制
def pagination_controls(total_pages):
    """建立翻頁按鈕"""
    col0, col1, col2, col3 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("⬆️ 上一頁") and st.session_state.current_page > 0:
            st.session_state.current_page -= 1
    with col2:
        if st.button("⬇️ 下一頁") and st.session_state.current_page < total_pages - 1:
            st.session_state.current_page += 1


# 更新抽查資料函數
def update_inspection_data():
    """更新抽查資料、PDF和照片"""
    if not st.session_state.selected_inspection_id:
        st.error("❌ 請先選擇抽查表")
        return
    
    # 準備抽查資料
    inspection_data = {
        "result": check_result,  # 抽查結果
        "remark": check_note  # 備註
    }
    
    # 更新抽查記錄
    result = update_inspection(st.session_state.selected_inspection_id, inspection_data)
    
    if "error" in result:
        st.error(f"❌ 更新抽查資料失敗: {result['error']}")
        return
    
    st.success(f"✅ 抽查資料更新成功！ID: {st.session_state.selected_inspection_id}")
    
    # 重新獲取更新後的抽查資料
    updated_inspection = get_inspection(st.session_state.selected_inspection_id)
    if updated_inspection:
        st.session_state.inspection_data = updated_inspection
        # 清空照片列表和PDF檔案（因為已經上傳了）
        st.session_state.photos = []
        st.session_state.pdf_file = None
        st.rerun()

# 選擇抽查表函數
def select_inspection(inspection_id):
    """選擇抽查表並載入資料"""
    # 設置選中的抽查表ID
    st.session_state.selected_inspection_id = inspection_id
    
    # 獲取抽查表詳細資料
    inspection_data = get_inspection(inspection_id)
    
    # 確保獲取到資料並且格式正確
    if inspection_data and isinstance(inspection_data, dict):
        # 檢查必要欄位是否存在
        required_fields = ["id", "project_id", "subproject_name", "inspection_form_name", 
                          "inspection_date", "location", "timing", "created_at", "updated_at"]
        
        if all(field in inspection_data for field in required_fields):
            # 確保photos欄位存在，如果不存在則設為空列表
            if "photos" not in inspection_data:
                inspection_data["photos"] = []
                
            # 將資料存入session state
            st.session_state.inspection_data = inspection_data
            st.rerun()
        else:
            st.error("❌ 抽查表資料格式不正確，缺少必要欄位")
    else:
        st.error("❌ 無法獲取抽查表資料")

# 側邊欄 - 抽查表選擇
with st.sidebar:
    # st.title("🔍 選擇抽查表")
    
    # # 獲取專案列表
    # projects = get_projects()
    # project_options = ["全部"] + [project["name"] for project in projects]
    # selected_project = st.selectbox("選擇專案", options=project_options)
    
    # # 根據選擇的專案獲取抽查表
    # project_id = None
    # if selected_project != "全部":
    #     for project in projects:
    #         if project["name"] == selected_project:
    #             project_id = project["id"]
    #             break

    project_id = st.session_state.active_project_id
    
    # 獲取抽查表列表
    inspections = get_inspections(project_id)
    
    if inspections:
        # 建立抽查表選項列表
        inspection_options = [f"{insp['inspection_form_name']} - {insp['inspection_date']} (ID: {insp['id']})" for insp in inspections]
        # inspection_options.insert(0, "請選擇抽查表")  # 添加預設選項
        
        # 使用selectbox選擇抽查表
        selected_inspection_option = st.selectbox("抽查表列表", options=inspection_options, key="inspection_selector")
        st.markdown("---")
        # 當選擇了非預設選項時，處理選擇
        if selected_inspection_option != "請選擇抽查表":
            # 從選項中提取ID
            selected_id = int(selected_inspection_option.split("ID: ")[1].strip(")"))
            
            # 如果選擇了新的抽查表，則載入資料
            if st.session_state.selected_inspection_id != selected_id:
                # 清空之前的資料
                st.session_state.photos = []
                st.session_state.pdf_file = None
                
                # 獲取最新資料
                select_inspection(selected_id)

        else:
            st.toast("⭐ 請選擇抽查表")
                
    else:
        st.warning("沒有找到抽查表")
        st.stop()

# 主應用介面
st.subheader(":pencil: 編輯抽查表")

# 檢查是否已選擇抽查表
if st.session_state.selected_inspection_id and st.session_state.inspection_data:
    inspection_data = st.session_state.inspection_data
    
    # 顯示抽查表基本資訊
    st.info(f"📋 抽查表 ID: {inspection_data['id']} | 建立時間: {inspection_data['created_at']} ")
    
    col3, col4 = st.columns([1,1])
    
    with col3.container(border=True):

        # 顯示專案名稱（不可編輯）
        # project_name = ""
        # for project in projects:
        #     if project["id"] == inspection_data["project_id"]:
        #         project_name = project["name"]
        #         break
        
        project_name = st.session_state.active_project

        # 顯示專案名稱、抽查表名稱、日期、地點、抽查時機

        st.markdown(f"🏗️ **專案名稱**: {project_name}")
        st.markdown(f"📋 **抽查表名稱**: {inspection_data['inspection_form_name']}")
        st.markdown(f"📅 **日期**: {inspection_data['inspection_date']}")
        st.markdown(f"🗺️ **地點**: {inspection_data['location']}")
        st.markdown(f"🕒 **抽查時機**: {inspection_data['timing']}")
        st.markdown("---")
        
        # 可編輯的欄位
        st.badge("可編輯的欄位",color="violet")
        check_result = st.pills("✅ 抽查結果", options=["合格", "不合格"], default=inspection_data.get("result", None))
        check_note = st.text_area("🗒️ 備註", value=inspection_data.get("remark", ""), height=100)

        if st.button("儲存更新", type="primary"):
            update_inspection_data()

    with col4:
        # 獲取照片列表
        photos = inspection_data.get("photos", [])
        
        # 先建立 tab 標題：第一個是 PDF，後面依據照片數量建立
        session_photo_tabs = [f"🖼️ 新照片 {i+1}" for i in range(len(st.session_state.photos))]
        existing_photo_tabs = [f"🖼️ 已有照片 {i+1}" for i in range(len(photos))]
        tab_titles = ["📑 PDF 預覽"] + existing_photo_tabs + session_photo_tabs
        
        # 建立 tabs
        tabs = st.tabs(tab_titles)
        
        # === PDF 預覽 Tab ===
        with tabs[0]:
            pdf_file = st.session_state.get("pdf_file", None)
            if pdf_file:
                total_pages, pdf_images = initialize_pdf(pdf_file)
                if total_pages and pdf_images:
                    display_pdf_page(total_pages, pdf_images)
                    pagination_controls(total_pages)
            elif inspection_data.get("pdf_path"):
                # 構建PDF的完整URL
                pdf_filename = os.path.basename(inspection_data['pdf_path'])
                pdf_url = f"{API_BASE_URL}/{inspection_data['pdf_path']}"
                # st.markdown(f"**已上傳PDF**: [{pdf_filename}]({pdf_url})")
                
                # 嘗試顯示PDF
                try:
                    total_pages, pdf_images = initialize_pdf_from_url(pdf_url)
                    if total_pages and pdf_images:
                        display_pdf_page(total_pages, pdf_images)
                        pagination_controls(total_pages)
                    else:
                        st.info("無法顯示PDF預覽，但您可以點擊上方連結查看。")
                except Exception as e:
                    st.error(f"PDF預覽錯誤: {e}")
                    st.info("無法顯示PDF預覽，但您可以點擊上方連結查看。")
            else:
                st.info("尚未上傳 PDF。")
        
        # === 已有照片 Tabs ===
        for i, photo in enumerate(photos):
            with tabs[i + 1]:  # 從第二個tab開始
                # 構建照片的完整URL
                if photo.get('photo_path'):
                    photo_filename = os.path.basename(photo['photo_path'])
                    photo_url = f"{API_BASE_URL}/{photo['photo_path']}"
                    
                    # 顯示照片資訊
                    st.markdown(f"**照片ID**: {photo.get('id', '無ID')}")
                    st.markdown(f"**照片說明**: {photo.get('caption', '無說明')}")
                    st.markdown(f"**拍攝日期**: {photo.get('capture_date', '無日期')}")
                    
                    # 顯示照片
                    try:
                        response = requests.get(photo_url)
                        if response.status_code == 200:
                            st.image(BytesIO(response.content), caption=photo.get('caption', '無說明'))
                        else:
                            st.error(f"無法獲取照片: HTTP {response.status_code}")
                            st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")
                    except Exception as e:
                        st.error(f"照片顯示錯誤: {e}")
                        st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")
        
        # === 新上傳照片 Tabs ===
        for i, photo in enumerate(st.session_state.photos):
            with tabs[i + 1 + len(photos)]:  # 從已有照片後開始
                st.image(photo["file"], caption=f"圖片說明: {photo['caption']}")
                st.button("刪除照片", key=f"delete_photo_{i}", on_click=lambda i=i: st.session_state.photos.pop(i) if len(st.session_state.photos) > 1 else st.session_state.photos.clear())

else:
    st.info("👈 請從側邊欄選擇要編輯的抽查表")
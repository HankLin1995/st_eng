import streamlit as st
import pypdfium2 as pdfium
import datetime

from api import get_projects, create_inspection, upload_inspection_pdf, upload_photo, get_project_storage

if "photos" not in st.session_state:
    st.session_state.photos = []  # 用來儲存多張照片的列表
if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None  # 用來儲存上傳的 PDF 檔案
if "project_id" not in st.session_state:
    st.session_state.project_id = None  # 用來儲存專案ID

# PDF 初始化（不儲存檔案）
def initialize_pdf(uploaded_file):
    """直接使用上傳的檔案初始化 PDF 並返回頁數與圖像"""
    try:
        pdf = pdfium.PdfDocument(uploaded_file)
        total_pages = len(pdf)
        pdf_images = {i: pdf[i].render(scale=2).to_pil() for i in range(total_pages)}
        return total_pages, pdf_images
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

@st.dialog("📤 上傳抽查表")
def upload_pdf_ui():

    pdf_file = st.file_uploader("請選擇", type=["pdf", "jpg", "jpeg", "png"])

    #確認目前系統餘裕

    if st.button("確認上傳"):
        st.session_state.pdf_file = pdf_file
        st.rerun()

@st.dialog("📤 上傳照片")
def upload_photos_ui():

    # capture_date = st.date_input("📅 照片日期")
    caption = st.text_input("照片說明", placeholder="例如：檢查結果、問題點等")
    # Define the accepted file types explicitly
    uploaded_file = st.file_uploader("請選擇", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption='Uploaded Image')

        # Append the uploaded file to the session state

        if st.button("確認上傳"):
            st.session_state.photos.append({
                "file": uploaded_file,
                # "date": capture_date,
                "caption": caption
            })
            st.success("照片上傳成功！")
            st.rerun()

# 儲存資料函數
def save_inspection_data():
    """儲存抽查資料、PDF和照片"""
    # 獲取選中的專案ID
    selected_project_name = check_project
    project_id = None
    
    # 從專案列表中找到對應的專案ID
    projects = get_projects()
    for project in projects:
        if project["name"] == selected_project_name:
            project_id = project["id"]
            break
    
    if not project_id:
        st.error("❌ 無法找到所選專案，請重新選擇")
        return
    
    # 準備抽查資料
    inspection_data = {
        "project_id": project_id,
        "subproject_name": check_item,  # 使用抽查項目作為子專案名稱
        "inspection_form_name": check_item,  # 使用抽查項目作為表單名稱
        "inspection_date": check_date.isoformat(),  # 轉換為ISO格式的日期字符串
        "location": check_location,
        "timing": check_type,  # 抽查時機
        "result": check_result,  # 抽查結果
        "remark": check_note  # 備註
    }
    
    # 建立抽查記錄
    result = create_inspection(inspection_data)
    
    if "error" in result:
        st.error(f"❌ 儲存抽查資料失敗: {result['error']}")
        return
    
    inspection_id = result["id"]
    st.success(f"✅ 抽查資料儲存成功！ID: {inspection_id}")
    
    # 上傳PDF檔案（如果有）
    if st.session_state.pdf_file:
        pdf_result = upload_inspection_pdf(inspection_id, st.session_state.pdf_file)
        if "error" in pdf_result:
            st.error(f"❌ PDF上傳失敗: {pdf_result['error']}")
        else:
            st.success("✅ PDF上傳成功！")
    
    # 上傳照片（如果有）
    for photo in st.session_state.photos:
        # 取得目前日期作為照片日期
        today = datetime.date.today().isoformat()
        
        photo_result = upload_photo(
            inspection_id=inspection_id,
            file=photo["file"],
            capture_date=today,
            caption=photo["caption"]
        )
        
        if "error" in photo_result:
            st.error(f"❌ 照片上傳失敗: {photo_result['error']}")
        else:
            st.success(f"✅ 照片「{photo['caption']}」上傳成功！")
    
    # 清空表單和session state
    st.session_state.photos = []
    st.session_state.pdf_file = None
    st.rerun()

try:

    current_storage=get_project_storage(st.session_state.project_id)
    # 移除儲存空間限制，只顯示已使用空間
    used_space_mb = int(current_storage['total_size_bytes']/1024/1024)
    available_space = f"已使用: {used_space_mb} MB (無限制)"

except:
    available_space="未能獲取使用情況"

# 主應用介面

st.subheader("✏️  新增抽查表")
st.info(f"目前工程-> {st.session_state.active_project} | 📦 剩餘空間: {available_space}")

if st.session_state.active_project is None:
    st.error("請先建立專案")
    st.stop()

col3, col4 = st.columns([1,1])

with col3.container(border=True):

    st.badge("填寫抽查資料",color="violet")

    prjs=get_projects(owner="TEST_EMAIL")#st.user.email)

    get_project_list = [item["name"] for item in prjs]

    # check_project = st.selectbox("🏗️ 專案名稱", options=get_project_list,disabled=True)
    check_project=st.session_state.active_project
    check_date = st.date_input("📅 日期")
    check_location = st.text_input("🗺️ 地點")
    check_item = st.text_input("📝 抽查項目")
    check_type = st.pills("🕒 抽查時機", options=["檢驗停留點", "隨機抽查", "其他"])
    check_result = st.pills("✅ 抽查結果", options=["合格", "不合格"])
    check_note = st.text_area("🗒️ 備註", height=100)

    # Find the selected project's ID
    selected_project = next(item for item in prjs if item["name"] == check_project)
    project_id = selected_project["id"]

    st.session_state.project_id = project_id

with col4:

    # 先建立 tab 標題：第一個是 PDF，後面依據照片數量建立
    photo_tabs = [f"🖼️ 照片 {i+1}" for i in range(len(st.session_state.photos))]
    tab_titles = ["📑 PDF 預覽"] + photo_tabs

    # 建立 tabs
    tabs = st.tabs(tab_titles)

    # === PDF 預覽 Tab ===
    with tabs[0]:
        # with st.expander("📑 PDF 預覽", expanded=True):
        pdf_file = st.session_state.get("pdf_file", None)
        if pdf_file:
            total_pages, pdf_images = initialize_pdf(pdf_file)
            if total_pages and pdf_images:
                display_pdf_page(total_pages, pdf_images)
                pagination_controls(total_pages)
        else:
            st.info("尚未上傳 PDF。")

    # === 每張照片一個 Tab ===
    for i, photo in enumerate(st.session_state.photos):
        with tabs[i + 1]:  # tabs[1] 是第一張照片
            st.image(photo["file"], caption="圖片說明: "+photo["caption"])
            st.button("刪除照片", key=f"delete_photo_{i}", on_click=lambda i=i: st.session_state.photos.pop(i) if len(st.session_state.photos) > 1 else st.session_state.photos.clear())  # 刪除照片按鈕

# PDF 預覽區

# with col4.expander("📑 PDF 預覽", expanded=True):

#         # pdf_file = st.file_uploader("📤 上傳抽查紀錄表", type=["pdf", "jpg", "jpeg", "png"])
#         pdf_file=st.session_state.pdf_file
#         if pdf_file:
#             total_pages, pdf_images = initialize_pdf(pdf_file)
#             if total_pages and pdf_images:
#                 display_pdf_page(total_pages, pdf_images)
#                 pagination_controls(total_pages)

# import itertools

# col5, col6, col7 = st.columns([1, 1, 1])
# columns = itertools.cycle([col5, col6, col7])

# for photo in st.session_state.photos:
#     col = next(columns)
#     with col:
#         st.image(photo["file"], caption=photo["caption"])

## 加入上傳照片按鈕
            
# 移除儲存空間限制檢查
# max_size=100*1024*1024
# if current_storage['total_size_bytes'] <= max_size:
# 允許無限上傳

if st.sidebar.button("📤 上傳抽查表", key="upload_pdf"):
    upload_pdf_ui()

if st.sidebar.button("📸 上傳照片", key="upload_photos"):
    upload_photos_ui()

st.sidebar.markdown("---")

st.markdown("---")

if st.button("儲存資料", type="primary"):
    save_inspection_data()
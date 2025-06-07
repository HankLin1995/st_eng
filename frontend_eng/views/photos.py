import streamlit as st
import pandas as pd
import time
import os
from io import BytesIO
import requests
from api import (
    get_photos,
    get_photo,
    upload_photo,
    update_photo,
    delete_photo
)
from convert import get_inspections_df, get_photos_df

# inspections_df = get_inspections_df(st.session_state.active_project_id)

# API 基礎 URL，預設為 localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_project_photos_df():

    inspections_df = get_inspections_df(st.session_state.active_project_id)
    # 取得照片資料
    df = get_photos_df()
    
    if df.empty:
        st.info("目前沒有照片資料")
        st.stop()
        return
    
    # 合併抽查資訊
    if not inspections_df.empty:
        df = pd.merge(
            df, 
            inspections_df[["抽查編號", "檢查位置", "抽查表名稱", "抽查次數"]], 
            left_on="抽查編號", 
            right_on="抽查編號", 
            how="right"
        )

    return df

# @st.cache_data()
def get_filter_df(inspection_name=None, inspection_count=None):
    # 取得照片資料
    df = get_project_photos_df()
    
    # if df.empty:
    #     st.info("目前沒有照片資料")
    #     st.stop()
    #     return
    
    # # 合併抽查資訊
    # if not inspections_df.empty:
    #     df = pd.merge(
    #         df, 
    #         inspections_df[["抽查編號", "檢查位置", "抽查表名稱", "抽查次數"]], 
    #         left_on="抽查編號", 
    #         right_on="抽查編號", 
    #         how="left"
    #     )

    # 根據選擇的抽查表名稱和次數進行篩選
    if inspection_name != "全部抽查表":
        df = df[df["抽查表名稱"] == inspection_name]
        
        if inspection_count != "全部次數":
            count_num = int(inspection_count.replace("第", "").replace("次", ""))
            df = df[df["抽查次數"] == count_num]
    
    if df.empty:
        st.info("沒有符合篩選條件的照片")
        st.stop()
        return

    return df

def get_filter_options():
    # 篩選條件
    inspections_df = get_inspections_df(st.session_state.active_project_id)

    # 建立抽查表名稱的唯一列表
    # inspection_names = ["全部抽查表"]
    inspection_names = []
    inspection_name_to_counts = {}

    if not inspections_df.empty:
        # 獲取唯一的抽查表名稱
        unique_names = inspections_df["抽查表名稱"].unique()
        inspection_names.extend(unique_names)
        
        # 為每個抽查表名稱建立對應的抽查次數字典
        for name in unique_names:
            counts = inspections_df[inspections_df["抽查表名稱"] == name]["抽查次數"].unique()
            inspection_name_to_counts[name] = ["全部次數"] + [f"第{count}次" for count in sorted(counts)]

    # 第一個下拉選單：選擇抽查表名稱
    selected_inspection_name = st.sidebar.selectbox(
        "依抽查表名稱篩選", 
        inspection_names
    )

    # 第二個下拉選單：選擇抽查次數（根據選擇的抽查表名稱動態變化）
    count_options = ["全部次數"]
    if selected_inspection_name != "全部抽查表" and selected_inspection_name in inspection_name_to_counts:
        count_options = inspection_name_to_counts[selected_inspection_name]

    selected_count = st.sidebar.selectbox(
        "依抽查次數篩選",
        count_options
    )

    return selected_inspection_name, selected_count

def single_card(row):
    # 構建照片的完整URL
    if '檔案路徑' in row:
        photo_filename = os.path.basename(row['檔案路徑'])
        photo_url = f"{API_BASE_URL}/{row['檔案路徑']}"
        
        # 顯示照片資訊
        st.markdown(f"**照片ID**: {row.get('照片編號', '無ID')}")
        # st.markdown(f"**照片說明**: {row.get('描述', '無說明')}")
        st.markdown(f"**檢查位置**: {row.get('檢查位置', '無位置')}")
        
        # 顯示照片
        try:
            response = requests.get(photo_url)
            if response.status_code == 200:
                st.image(BytesIO(response.content), caption=row.get('描述', '無說明'))
            else:
                st.error(f"無法獲取照片: HTTP {response.status_code}")
                st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")
        except Exception as e:
            st.error(f"照片顯示錯誤: {e}")
            st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")

# 上傳照片對話框
@st.dialog("📤上傳照片")
def upload_photo_ui():
    if inspections_df.empty:
        st.warning("請先建立抽查")
        return
    
    with st.form("upload_photo_form"):
        
        inspection_options = [f"{row['抽查表名稱']} - 第{row['抽查次數']}次 - {row['抽查編號']} - {row['檢查位置']}" for _, row in inspections_df.iterrows()]
        selected_inspection = st.selectbox("選擇抽查", inspection_options)
        capture_date = st.date_input("拍照日期")
        caption = st.text_input("照片描述", placeholder="請輸入照片描述")
        photo_file = st.file_uploader("選擇照片", type=["jpg", "jpeg", "png"])
        
        # if photo_file:
        #     st.image(photo_file)
        
        submitted = st.form_submit_button("上傳")
        if submitted:
            if not all([selected_inspection, photo_file]):
                st.error("請選擇抽查並上傳照片")
                return
            
            # 取得抽查 ID
            inspection_id = int(selected_inspection.split(" - ")[2])
            
            response = upload_photo(inspection_id, photo_file,capture_date.strftime("%Y-%m-%d"), caption)
            if "error" not in response:
                st.toast("照片上傳成功", icon="✅")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"上傳失敗: {response['error']}")

# 編輯照片對話框
@st.dialog("✏️編輯照片")
def update_photo_ui():
    # 取得照片列表
    photos_df = get_project_photos_df()
    # if photos_df.empty:
    #     st.warning("目前沒有照片可編輯")
    #     return
    
    # # 合併抽查資訊
    # if not inspections_df.empty:
    #     photos_df = pd.merge(
    #         photos_df, 
    #         inspections_df[["抽查編號", "檢查位置", "抽查表名稱", "抽查次數"]], 
    #         left_on="抽查編號", 
    #         right_on="抽查編號", 
    #         how="left"
    #     )
    
    # 選擇照片
    photo_options = [f"{row['照片編號']}" for _, row in photos_df.iterrows()]
    selected_photo = st.selectbox("選擇照片", photo_options)
    
    if not selected_photo:
        st.warning("請選擇要編輯的照片")
        return
    
    # 取得照片 ID
    photo_id = selected_photo#int(selected_photo.split(" - ")[2])
    
    # 取得照片詳細資料
    photo = get_photo(photo_id)
    if not photo:
        st.error("無法取得照片資料")
        return
    
    # 編輯表單
    with st.form("edit_photo_form"):
        # 顯示照片預覽
        photo_url = f"{API_BASE_URL}/{photo['photo_path']}"
        try:
            response = requests.get(photo_url)
            if response.status_code == 200:
                st.image(BytesIO(response.content), caption=photo.get('caption', '無說明'))
            else:
                st.error(f"無法獲取照片: HTTP {response.status_code}")
                photo_filename = os.path.basename(photo['photo_path'])
                st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")
        except Exception as e:
            st.error(f"照片顯示錯誤: {e}")
            photo_filename = os.path.basename(photo['photo_path'])
            st.markdown(f"**照片連結**: [{photo_filename}]({photo_url})")
        
        caption = st.text_input("照片描述", value=photo.get("caption", ""))
        
        submitted = st.form_submit_button("更新")
        if submitted:
            data = {
                "caption": caption,
            }
            
            response = update_photo(photo_id, data)
            if "error" not in response:
                st.toast("照片更新成功", icon="✅")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"更新失敗: {response['error']}")

# 刪除照片對話框
@st.dialog("🗑️刪除照片")
def delete_photo_ui():
    # 取得照片列表
    photos_df = get_project_photos_df()
    # if photos_df.empty:
    #     st.warning("目前沒有照片可刪除")
    #     return
    
    # # 合併抽查資訊
    # if not inspections_df.empty:
    #     photos_df = pd.merge(
    #         photos_df, 
    #         inspections_df[["抽查編號", "檢查位置", "抽查表名稱", "抽查次數"]], 
    #         left_on="抽查編號", 
    #         right_on="抽查編號", 
    #         how="left"
    #     )
    
    # 選擇照片
    photo_options = [f"{row['抽查表名稱']} - 第{row['抽查次數']}次 - {row['照片編號']} - {row['檢查位置']} - {row['描述']}" for _, row in photos_df.iterrows()]
    selected_photo = st.selectbox("選擇照片", photo_options)
    
    if not selected_photo:
        st.warning("請選擇要刪除的照片")
        return
    
    # 取得照片 ID
    photo_id = int(selected_photo.split(" - ")[2])
    
    # 確認刪除
    st.warning("⚠️ 刪除照片後無法復原！")
    
    if st.button("確認刪除"):
        response = delete_photo(photo_id)
        if "error" not in response:
            st.toast("照片刪除成功", icon="✅")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"刪除失敗: {response['error']}")

##### MAIN UI #####

selected_inspection_name, selected_count = get_filter_options()

st.sidebar.markdown("---")

df=get_filter_df(selected_inspection_name, selected_count)

if not df.empty:
    st.subheader(f"📸 照片圖廊")
    st.info(f"目前工程-> {st.session_state.active_project}")
    cols = st.columns(3, border=True)
    for i, (_, row) in enumerate(df.iterrows()):
        with cols[i % 3]:
            single_card(row)

st.markdown("---")

# 按鈕列
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📤上傳照片", use_container_width=True):
        upload_photo_ui()

with col2:
    if st.button("✏️編輯照片", use_container_width=True):
        update_photo_ui()

with col3:
    if st.button("🗑️刪除照片", use_container_width=True):
        delete_photo_ui()
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from api import (
    get_project,
    get_inspections,
    get_inspection,
    create_inspection,
    update_inspection,
    delete_inspection,
    upload_inspection_pdf
)
from convert import get_projects_df, get_inspections_df

from api import API_BASE_URL

@st.cache_data()
def get_merged_df(project_filter):

        # 取得抽查資料
    df = get_inspections_df(project_filter['id'])
    
    if df.empty:
        st.info("目前沒有抽查資料")
        return
    
    # 合併專案名稱
    if not projects_df.empty:
        df = pd.merge(
            df, 
            projects_df[["專案編號", "專案名稱"]], 
            left_on="專案編號", 
            right_on="專案編號", 
            how="left"
        )

    return df

@st.dialog("📝新增抽查")
def add_inspection_ui():
    if projects_df.empty:
        st.warning("請先建立專案")
        return
    
    st.subheader("新增抽查紀錄")
    with st.form("add_inspection_form", clear_on_submit=True):
        # 專案選擇
        project_options = [(str(p.專案編號), p.專案名稱) for p in get_projects_df(owner="TEST_EMAIL").itertuples(index=False)]
        project_id = st.selectbox("所屬專案", options=[x[0] for x in project_options], format_func=lambda x: dict(project_options)[x])

        subproject_name = st.text_input("分項工程名稱")
        inspection_form_name = st.text_input("抽查表名稱")
        inspection_date = st.date_input("抽查日期")
        location = st.text_input("檢查位置")
        timing = st.selectbox("抽查時機", options=["檢驗停留點", "隨機抽查"])
        result = st.selectbox("抽查結果", options=["合格", "不合格"])
        remark = st.text_area("備註")

        submitted = st.form_submit_button("新增抽查")
        if submitted:
            if not all([project_id, subproject_name, inspection_form_name, inspection_date, location, timing, result]):
                st.warning("請填寫所有必填欄位")
            else:
                data = {
                    "project_id": int(project_id),
                    "subproject_name": subproject_name,
                    "inspection_form_name": inspection_form_name,
                    "inspection_date": inspection_date.strftime("%Y-%m-%d"),
                    "location": location,
                    "timing": timing,
                    "result": result,
                    "remark": remark
                }
                resp = create_inspection(data)
                if "error" not in resp:
                    st.toast("新增抽查成功", icon="✅")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"新增抽查失敗: {resp['error']}")

# 編輯抽查對話框
@st.dialog("✏️編輯抽查")
def update_inspection_ui():
    # 取得抽查列表
    inspections_df = get_inspections_df()
    if inspections_df.empty:
        st.warning("目前沒有抽查可編輯")
        return
    
    # 合併專案名稱
    if not projects_df.empty:
        inspections_df = pd.merge(
            inspections_df, 
            projects_df[["專案編號", "專案名稱"]], 
            left_on="專案編號", 
            right_on="專案編號", 
            how="left"
        )
    
    # 選擇抽查
    inspection_options = [f"{row['抽查編號']} - {row['專案名稱']} - {row['檢查位置']}" for _, row in inspections_df.iterrows()]
    selected_inspection = st.selectbox("選擇抽查", inspection_options)
    
    if not selected_inspection:
        st.warning("請選擇要編輯的抽查")
        return
    
    # 取得抽查 ID
    inspection_id = int(selected_inspection.split(" - ")[0])
    
    # 取得抽查詳細資料
    inspection = get_inspection(inspection_id)
    if not inspection:
        st.error("無法取得抽查資料")
        return
    
    # 編輯表單
    with st.form("edit_inspection_form"):
        # 只能編輯結果和備註
        result = st.selectbox("抽查結果", ["合格", "不合格"], index=["合格", "不合格"].index(inspection.get("result", "合格") or "合格"))
        remark = st.text_area("備註", value=inspection.get("remark", ""))
        


        # 顯示其他不可編輯的欄位
        st.info(f"所屬專案: {projects_df[projects_df['專案編號'] == inspection['project_id']]['專案名稱'].values[0] if not projects_df.empty else ''}")
        st.info(f"分項工程名稱: {inspection.get('subproject_name', '')}")
        st.info(f"抽查表名稱: {inspection.get('inspection_form_name', '')}")
        st.info(f"檢查位置: {inspection.get('location', '')}")
        st.info(f"抽查時機: {inspection.get('timing', '')}")
        st.info(f"抽查日期: {inspection.get('inspection_date', '')}")
        
        # 上傳 PDF
        pdf_file = st.file_uploader("上傳報告 PDF", type=["pdf"])
        
        submitted = st.form_submit_button("更新")
        if submitted:
            data = {
                "result": result,
                "remark": remark
            }
            
            response = update_inspection(inspection_id, data)
            if "error" not in response:
                st.toast("抽查更新成功", icon="✅")
                
                # 如果有上傳 PDF
                if pdf_file:
                    pdf_response = upload_inspection_pdf(inspection_id, pdf_file)
                    if "error" not in pdf_response:
                        st.toast("PDF 上傳成功", icon="✅")
                    else:
                        st.error(f"PDF 上傳失敗: {pdf_response['error']}")
                
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"更新失敗: {response['error']}")

# 刪除抽查對話框
@st.dialog("🗑️刪除抽查")
def delete_inspection_ui():
    # 取得抽查列表
    inspections_df = get_inspections_df()
    if inspections_df.empty:
        st.warning("目前沒有抽查可刪除")
        return
    
    # 合併專案名稱
    if not projects_df.empty:
        inspections_df = pd.merge(
            inspections_df, 
            projects_df[["專案編號", "專案名稱"]], 
            left_on="專案編號", 
            right_on="專案編號", 
            how="left"
        )
    
    # 選擇抽查
    inspection_options = [f"{row['抽查編號']} - {row['專案名稱']} - {row['檢查位置']}" for _, row in inspections_df.iterrows()]
    selected_inspection = st.selectbox("選擇抽查", inspection_options)
    
    if not selected_inspection:
        st.warning("請選擇要刪除的抽查")
        return
    
    # 取得抽查 ID
    inspection_id = int(selected_inspection.split(" - ")[0])
    
    # 確認刪除
    st.warning("⚠️ 刪除抽查將同時刪除所有相關照片，此操作無法復原！")
    
    if st.button("確認刪除"):
        response = delete_inspection(inspection_id)
        if "error" not in response:
            st.toast("抽查刪除成功", icon="✅")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"刪除失敗: {response['error']}")


##### MAIN_UI #####

st.subheader(f"🔍 抽查表清單")
st.info(f"目前工程-> {st.session_state.active_project}")

# 取得目標專案

# projects_df = get_projects_df(owner=st.user.email)
# project_filter = st.sidebar.selectbox(
#     "依專案篩選", 
#     ["全部工程"] + projects_df["工程名稱"].tolist() if not projects_df.empty else ["全部工程"]
# )

# if project_filter == "全部工程":
#     project_id=None
# else:
#     project_id=projects_df[projects_df["工程名稱"] == project_filter]["專案編號"].values[0]

project_id = st.session_state.active_project_id

df = get_inspections_df(project_id)

if df.empty:
    st.warning("沒有找到抽查表")
    st.stop()

# st.write(df)

# 顯示篩選後的抽查清單

# if project_filter != "全部工程":
    # df=df[df["專案編號"] == project_id]

# df=df[df["專案編號"] == project_id]

df_show=df[["抽查編號", "抽查表名稱", "抽查日期","檢查位置", "抽查結果"]].style.format({
        "抽查日期": lambda x: x
    })

# 顯示抽查資料表
event = st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
)

selection = event.selection.rows

inspection_data={}

if selection:

    filtered_df = df.iloc[selection]

    # st.write(filtered_df)

    if st.button("🗑️ 刪除報表", key="delete_multiple"):

        for _, row in filtered_df.iterrows():
            inspection_id = int(row['抽查編號'])

            delete_inspection(inspection_id)
            st.toast("刪除成功", icon="✅")

        st.cache_data.clear()
        time.sleep(1)
        st.rerun()

st.markdown("---")

if len(selection) > 0:
    if st.button("📝列印報表", key="print_multiple"):
        from utils import generate_pdf, merge_multiple_pdfs
        
        # 取得所有選中的抽查報表數據
        filtered_df = df.iloc[selection]

        pdf_files_list = []
        
        # 遍歷所有選中的抽查
        for i, (_, row) in enumerate(filtered_df.iterrows()):

            # 獲取完整的抽查數據
            insp_id = int(row['抽查編號'])
            insp_data = get_inspection(insp_id)
            # st.write(insp_data)
            
            if insp_data:
                # # 添加原始 PDF（如果有）
                # if insp_data.get('pdf_path'):
                #     pdf_url = f"http://localhost:8000/{insp_data.get('pdf_path')}"
                #     pdf_files_list.append((pdf_url, True))
                
                # # 生成並添加照片報告 PDF
                # photo_pdf_bytes = generate_pdf(insp_data)
                # pdf_files_list.append((photo_pdf_bytes, False))
                # 添加原始 PDF（如果有）
                if insp_data.get('pdf_path'):
                    pdf_url = f"{API_BASE_URL}/{insp_data.get('pdf_path')}"
                    pdf_files_list.append((pdf_url, True))

                # 照片分組，每3張為一組
                photos = insp_data.get('photos', [])
                for j in range(0, len(photos), 3):
                    photo_group = photos[j:j+3]
                    
                    # 為這組照片建立新的 inspection data (僅包含這組照片)
                    temp_insp_data = insp_data.copy()
                    temp_insp_data["photos"] = photo_group

                    # 生成報告 PDF 並加入清單
                    photo_pdf_bytes = generate_pdf(temp_insp_data)
                    pdf_files_list.append((photo_pdf_bytes, False))
        # 合併所有 PDF
        merged_pdf_bytes = merge_multiple_pdfs(pdf_files_list)
        
        if merged_pdf_bytes:
            # 在 Streamlit 中顯示下載按鈕
            st.download_button(
                label="下載合併 PDF 報告",
                data=merged_pdf_bytes,
                file_name=f"multiple_inspection_reports_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("合併 PDF 失敗，請確認選擇的報表有效。")

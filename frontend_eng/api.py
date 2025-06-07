import requests
import os
from dotenv import load_dotenv
import streamlit as st

# 載入環境變數
load_dotenv()

# API 基礎 URL，預設為 localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 專案相關 API
def get_projects(owner=None):
    """取得所有專案"""
    try:
        headers = {}
        if owner:
            headers["owner"] = owner
            
        response = requests.get(f"{API_BASE_URL}/api/projects/", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得專案失敗: {response.text}")
            return []
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return []

def get_project(project_id, owner=None):
    """取得單一專案詳細資料（含巡檢）"""
    try:
        headers = {}
        if owner:
            headers["owner"] = owner
            
        response = requests.get(f"{API_BASE_URL}/api/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得專案詳細資料失敗: {response.text}")
            return None
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return None

def create_project(data):
    """建立新專案"""
    # print(data)
    try:
        # 確保包含所有必要欄位
        required_fields = ["name", "location", "contractor", "start_date", "end_date","owner"]
        for field in required_fields:
            if field not in data:
                return {"error": f"缺少必要欄位: {field}"}
        
        # 從 data 中提取 owner 並放入標頭
        owner = data.get("owner")
        headers = {"owner": owner} if owner else {}
        
        response = requests.post(f"{API_BASE_URL}/api/projects/", json=data, headers=headers)
        if response.status_code == 201:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def update_project(project_id, data):
    """更新專案資料"""
    # print(data)
    try:
        # 確保包含所有必要欄位
        required_fields = ["name", "location", "contractor", "start_date", "end_date","owner"]
        for field in required_fields:
            if field not in data:
                return {"error": f"缺少必要欄位: {field}"}
        
        # 從 data 中提取 owner 並放入標頭
        owner = data.get("owner")
        headers = {"owner": owner} if owner else {}
        
        response = requests.put(f"{API_BASE_URL}/api/projects/{project_id}", json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def delete_project(project_id, owner=None):
    """刪除專案"""
    try:
        headers = {"owner": owner} if owner else {}
        response = requests.delete(f"{API_BASE_URL}/api/projects/{project_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

# 巡檢相關 API
def get_inspections(project_id=None):
    """取得所有巡檢，可選依專案篩選"""
    try:
        url = f"{API_BASE_URL}/api/inspections/"
        params = {}
        if project_id:
            params["project_id"] = project_id
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得巡檢失敗: {response.text}")
            return []
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return []

def get_inspection(inspection_id):
    """取得單一巡檢詳細資料（含照片）"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/inspections/{inspection_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得巡檢詳細資料失敗: {response.text}")
            return None
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return None

def create_inspection(data):
    """建立新巡檢"""
    try:
        # 確保包含所有必要欄位
        required_fields = ["project_id", "subproject_name", "inspection_form_name", "inspection_date", "location", "timing"]
        for field in required_fields:
            if field not in data:
                return {"error": f"缺少必要欄位: {field}"}
        
        response = requests.post(f"{API_BASE_URL}/api/inspections/", json=data)
        if response.status_code == 201:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def update_inspection(inspection_id, data):
    """更新巡檢資料"""
    try:
        # 檢查必要欄位 (InspectionUpdate 模型只要求 result 欄位)
        if "result" not in data:
            return {"error": "缺少必要欄位: result"}
        
        response = requests.put(f"{API_BASE_URL}/api/inspections/{inspection_id}", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def delete_inspection(inspection_id):
    """刪除巡檢"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/inspections/{inspection_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def upload_inspection_pdf(inspection_id, file):
    """上傳巡檢 PDF"""
    try:
        files = {"file": (file.name,file.getvalue(), "application/pdf")}
        response = requests.post(f"{API_BASE_URL}/api/inspections/{inspection_id}/upload-pdf", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

# 照片相關 API
def get_photos(inspection_id=None):
    """取得所有照片，可選依巡檢篩選"""
    try:
        url = f"{API_BASE_URL}/api/photos/"
        params = {}
        if inspection_id:
            params["inspection_id"] = inspection_id
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得照片失敗: {response.text}")
            return []
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return []

def get_photo(photo_id):
    """取得單一照片詳細資料"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/photos/{photo_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"取得照片詳細資料失敗: {response.text}")
            return None
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return None

def upload_photo(inspection_id, file, capture_date, caption):
    """上傳照片"""
    try:
        files = {"file": (file.name, file, "image/jpeg")}
        data = {"inspection_id": inspection_id, "capture_date": capture_date, "caption": caption}
        response = requests.post(f"{API_BASE_URL}/api/photos/", files=files, data=data)
        if response.status_code == 201:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def update_photo(photo_id, data):
    """更新照片資料"""
    try:
        response = requests.put(f"{API_BASE_URL}/api/photos/{photo_id}", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def delete_photo(photo_id):
    """刪除照片"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/photos/{photo_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

# 儲存空間相關 API
def get_project_storage(project_id, owner=None):
    """獲取專案的儲存空間信息"""
    try:
        headers = {}
        if owner:
            headers["owner"] = owner
        
        response = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/storage", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            # st.error(f"獲取儲存空間信息失敗: {response.text}")
            return None
    except Exception as e:
        st.error(f"API 連線錯誤: {str(e)}")
        return None

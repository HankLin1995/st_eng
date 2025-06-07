import pandas as pd
from api import get_projects, get_inspections, get_photos

def get_projects_df(owner):
    """將專案資料轉換為 DataFrame 格式"""
    projects = get_projects(owner)
    if not projects:
        return pd.DataFrame()
    
    # 轉換為 DataFrame 並重新命名欄位為中文
    df = pd.DataFrame(projects)
    if not df.empty:
        # 重新命名欄位
        df = df.rename(columns={
            "id": "專案編號",
            "name": "工程名稱",
            "location": "工程位置",
            "contractor": "承攬廠商",
            "start_date": "開始日期",
            "end_date": "結束日期",
            "owner": "專案擁有者"
        })
        
        # 轉換日期格式
        if "開始日期" in df.columns:
            df["開始日期"] = pd.to_datetime(df["開始日期"]).dt.strftime("%Y-%m-%d")
        if "結束日期" in df.columns:
            df["結束日期"] = pd.to_datetime(df["結束日期"]).dt.strftime("%Y-%m-%d")
    
    return df

def get_inspections_df(project_id=None):
    """將巡檢資料轉換為 DataFrame 格式"""
    inspections = get_inspections(project_id)
    if not inspections:
        return pd.DataFrame()
    
    # 轉換為 DataFrame 並重新命名欄位為中文
    df = pd.DataFrame(inspections)
    if not df.empty:
        # 重新命名欄位
        df = df.rename(columns={
            "id": "抽查編號",
            "project_id": "專案編號",
            "subproject_name": "分項工程名稱",
            "inspection_form_name": "抽查表名稱",
            "inspection_date": "抽查日期",
            "location": "檢查位置",
            "timing": "抽查時機",
            "result": "抽查結果",
            "remark": "備註",
            "pdf_path": "PDF路徑",
            "created_at": "建立時間",
            "updated_at": "更新時間"
        })
        
        # 計算每個抽查表名稱的抽查次數
        inspection_counts = df.groupby('抽查表名稱').cumcount() + 1
        df['抽查次數'] = inspection_counts
        
        # 轉換日期格式
        if "抽查日期" in df.columns:
            df["抽查日期"] = pd.to_datetime(df["抽查日期"]).dt.strftime("%Y-%m-%d")
        if "建立時間" in df.columns:
            df["建立時間"] = pd.to_datetime(df["建立時間"]).dt.strftime("%Y-%m-%d %H:%M")
        if "更新時間" in df.columns:
            df["更新時間"] = pd.to_datetime(df["更新時間"]).dt.strftime("%Y-%m-%d %H:%M")
    
    return df

def get_photos_df(inspection_id=None):
    """將照片資料轉換為 DataFrame 格式"""
    photos = get_photos(inspection_id)
    if not photos:
        return pd.DataFrame()
    
    # 轉換為 DataFrame 並重新命名欄位為中文
    df = pd.DataFrame(photos)
    if not df.empty:
        # 重新命名欄位
        df = df.rename(columns={
            "id": "照片編號",
            "inspection_id": "抽查編號",
            "photo_path": "檔案路徑",
            "caption": "描述",
            "capture_date": "上傳時間"
        })
        
        # 轉換日期格式
        if "上傳時間" in df.columns:
            df["上傳時間"] = pd.to_datetime(df["上傳時間"]).dt.strftime("%Y-%m-%d %H:%M")
    
    return df

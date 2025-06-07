# 施工抽查系統 | ST Engineering Inspection System

## 專案概述 | Project Overview
此專案包含一個使用 Python 構建的後端 API 服務和一個使用 Streamlit 構建的前端網頁應用程式。該系統專為施工抽查管理和數據處理而設計。

This project consists of a backend API service built with Python and a frontend web application built with Streamlit. The system is designed for construction inspection management and data processing.

## 專案結構 | Project Structure
- `backend_eng/`: 後端 API 服務 | Backend API service
- `frontend_eng/`: 前端 Streamlit 應用程式 | Frontend Streamlit application

## 系統需求 | Prerequisites
- Docker 和 Docker Compose | Docker and Docker Compose

## 開始使用 | Getting Started

### 啟動應用程式 | Running the Application
執行以下命令啟動所有服務：

To start all services:

```bash
docker-compose up --build -d
```

這將啟動：
This will start:
1. 後端 API 服務（可通過端口 8000 訪問）| Backend API service (accessible on port 8000)
2. 前端 Streamlit 應用程式（可通過端口 8501 訪問）| Frontend Streamlit application (accessible on port 8501)
3. MySQL 資料庫（可通過端口 3306 訪問）| MySQL database (accessible on port 3306)

### 訪問應用程式 | Accessing the Application
- 前端 | Frontend: http://localhost:8501
- 後端 API | Backend API: http://localhost:8000

## 開發 | Development

### 後端開發 | Backend Development
後端位於 `backend_eng` 目錄中，使用 MySQL 資料庫進行數據存儲。

The backend is located in the `backend_eng` directory. It uses a MySQL database for data storage.

### 前端開發 | Frontend Development
前端位於 `frontend_eng` 目錄中，使用 Streamlit 構建，並與後端 API 通信。

The frontend is located in the `frontend_eng` directory. It's built with Streamlit and communicates with the backend API.

## 部署 | Deployment
該應用程式配置為使用 Docker Compose 進行部署。對於生產環境部署，請考慮調整 docker-compose.yml 文件中的配置。

The application is configured to be deployed using Docker Compose. For production deployment, consider adjusting the configuration in the docker-compose.yml file.

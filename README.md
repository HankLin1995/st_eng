# ST Engineering Inspection System

## Project Overview
This project consists of a backend API service built with Python and a frontend web application built with Streamlit. The system is designed for inspection management and data processing.

## Project Structure
- `backend_eng/`: Backend API service
- `frontend_eng/`: Frontend Streamlit application

## Prerequisites
- Docker and Docker Compose

## Getting Started

### Running the Application
To start all services:

```bash
docker-compose up --build -d
```

This will start:
1. Backend API service (accessible on port 8000)
2. Frontend Streamlit application (accessible on port 8501)
3. MySQL database (accessible on port 3306)

### Accessing the Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## Development

### Backend Development
The backend is located in the `backend_eng` directory. It uses a MySQL database for data storage.

### Frontend Development
The frontend is located in the `frontend_eng` directory. It's built with Streamlit and communicates with the backend API.

## Testing
Run backend tests with:
```bash
docker-compose run test
```

## Deployment
The application is configured to be deployed using Docker Compose. For production deployment, consider adjusting the configuration in the docker-compose.yml file.

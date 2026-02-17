@echo off
echo Starting RAG Application...

:: Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python.
    pause
    exit /b
)

:: Install requirements if needed
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found!
    pause
    exit /b
)

:: Start Backend in a new window
echo Starting Backend Server...
start "RAG Backend" cmd /k "uvicorn backend:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend to initialize (simple pause)
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

:: Start Frontend in a new window
echo Starting Streamlit Frontend...
start "RAG Frontend" cmd /k "streamlit run streamlit_app.py --server.port 8501"

echo.
echo Application started!
echo Frontend: http://localhost:8501
echo Backend:  http://localhost:8000/docs
echo.
pause

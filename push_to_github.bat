@echo off
echo Initializing Git Repository...
git init

echo Adding files...
git add .

echo Committing changes...
git commit -m "Initial commit: Complete RAG Chatbot with Signup, Upload, and Vercel config"

echo Setting up remote...
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin https://github.com/venkyp2552/rag-chatbot.git

echo.
echo ----------------------------------------------------------------
echo Pushing to GitHub...
echo If asked for credentials, please enter them in this window.
echo ----------------------------------------------------------------
echo.
git push -u origin main

echo.
if %errorlevel% neq 0 (
    echo.
    echo ❌ Push failed! 
    echo Please make sure you have access to the repository.
    echo You may need to sign in to GitHub if a prompt appeared.
) else (
    echo ✅ Successfully pushed to GitHub!
)
pause

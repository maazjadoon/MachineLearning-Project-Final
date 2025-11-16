@echo off
echo 🔧 Cyber Sentinel System Launcher
echo =====================================
echo.

echo 🚀 Starting Model Server...
start "Model Server" cmd /k "python model_server.py"

echo ⏳ Waiting for Model Server to start...
timeout /t 3 /nobreak >nul

echo 🌐 Starting Web Application (Fallback Mode)...
start "Web Application" cmd /k "python run_fallback.py"

echo.
echo 🎉 System started successfully!
echo =====================================
echo 📊 Dashboard: http://localhost:5000
echo 🔍 Real-time Detection: http://localhost:5000/detection
echo 📈 History: http://localhost:5000/history
echo.
echo 💡 Services running:
echo    ✅ Model Server (port 9999)
echo    ✅ Web Application (fallback mode)
echo.
echo ⚠️  Close this window to stop all services
echo =====================================

pause

@echo off
echo 🚀 Starting API Proxy Server...
echo.
echo 📍 Current directory: %CD%
echo 🔐 Credentials: Demodiemthu:123456
echo 🌐 Server will run on http://localhost:5000
echo.
echo 📋 Available endpoints:
echo   - GET /api/proxy/test - Test proxy
echo   - GET /api/proxy/health - Health check
echo   - GET /api/proxy/thuhohpk/{service_type} - Call external API
echo.
echo 💡 Usage in React app:
echo   - Nút "Lấy dữ liệu từ thuhohpk.com" sẽ tự động thử proxy
echo   - Proxy URL: http://localhost:5000/api/proxy/thuhohpk/{service_type}
echo.
echo ⚠️  Make sure you have installed dependencies:
echo    pip install -r requirements.txt
echo.
echo 🚀 Starting server...
python server_api_proxy.py
pause

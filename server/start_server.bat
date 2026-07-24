@echo off
chcp 65001 >nul
title 嘉行找人 - 测试服务器

echo ==============================
echo    嘉行找人 - 本地测试服务器
echo ==============================
echo.

REM 检查PHP是否可用
where php >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到PHP，请先安装PHP并添加到PATH
    echo 下载地址: https://windows.php.net/download/
    pause
    exit /b 1
)

REM 获取本机IP
echo 本机IP地址:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /r "IPv4.*[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*"') do (
    set "IP=%%a"
    goto :found_ip
)
:found_ip
set IP=%IP: =%
echo   局域网: %IP%
echo   本机:   127.0.0.1
echo.
echo 客户端服务器地址填: http://%IP%:8080
echo.

REM 创建data目录
if not exist "%~dp0data" mkdir "%~dp0data"

REM 询问是否加载mock数据
if exist "%~dp0data\app.db" (
    echo [提示] 数据库已存在，跳过mock数据
) else (
    echo 是否加载测试数据？(包含6个模拟用户+收藏+找人请求)
    set /p LOADMOCK="输入 Y 加载，回车跳过: "
    if /i "%LOADMOCK%"=="Y" (
        echo.
        php "%~dp0mock_data.php"
    )
)
echo.

REM 启动PHP内置服务器
echo ==============================
echo 启动中... 按 Ctrl+C 停止
echo ==============================
echo.
php -S 0.0.0.0:8080 -t "%~dp0"

pause

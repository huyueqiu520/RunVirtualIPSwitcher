@echo off
setlocal

REM 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在请求管理员权限...
    powershell -Command "Start-Process cmd -ArgumentList '/c', '%SCRIPT_DIR%VirtualIPSwitcher.py' -Verb RunAs"
    exit /b
)

REM 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 未找到Python，请确保已安装Python并添加到系统路径。
    pause
    exit /b 1
)

REM 运行Python脚本
echo 启动虚拟IP切换器...
python "%SCRIPT_DIR%VirtualIPSwitcher.py"

pause
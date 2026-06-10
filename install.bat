@echo off
chcp 65001 >nul
echo ========================================
echo 视频文案提取工具 v3.1 - 安装脚本
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [✓] Python 环境正常

echo.
echo [2/3] 安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [✓] 依赖安装完成

echo.
echo [3/3] 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 FFmpeg，请前往 https://ffmpeg.org/download.html 下载安装
    echo 未安装 FFmpeg 将无法提取音频
) else (
    echo [✓] FFmpeg 已安装
)

echo.
echo ========================================
echo 安装完成！
echo.
echo CLI 使用方式：
echo   python video_transcript_extractor.py "视频链接" --type url
echo   python video_transcript_extractor.py "D:\videos\my_video.mp4" --type file
echo.
echo 或使用快捷脚本：
echo   run.bat "视频链接"
echo ========================================
pause

@echo off
chcp 65001 >nul
echo ========================================
echo 视频文案提取工具 v3.1
echo ========================================
echo.

if "%~1"=="" (
    echo [错误] 请提供视频链接或文件路径
    echo.
    echo CLI 用法:
    echo   python video_transcript_extractor.py "视频链接" --type url
    echo   python video_transcript_extractor.py "D:\videos\my_video.mp4" --type file
    echo.
    echo 或使用快捷脚本:
    echo   run.bat "视频链接"
    echo   run.bat "D:\videos\my_video.mp4" --type file
    echo.
    pause
    exit /b 1
)

echo 正在处理：%~1
echo.

set PYTHONIOENCODING=utf-8
python video_transcript_extractor.py %*

if %errorlevel% neq 0 (
    echo.
    echo [错误] 处理失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 处理完成！
echo ========================================
pause

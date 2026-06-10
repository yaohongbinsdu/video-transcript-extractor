"""
测试使用 yt-dlp 获取抖音用户视频
"""
import subprocess
import json
import os
import sys

# 使用 yt-dlp 列出用户的所有视频
# yt-dlp 支持抖音用户的页面

output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# 方法1: 直接使用 yt-dlp 列出用户视频
cmd = [
    sys.executable, '-m', 'yt_dlp',
    '--flat-playlist',
    '--print', '%(id)s %(title)s',
    '--no-warnings',
    '--',
    'https://www.douyin.com/user/jinkeyan123',
]

print("运行 yt-dlp 获取视频列表...")
print(f"命令: {' '.join(cmd)}\n")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
except Exception as e:
    print(f"错误: {e}")

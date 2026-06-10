"""
批量获取抖音用户所有视频文案

此脚本通过抖音网页端 API 获取用户的视频列表，然后逐个下载并提取文案。

用法：
    python fetch_user_videos.py jinkeyan123            # 使用抖音用户名
    python fetch_user_videos.py MS4wLjABAAAAxxxxx      # 使用 sec_uid
    python fetch_user_videos.py <视频链接1> <视频链接2>  # 直接使用视频链接

注意：抖音的 API 需要浏览器 Cookie 才能正常工作。首次运行会提示获取 Cookie。
"""
import sys
import os
import json
import time
import requests
import re
import subprocess
from datetime import datetime
from pathlib import Path


# 抖音 Web 端请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def get_cookies_from_browser():
    """
    提示用户如何获取 Cookie
    """
    print("\n" + "="*60)
    print("抖音 API 需要浏览器 Cookie")
    print("="*60)
    print("\n请按以下步骤获取 Cookie：")
    print("1. 打开浏览器（Chrome/Edge）")
    print("2. 打开抖音网页版：https://www.douyin.com")
    print("3. 登录你的抖音账号")
    print("4. 按 F12 打开开发者工具")
    print("5. 切换到 'Network'（网络）标签")
    print("6. 刷新页面（F5）")
    print("7. 点击任意一个请求，切换到 'Headers'（标头）标签")
    print("8. 找到 'Request Headers' 中的 'Cookie' 字段")
    print("9. 复制整个 Cookie 值")
    print("10. 粘贴到下面的提示中")
    print("\n" + "="*60 + "\n")


def resolve_user_videos():
    """
    尝试多种方法获取用户视频列表
    返回 (user_info_dict, video_urls_list)
    """
    # 方法1: 直接检查命令行参数是否是视频链接
    # 方法2: 通过 API 获取用户视频
    
    print("此脚本需要抖音用户名来批量获取视频文案")
    print("但由于抖音 API 限制，当前版本暂时无法直接获取用户主页视频列表")
    print("\n建议的替代方案：")
    print("1. 如果有该用户的视频链接，可以直接运行:")
    print("   python video_transcript_extractor.py <视频链接> --type url")
    print("\n2. 或者先手动下载视频到本地，然后运行:")
    print("   python video_transcript_extractor.py <视频文件路径> --type file")
    print("\n3. 使用 yt-dlp 下载（需要更新到最新版本）:")
    print("   pip install -U yt-dlp")
    print("   yt-dlp --flat-playlist https://www.douyin.com/user/jinkeyan123")
    
    return None, []


def main():
    print("="*60)
    print("抖音用户视频文案批量提取工具")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n用法：")
        print("  python fetch_user_videos.py jinkeyan123     # 抖音用户名")
        print("  python fetch_user_videos.py MS4wLjAB...     # sec_uid")
        print("  python fetch_user_videos.py <链接1> <链接2>  # 直接使用视频链接")
        sys.exit(1)
    
    user_input = sys.argv[1]
    
    # 检查是否是视频链接
    if user_input.startswith(('http://', 'https://')) and any(x in user_input for x in ['video', 'reel']):
        # 直接处理单个视频链接
        print(f"检测到视频链接，使用 video_transcript_extractor.py 处理...")
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        cmd = [
            sys.executable, 'video_transcript_extractor.py',
            user_input, '--type', 'url', '--output', output_dir,
        ]
        subprocess.run(cmd)
        return
    
    # 处理用户名
    print(f"用户名: {user_input}")
    
    # 由于抖音 API 限制，提示用户
    resolve_user_videos()


if __name__ == '__main__':
    main()

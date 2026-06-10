"""
测试抖音 API 来获取用户信息
"""
import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    'Cookie': '',
}

# 尝试访问抖音搜索 API 来查找用户
# 或者尝试通过移动端 API

# 方法1：尝试通过抖音分享页面的 API
# 抖音分享链接格式: https://www.iesdouyin.com/share/user/jinkeyan123
share_url = 'https://www.iesdouyin.com/share/user/jinkeyan123'
try:
    resp = requests.get(share_url, headers=headers, timeout=15, allow_redirects=True)
    print(f"Share URL Status: {resp.status_code}")
    print(f"Final URL: {resp.url}")
    
    # 查找 sec_uid
    sec_uid_match = re.search(r'"sec_uid"\s*:\s*"([^"]+)"', resp.text)
    if sec_uid_match:
        print(f"Found sec_uid: {sec_uid_match.group(1)}")
    
    # 查找 user_id
    user_id_match = re.search(r'"user_id"\s*:\s*"([^"]+)"', resp.text)
    if user_id_match:
        print(f"Found user_id: {user_id_match.group(1)}")
    
    # 查找 unique_id
    unique_id_match = re.search(r'"unique_id"\s*:\s*"([^"]+)"', resp.text)
    if unique_id_match:
        print(f"Found unique_id: {unique_id_match.group(1)}")
        
    # 检查是否包含 video_list
    if 'video_list' in resp.text:
        print("Contains video_list")
        # 尝试解析 JSON
        json_match = re.search(r'"video_list"\s*:\s*(\[.*?\])', resp.text, re.DOTALL)
        if json_match:
            print(f"Video list length: {len(json_match.group(1))}")
            
except Exception as e:
    print(f"Error: {e}")

print("\n--- 尝试移动端 API ---")
# 方法2: 移动端 API
mobile_url = 'https://m.douyin.com/search/jinkeyan123?type=user'
try:
    resp = requests.get(mobile_url, headers=headers, timeout=15)
    print(f"Mobile API Status: {resp.status_code}")
    print(f"Content length: {len(resp.text)}")
except Exception as e:
    print(f"Error: {e}")

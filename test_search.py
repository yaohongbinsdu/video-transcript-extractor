"""
尝试通过抖音搜索 API 查找用户
"""
import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
    'X-Requested-With': 'fetch',
    'Accept': 'application/json, text/plain, */*',
}

# 尝试搜索用户
search_url = 'https://www.douyin.com/aweme/v1/web/discover/search/'
params = {
    'keyword': 'jinkeyan123',
    'search_channel': 'aweme_user_web',
    'search_source': 'normal_search',
    'query_correct': '1',
    'search_type': 'user',
    'detect_search_type': '1',
    'device_platform': 'webapp',
    'aid': '6383',
}

print("尝试搜索用户...")
try:
    resp = requests.get(search_url, params=params, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    else:
        print(f"Response: {resp.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")

# 尝试另一个 API 端点
print("\n--- 尝试另一个 API 端点 ---")
search_url2 = 'https://www.douyin.com/aweme/v1/web/search/item/'
params2 = {
    'keyword': 'jinkeyan123',
    'search_channel': 'aweme_user_web',
    'search_source': 'normal_search',
    'query_correct': '1',
    'search_type': 'user',
    'device_platform': 'webapp',
    'aid': '6383',
    'cookie_enabled': 'true',
}

try:
    resp = requests.get(search_url2, params=params2, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response length: {len(resp.text)}")
        # 查找 sec_uid
        sec_uid_match = re.search(r'"sec_uid"\s*:\s*"([^"]+)"', resp.text)
        if sec_uid_match:
            print(f"Found sec_uid: {sec_uid_match.group(1)}")
except Exception as e:
    print(f"Error: {e}")

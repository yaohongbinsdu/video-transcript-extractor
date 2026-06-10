import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
}

# 尝试通过搜索 API 或其他方式获取用户 sec_uid
# 抖音的 web API 可能需要特定的 cookie/token

# 先尝试访问用户主页，查看页面内容
url = 'https://www.douyin.com/user/jinkeyan123'
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

# 查找 sec_uid
sec_uid_match = re.search(r'"secUid":"([^"]+)"', resp.text)
if sec_uid_match:
    print(f"Found sec_uid: {sec_uid_match.group(1)}")
else:
    print("No sec_uid found in page")

# 查找 uniqueId
unique_id_match = re.search(r'"uniqueId":"([^"]+)"', resp.text)
if unique_id_match:
    print(f"Found uniqueId: {unique_id_match.group(1)}")

# 查看页面中是否包含 SSR_HOUDAO_RENUO_STATE 内容
ssr_match = re.search(r'<script id="SSR_HOUDAO_RENUO_STATE" type="text/json">(.*?)</script>', resp.text, re.DOTALL)
if ssr_match:
    try:
        data = json.loads(ssr_match.group(1))
        user_info = data.get('userInfo', {})
        user = user_info.get('user', {})
        print(f"User info: {json.dumps(user_info, ensure_ascii=False, indent=2)[:500]}")
    except:
        print("Failed to parse SSR state")

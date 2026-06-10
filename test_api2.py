"""
检查抖音分享页面的实际内容
"""
import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.douyin.com/',
}

share_url = 'https://www.iesdouyin.com/share/user/jinkeyan123'
resp = requests.get(share_url, headers=headers, timeout=15, allow_redirects=True)

# 保存原始内容到文件以便分析
with open('douyin_page.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)

print(f"Page length: {len(resp.text)}")
print(f"First 2000 chars:\n{resp.text[:2000]}")

# 查找所有 JSON 数据
json_matches = re.findall(r'window\._ROUTER_DATA\s*=\s*(\{.*?\});', resp.text, re.DOTALL)
if json_matches:
    print(f"\nFound {len(json_matches)} _ROUTER_DATA blocks")
    for i, match in enumerate(json_matches):
        print(f"Block {i} length: {len(match)}")
        print(f"Block {i} preview: {match[:500]}...")
else:
    print("\nNo _ROUTER_DATA found")

# 查找所有可能的用户信息
print("\n--- All potential user info patterns ---")
patterns = [
    (r'sec_uid', r'"sec_uid"\s*:\s*"([^"]+)"'),
    (r'unique_id', r'"unique_id"\s*:\s*"([^"]+)"'),
    (r'nickname', r'"nickname"\s*:\s*"([^"]+)"'),
    (r'user_id', r'"user_id"\s*:\s*(\d+)'),
    (r'secUid', r'"secUid"\s*:\s*"([^"]+)"'),
    (r'video_list', r'"video_list"\s*:\s*(\[[^\]]*\])'),
]

for name, pattern in patterns:
    matches = re.findall(pattern, resp.text)
    if matches:
        print(f"Found {name}: {matches[:3]}")

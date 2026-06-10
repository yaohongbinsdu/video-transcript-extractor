import requests
import re
import json


# 抖音链接
url = "https://v.douyin.com/2C_Y3IZld4E/"

# 第一步：获取重定向后的真实链接和视频 ID
session = requests.Session()
resp = session.get(url, allow_redirects=True)
video_id = re.search(r'video/(\d+)', resp.url).group(1)
print(f"视频 ID: {video_id}")

# 第二步：模拟移动端访问
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://www.douyin.com/'
}

resp = session.get(f'https://www.iesdouyin.com/share/video/{video_id}/', headers=headers)

# 第三步：提取页面中的 JSON 数据
match = re.search(r'window\._ROUTER_DATA\s*=\s*(\{.*?\});?<', resp.text)
if not match:
    print("提取失败，可能抖音接口变了")
    exit()
    
data = json.loads(match.group(1))
item = data['loaderData']['video_(id)/page']['videoInfoRes']['item_list'][0]

# 第四步：获取视频信息
author = item['author']['nickname']
title = item['desc']
video_uri = item['video']['play_addr']['uri']
video_url = f'https://www.douyin.com/aweme/v1/play/?video_id={video_uri}'

print(f"作者：{author}")
print(f"标题：{title}")
print(f"正在下载...")

# 第五步：下载视频
video = session.get(video_url, headers=headers, verify=False)
filename = f"{author}_{title[:30]}.mp4".replace('/', '_').replace('\\', '_')

with open(filename, 'wb') as f:
    f.write(video.content)

print(f"下载完成！保存为：{filename}")
print(f"文件大小：{len(video.content) / 1024 / 1024:.2f} MB")

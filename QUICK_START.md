# 快速开始 - 视频文案提取工具 v3.4

> 支持视频链接/本地文件双输入源，输出带时间戳简体中文优化文案
> **基于 Whisper ASR 引擎（GitHub openai/whisper），支持精确时间戳提取**
> **自动繁体转简体，只输出单个 raw.txt 文件**

## 🚀 一键安装

双击运行 `install.bat` 即可完成安装。

**安装内容：**
- yt-dlp：视频下载
- openai-whisper：语音识别
- opencc-python-reimplemented：繁体转简体
- requests：HTTP 请求

## 💻 使用方法

### 方式 1：使用 CLI 脚本（推荐）

**提取视频链接：**
```bash
run.bat "https://v.douyin.com/xxx/"
```

**提取本地文件：**
```bash
run.bat "D:\videos\my_video.mp4" --type file
```

### 方式 2：使用 Python 命令

**提取视频链接：**
```bash
python video_transcript_extractor.py "https://v.douyin.com/xxx/" --type url
```

**提取本地文件：**
```bash
python video_transcript_extractor.py "D:\videos\my_video.mp4" --type file
```

**指定模型：**
```bash
# 使用 Whisper base 模型（默认）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
  --whisper-model base

# 使用 Whisper small 模型（更高准确率）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
  --whisper-model small

# 强制使用 SenseVoice（备选）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
  --asr-engine sensevoice

# 强制使用 Sherpa-ONNX（轻量级）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
  --asr-engine sherpa
```

## 📋 输出说明

提取完成后，会在 `output/时间戳/` 目录下生成**单个文件**：

**raw.txt** - 带时间戳的简体中文文案

示例：
```
# 视频文案（带时间戳 + 简体中文）

视频 ID: 694a5ba3000000000d00f4d0
标题：第 03 集 跟你聊聊，所谓秘诀
时长：135.25 秒
提取时间：2026-05-02 20:18:48

==================================================

[001] [00:00.000 -> 00:04.600] 一个刚注册十天的新号，才发了两条视频
[002] [00:05.120 -> 00:05.880] 谢谢你们
[003] [00:11.000 -> 00:14.080] 有很多人私信我，让我说说做短视频的秘诀
...
```

**v3.4 变化：**
- ❌ 删除 transcript.txt（优化文案）
- ✅ 只输出 raw.txt 文件
- ✅ 自动清理临时文件（视频、音频）
- ✅ 输出目录更简洁

## ⚠️ 注意事项

1. **FFmpeg 必须安装**：用于音频提取
   - Windows 下载：https://ffmpeg.org/download.html
   - 安装后确保 `ffmpeg` 命令可用

2. **Whisper 首次使用**：会自动下载模型（base 模型约 150MB）
   - 请确保网络连接正常
   - 模型下载后会自动缓存，后续无需重复下载

3. **性能说明**：
   - CPU 模式：base 模型约 1-2 分钟/视频
   - GPU 模式：速度提升 3-5 倍

4. **网络要求**：
   - 下载视频需要稳定网络
   - Whisper 识别完全离线，无需联网

5. **模型选择**：
   - **tiny**：最快，准确率较低（适合快速测试）
   - **base**：平衡速度和准确率（**推荐**）
   - **small**：准确率更高，速度较慢
   - **medium/large**：最高准确率，速度慢（适合高精度需求）

6. **简繁转换**：
   - 自动将繁体中文转换为简体中文
   - 使用 OpenCC 库
   - 无需额外配置

7. **版权说明**：仅供学习研究使用

8. **输出文件**：v3.4 版本开始，只输出 raw.txt 文件，自动删除视频/音频临时文件

## 🐛 故障排查

### FFmpeg 未找到
```bash
ffmpeg -version  # 检查是否安装
```

### Whisper 未安装
```bash
# 检查是否已安装
pip show openai-whisper

# 重新安装
pip install openai-whisper
```

### OpenCC 未安装（简繁转换失败）
```bash
# 检查是否已安装
pip show opencc-python-reimplemented

# 重新安装
pip install opencc-python-reimplemented
```

### 视频下载失败
```bash
# 更新 yt-dlp
pip install -U yt-dlp
```

### 模型下载失败
```bash
# 检查网络连接
# 首次使用需要下载模型，约 150MB（base 模型）
# 模型会自动缓存到 ~/.cache/whisper
```

## 📚 支持的平台

- ✅ 抖音、小红书、B 站、YouTube、TikTok
- ✅ 微博、爱奇艺、优酷、腾讯视频
- ✅ Facebook、Instagram、Twitter/X
- ✅ Pinterest、Vimeo、Dailymotion
- ✅ 1000+ 其他网站（通过 yt-dlp）
- ✅ 本地视频文件（MP4、MOV、AVI、MKV 等）

完整平台列表：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## 💡 使用场景

- **自媒体运营**：快速提取视频文案，进行二次创作
- **学习笔记**：从教学视频中提取知识点（带时间戳方便定位）
- **字幕制作**：获取视频字幕初稿（带精确时间戳）
- **内容分析**：分析竞品视频内容
- **知识管理**：将视频内容转为文字存档
- **视频剪辑**：根据时间戳快速定位片段
- **跨境内容**：自动将港澳台视频文案转换为简体中文

---

**版本：v3.4**  
**更新日期：2026-05-05**  
**主要更新**：新增繁体转简体、只输出单个文件、自动清理临时文件

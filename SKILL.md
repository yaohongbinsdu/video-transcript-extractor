---
name: "video-transcript-extractor"
description: "视频文案提取工具 v3.5 - 支持视频链接/本地文件双输入源，输出带时间戳简体中文优化文案。集成 yt-dlp 视频下载（1000+ 网站）、FFmpeg 音频提取、Whisper ASR 引擎（GitHub openai/whisper，带时间戳）、文案清理引擎（逐句优化，修正错别字，繁体转简体）。自动检测并下载 Whisper 模型。Invoke when user needs to extract transcript/text from videos with timestamps."
---

# 视频文案提取工具 v3.5

> 支持视频链接/本地文件双输入源，输出带时间戳简体中文优化文案
> **基于 Whisper ASR 引擎（GitHub openai/whisper），支持精确时间戳提取**
> **逐句优化逻辑：保留时间戳和分段结构，修正每句错别字，自动繁体转简体**
> **支持先用 chrome-devtools-mcp 访问浏览器，获取不同平台的视频链接后再提取文案**

## ✨ 核心能力

| 组件 | 技术 | 说明 |
|------|------|------|
| **视频下载** | yt-dlp | 多平台支持（1000+ 网站），自动去水印，**不依赖其他工具** |
| **浏览器取链** | chrome-devtools-mcp | 从用户当前浏览器页面获取不同平台的视频页面链接、短链跳转后的最终 URL |
| **音频提取** | FFmpeg | 高质量音频提取，16kHz 采样率 |
| **语音识别** | Whisper（GitHub openai/whisper） | 本地识别，**支持时间戳**，准确率高 |
| **文案清理** | 逐句优化引擎 | **保留时间戳和分段，修正每句错别字，繁体转简体** |
| **输出格式** | raw.txt（带时间戳 + 简体中文） | **简体中文、带时间戳的可读文案** |

### 重要说明

**视频下载方式：**
- ✅ **默认使用 yt-dlp**，不依赖任何其他工具
- ✅ **不调用 social-media-assistant** 或其他技能
- ✅ **不使用浏览器 Cookie**，避免隐私泄露
- ✅ 自动重试机制，提高下载成功率

**ASR 引擎说明（Whisper）：**
- 来源：GitHub https://github.com/openai/whisper
- 安装：`pip install openai-whisper`
- 模型选项：tiny / base / small / medium / large
- 默认模型：**base**（平衡速度和准确率）
- 优势：
  - ✅ 识别准确率高
  - ✅ **支持精确时间戳**（精确到毫秒）
  - ✅ 支持多语言（中文优化）
  - ✅ 自动断句分段
  - ✅ 完全本地运行，无需 API Key

**降级机制：**
- 优先使用 Whisper（GitHub）
- Whisper 失败时降级到 SenseVoice（FunASR）
- 再失败降级到 Sherpa-ONNX（轻量级备选）

**简繁转换：**
- 使用 OpenCC 库自动将繁体中文转换为简体中文
- 安装：`pip install opencc-python-reimplemented`
- 转换时机：语音识别后自动转换
- 输出格式：简体中文文案

## 🎯 支持的平台

### 主流平台
- ✅ 抖音（支持去水印）
- ✅ 小红书
- ✅ B 站
- ✅ YouTube
- ✅ TikTok
- ✅ 微博、爱奇艺、优酷、腾讯视频
- ✅ Facebook、Instagram、Twitter/X
- ✅ Pinterest、Vimeo、Dailymotion
- ✅ Twitch、Reddit、Snapchat
- ✅ AcFun、西瓜视频
- ✅ 本地视频文件（MP4、MOV、AVI、MKV 等）

### 更多平台
yt-dlp 支持 **1000+** 个网站，完整列表：
https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## 🌐 先从浏览器获取视频链接（chrome-devtools-mcp）

适用场景：用户只说“浏览器里这个视频”或只打开了页面，但没有把视频链接直接发给你。

**推荐流程：**
1. 使用 `chrome-devtools-mcp` 访问用户当前浏览器标签页
2. 读取当前页面 URL；如果是短链或分享页，等待跳转后获取最终 URL
3. 如当前页面 URL 不足以定位视频，再检查页面中的 `<video>` 元素、播放器链接或媒体请求
4. 将拿到的公开视频链接传给 `video_transcript_extractor.py`，再走正常下载与转写流程

**平台处理建议：**
- 抖音 / TikTok：优先使用详情页或跳转后的最终分享链接
- 小红书：优先使用笔记详情页链接，不直接依赖页面临时媒体地址
- B 站 / YouTube：优先使用标准视频页面 URL
- 其他平台：优先使用可公开访问的落地页 URL，其次才是页面内媒体直链

**注意：**
- 优先记录“可复用的视频页面链接”，而不是短时有效的临时资源地址
- 如果页面需要登录、地区限制或额外授权，应先向用户说明限制
- 获取到链接后，仍由 `yt-dlp` 负责实际下载与兼容性处理

## 🚀 快速使用

### 1. 先从浏览器取链接（适用于未直接提供 URL）

- 用户已在浏览器打开视频页时，先用 `chrome-devtools-mcp` 获取当前页面 URL 或最终跳转链接
- 拿到链接后，再按下面的“从视频链接提取文案”方式执行

### 2. 从视频链接提取文案（推荐）

```bash
# 抖音视频
python video_transcript_extractor.py "https://v.douyin.com/xxx/" --type url

# 小红书视频
python video_transcript_extractor.py "https://www.xiaohongshu.com/explore/xxx" --type url

# B 站视频
python video_transcript_extractor.py "https://www.bilibili.com/video/BV1xx411c7mD" --type url

# YouTube 视频
python video_transcript_extractor.py "https://www.youtube.com/watch?v=xxx" --type url
```

### 3. 从本地文件提取文案

```bash
# 本地视频文件
python video_transcript_extractor.py "D:\videos\my_video.mp4" --type file
```

### 4. 指定输出目录和模型

```bash
# 使用 Whisper base 模型（默认）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
  --output "D:\output" \
  --asr-engine auto \
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

### 文件 1：原始文案（raw.txt）
- **带时间戳的简体中文记录**
- 格式：`[序号] [开始时间 -> 结束时间] 文本内容`
- 示例：`[001] [00:00.000 -> 00:04.600] 一个刚注册十天的新号`
- 包含视频元数据（ID、标题、时长、提取时间）
- 适合字幕制作、时间定位、二次编辑
- **自动繁体转简体**：所有繁体中文自动转换为简体中文

### 文件 2：优化文案（transcript.txt）
- **大模型语义优化后的可读文案（已移除，只保留 raw.txt）**
- v3.4 版本开始，**只输出 raw.txt 文件**，删除 transcript.txt
- 原因：raw.txt 已经包含时间戳和简体中文优化，满足大部分需求

## 🔧 前置依赖

### 1. Python 依赖

```bash
pip install -r requirements.txt
```

**requirements.txt 包含：**
- `openai-whisper`: Whisper ASR 引擎（GitHub openai/whisper）
- `yt-dlp`: 视频下载
- `requests`: HTTP 请求
- `opencc-python-reimplemented`: 繁体转简体中文

### 2. 系统工具

**FFmpeg（必须）：**
- Windows: https://ffmpeg.org/download.html
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### 3. 可选依赖（备选 ASR 引擎）

**FunASR（用于 SenseVoice 降级）：**
```bash
pip install funasr torch torchaudio modelscope
```

**Sherpa-ONNX（轻量级备选）：**
```bash
pip install sherpa-onnx numpy
```

## 💡 使用场景

1. **自媒体运营**：快速提取视频文案，进行二次创作
2. **学习笔记**：从教学视频中提取知识点（带时间戳方便定位）
3. **字幕制作**：获取视频字幕初稿（带精确时间戳）
4. **内容分析**：分析竞品视频内容
5. **知识管理**：将视频内容转为文字存档
6. **视频剪辑**：根据时间戳快速定位片段

## ⚙️ 文案清理引擎功能

### 逐句优化流程（v3.4 核心逻辑）

**处理流程：**
```
Whisper ASR 识别 → 保留时间戳和分段 → 逐句修正错别字 → 繁体转简体 → 输出可读文案
```

**核心特点：**
- ✅ **保留时间戳**：每句都有精确的时间戳（毫秒级）
- ✅ **保留分段结构**：不重新断句，保持原始分段
- ✅ **逐句优化**：对每一句单独进行错别字修正
- ✅ **语句通顺**：修正后的句子可直接阅读
- ✅ **繁体转简体**：自动将繁体中文转换为简体中文

### 错别字修正逻辑

**修正方法：**
1. **常见错别字映射表**：基于上下文理解的错误映射
2. **逐句匹配替换**：对每一句的文本进行匹配和替换
3. **补全漏字**：基于语法补全"的"、"地"、"得"等
4. **移除重复**：消除无意义的重复词语

**常见错别字修正示例：**

| 原始识别 | 修正后 | 说明 |
|---------|--------|------|
| 住车 | 注册 | 同音字错误 |
| 信号 | 新号 | 同音字错误 |
| 比青年总 | 鼻青脸肿 | 成语识别错误 |
| 高极各地部 | 高级个体 IP | 专业术语错误 |
| 哨而 | 少儿 | 同音字错误 |
| 承认 | 成人 | 同音字错误 |
| 全往 | 全网 | 同音字错误 |
| 自自清晰 | 定位清晰 | 语义理解错误 |
| 没有生活 | 美好生活 | 语义理解错误 |
| 油力吸吸 | 油腻腻 | 形容词错误 |
| 前置色降头 | 前置摄像头 | 专业术语错误 |
| 送单单 | 宋丹丹 | 人名错误 |
| 七个夜 | 七个亿 | 数量词错误 |
| 架效 | 驾校 | 机构名称错误 |
| 巨勒步 | 俱乐部 | 组织名称错误 |
| 之前的高几个体育 | 值钱的高级个体 | 语义完全错误 |
| 人色 | 人设 | 同音字错误 |
| 求都 | 都 | 漏字 |
| 编借 | 边界 | 同音字错误 |
| 表达形势 | 表达形式 | 同音字错误 |
| 较成 | 教程 | 同音字错误 |
| 考作文 | 靠作文 | 同音字错误 |
| 来用 | 哪有 | 语义错误 |
| 你们 | 你面前 | 语义补全 |
| 滚的远 | 滚得远 | "的/得"修正 |

### 输出格式说明

**raw.txt 文件格式：**
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
[004] [00:14.340 -> 00:16.380] 想知道我是怎么做一个成一个的
[005] [00:16.640 -> 00:18.680] 我看大家做视频做得鼻青脸肿
...
```

**输出特点：**
- ✅ 带精确时间戳（毫秒级）
- ✅ 已修正所有错别字
- ✅ 保留原始分段结构
- ✅ 语句通顺，可直接阅读
- ✅ 不重新断句，保持原貌
- ✅ **自动繁体转简体**：所有繁体中文自动转换为简体中文

3. **优化断句**
   - 基于语义理解重新断句
   - 添加恰当的标点符号
   - 消除歧义，确保通顺

4. **消除重复**
   - 移除无意义的重复词语
   - 优化语义连贯性

### 处理流程

```
原始 ASR 文本 → 大模型理解 → 语义分析 → 错字修正 → 断句优化 → 输出可读文案
```

## 📊 输出示例

### raw.txt（带时间戳 + 简体中文）

```
# 视频文案（带时间戳 + 简体中文）

视频 ID: 694a5ba3000000000d00f4d0
标题：第 03 集 跟你聊聊，所谓秘诀
时长：135.25 秒
提取时间：2026-05-02 18:09:03

==================================================

[001] [00:00.000 -> 00:04.600] 一个刚注册十天的新号，才发了两条视频
[002] [00:05.120 -> 00:05.880] 谢谢你们
[003] [00:11.000 -> 00:14.080] 有很多人私信我，让我说说做短视频的秘诀
[004] [00:14.340 -> 00:16.380] 想知道我是怎么做一个成一个的
[005] [00:16.640 -> 00:18.680] 我看大家做视频做得鼻青脸肿
...
```

**说明：**
- v3.4 版本开始，**只输出 raw.txt 文件**
- 删除 transcript.txt，避免文件冗余
- 自动清理临时文件（视频、音频）

## ⚠️ 注意事项

1. **FFmpeg 必须安装**：用于音频提取
2. **Whisper 首次使用**：会自动下载模型（base 模型约 150MB）
3. **性能说明**：
   - CPU 模式：base 模型约 1-2 分钟/视频
   - GPU 模式：速度提升 3-5 倍
4. **网络要求**：下载视频需要稳定网络，Whisper 识别完全离线
5. **模型选择**：
   - tiny：最快，准确率较低（适合快速测试）
   - base：平衡速度和准确率（**推荐**）
   - small：准确率更高，速度较慢
   - medium/large：最高准确率，速度慢（适合高精度需求）
6. **版权说明**：仅供学习研究使用
7. **输出文件**：v3.4 版本开始，只输出 raw.txt 文件，自动删除视频/音频临时文件

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

## 📚 技术架构

```
video_transcript_extractor.py
├── VideoDownloader (yt-dlp)     # 下载视频（1000+ 平台）
├── AudioExtractor (FFmpeg)      # 提取音频（16kHz）
├── WhisperLocal (openai-whisper) # 语音识别 + 时间戳
├── TextCleaner                  # 语义优化、纠错、补漏、繁体转简体
│   ├── convert_to_simplified()  # 繁体转简体（OpenCC）
│   ├── clean()                  # 基础清理
│   ├── add_punctuation()        # 智能标点
│   └── optimize_with_llm()      # LLM 优化
└── TranscriptGenerator          # 生成单文件输出（raw.txt）
```

## 🔄 版本更新

### v3.5（当前版本）
- ✅ **新增 chrome-devtools-mcp 浏览器取链流程**：可从用户当前浏览器页面获取不同平台的视频链接
- ✅ **支持短链/分享页处理说明**：先取跳转后的最终 URL，再交给 yt-dlp 下载
- ✅ **补充跨平台取链策略**：优先使用可复用的视频页面链接，避免依赖临时媒体地址

### v3.4
- ✅ **新增繁体转简体功能**：使用 OpenCC 自动转换繁体中文为简体中文
- ✅ **只输出单个文件**：删除 transcript.txt，只保留 raw.txt
- ✅ **自动清理临时文件**：输出目录只保留 raw.txt，删除视频/音频文件
- ✅ **优化输出格式**：raw.txt 标题改为"带时间戳 + 简体中文"
- ✅ **更新依赖**：添加 opencc-python-reimplemented

### v3.3
- ✅ 固定逐句优化逻辑
- ✅ 保留时间戳和分段结构
- ✅ 逐句修正错别字，不重新断句
- ✅ 优化映射表，覆盖 25+ 种常见错误
- ✅ 输出格式：`# 视频文案（带时间戳 + 已优化）`

### v3.2
- ✅ 新增大模型语义优化逻辑
- ✅ 基于上下文理解修正错别字（如"住车"→"注册"、"比青年总"→"鼻青脸肿"）
- ✅ 补全漏字和标点（如"做得"→"做得鼻青脸肿"）
- ✅ 优化断句，使语句通顺
- ✅ 消除歧义，提升可读性
- ✅ 输出带时间戳的优化文案，可直接阅读

### v3.1
- ✅ 新增 Whisper 模型自动检测功能
- ✅ 模型存在时直接加载，不存在自动下载
- ✅ 显示模型下载路径和进度提示
- ✅ 优化模型管理体验

### v3.0
- ✅ 使用 GitHub openai/whisper 替代 FunASR
- ✅ 支持精确时间戳提取（毫秒级）
- ✅ 大模型语义优化（纠错、补漏、断句）
- ✅ 双格式输出：raw.txt（带时间戳）+ transcript.txt（优化后）
- ✅ 自动降级机制：Whisper → SenseVoice → Sherpa-ONNX

### v2.1
- FunASR/Sherpa-ONNX 双引擎
- 离线识别，无需 API Key
- 自动降级机制

### v2.0
- 文案清理引擎升级
- 大模型理解优化接口
- 自动删除临时文件

## 📄 许可证

本项目仅供学习研究使用。

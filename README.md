# 视频文案提取工具 v3.4

> 支持视频链接/本地文件双输入源，输出带时间戳简体中文优化文案
> **基于 Whisper ASR 引擎（GitHub openai/whisper），支持精确时间戳提取**
> **逐句优化逻辑：保留时间戳和分段，修正每句错别字，自动繁体转简体**

## ✨ 核心功能

### 1️⃣ 双输入源支持
- **视频链接**：支持抖音、小红书、B 站、YouTube、TikTok 等 1000+ 网站
- **本地文件**：支持 MP4、MOV、AVI、MKV 等常见视频格式

### 2️⃣ 核心技术栈
| 组件 | 技术 | 说明 |
|------|------|------|
| **视频下载** | yt-dlp | 多平台支持（1000+ 网站），自动去水印 |
| **音频提取** | FFmpeg | 高质量音频提取，16kHz 采样率 |
| **语音识别** | Whisper（GitHub openai/whisper） | 本地识别，**支持时间戳**，准确率高 |
| **文案清理** | 大模型语义优化 + OpenCC | 修正错别字、补全漏字、优化断句、**繁体转简体** |

**ASR 引擎选择：**
- **Whisper（推荐）**：GitHub openai/whisper，识别准确率高，**支持精确时间戳**
- **SenseVoice（备选）**：FunASR 加载，中文优化
- **Sherpa-ONNX（轻量级）**：不依赖 torch，适合环境受限场景
- **自动降级**：Whisper → SenseVoice → Sherpa-ONNX

**简繁转换：**
- **OpenCC**：自动将繁体中文转换为简体中文
- **转换时机**：语音识别后自动转换
- **输出格式**：简体中文文案

### 3️⃣ 单文件输出（v3.4 新特性）

#### 文件 1：原始文案（raw.txt）
- **带时间戳的简体中文记录**
- 格式：`[序号] [开始时间 -> 结束时间] 文本内容`
- 示例：`[001] [00:00.000 -> 00:04.600] 一个刚注册十天的新号`
- 包含视频元数据（ID、标题、时长、提取时间）
- 适合字幕制作、时间定位、二次编辑
- **自动繁体转简体**：所有繁体中文自动转换为简体中文

**v3.4 变化：**
- ❌ 删除 transcript.txt（优化文案）
- ✅ 只输出 raw.txt 文件
- ✅ 自动清理临时文件（视频、音频）
- ✅ 输出目录更简洁

## 🔧 前置依赖

### 1. Python 依赖

```bash
pip install -r requirements.txt
```

**依赖说明：**
- `yt-dlp`: 视频下载（支持 1000+ 网站）
- `requests`: HTTP 请求
- `openai-whisper`: Whisper ASR 引擎
- `opencc-python-reimplemented`: 繁体转简体中文

### 2. 系统工具

**FFmpeg（必须）：**
- Windows: https://ffmpeg.org/download.html
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### 3. ASR 引擎依赖

**方案 1：Whisper（推荐）**

Whisper 需要以下 Python 包（已包含在 requirements.txt 中）：
- `openai-whisper`: OpenAI Whisper 本地识别
- `torch`: PyTorch（CPU 版本）
- `torchaudio`: PyTorch 音频处理

**首次使用**：会自动下载模型（base 模型约 150MB），模型下载后会自动缓存

**方案 2：Sherpa-ONNX（备选）**

当环境限制无法安装 torch 时使用：
- `sherpa-onnx`: 轻量级 ASR 引擎
- `numpy`: 数值计算库

**优势**：
- 不依赖 torch，安装包小
- 启动速度快
- 适合环境受限场景

### 4. 使用示例

#### 方式 1：从视频链接提取

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

#### 方式 2：从本地文件提取

```bash
# 本地视频文件
python video_transcript_extractor.py "D:\videos\my_video.mp4" --type file
```

#### 方式 3：指定参数

```bash
# 使用 Whisper base 模型（默认）
python video_transcript_extractor.py "https://v.douyin.com/xxx/" \
  --type url \
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

## 📋 输出示例

### raw.txt（带时间戳 + 简体中文）

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

## 💡 使用场景

1. **自媒体运营**：快速提取视频文案，进行二次创作
2. **学习笔记**：从教学视频中提取知识点（带时间戳方便定位）
3. **字幕制作**：获取视频字幕初稿（带精确时间戳）
4. **内容分析**：分析竞品视频内容
5. **知识管理**：将视频内容转为文字存档
6. **视频剪辑**：根据时间戳快速定位片段
7. **跨境内容**：自动将港澳台视频文案转换为简体中文

## ⚙️ 文案清理引擎功能

### 处理流程（v3.4）

```
Whisper ASR 识别 → 保留时间戳和分段 → 逐句修正错别字 → 繁体转简体 → 输出简体中文文案
```

### 核心特点
- ✅ **保留时间戳**：每句都有精确的时间戳（毫秒级）
- ✅ **保留分段结构**：不重新断句，保持原始分段
- ✅ **逐句优化**：对每一句单独进行错别字修正
- ✅ **语句通顺**：修正后的句子可直接阅读
- ✅ **繁体转简体**：自动将繁体中文转换为简体中文

### 简繁转换示例

| 原始识别（繁体） | 转换后（简体） |
|-----------------|---------------|
| 同樣的一個花生交給不同的兩個博主賣 | 同样的一个花生交给不同的两个博主卖 |
| 卻賣出了兩種截然不同的結果 | 却卖出了两种截然不同的结果 |
| 在籃球裡這一招很好用 | 在篮球里这一招很好用 |
| 博文 A 說這個花生可逆保買香脆美味 | 博主 A 说这个花生可逆保买香脆美味 |

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

### v3.4（当前版本）
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

## 📄 许可证

本项目仅供学习研究使用。

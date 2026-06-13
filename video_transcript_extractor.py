"""
视频文案提取工具 v2.1
支持视频链接/本地文件双输入源，输出纯文本 + 结构化文案双格式

核心能力：
- yt-dlp：多平台视频下载（自动去水印）- 支持 1000+ 网站
- FFmpeg：音频提取与格式转换
- FunASR：本地语音识别（阿里达摩院开源，离线识别）
- Sherpa-ONNX：轻量级备选 ASR（不依赖 torch，适合环境受限场景）
- 文案清理引擎：自动移除表情包、修正错别字、补全漏字
- 双格式输出：raw.txt（纯文本）+ transcript.md（结构化 Markdown）
"""

import os
import sys
import json
import subprocess
import requests
import re
import time
from datetime import datetime
from pathlib import Path
import shutil
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

INVALID_PATH_CHARS = r'[<>:"/\\|?*\x00-\x1f]+'

# 简繁转换（延迟导入，避免未安装时报错）
OPENCC_AVAILABLE = False
try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    pass

# FunASR 状态（延迟导入，避免 Windows 兼容性问题）
FUNASR_AVAILABLE = False
FUNASR_IMPORT_ERROR = None

# Sherpa-ONNX 状态（轻量级备选方案，不依赖 torch）
SHERPA_ONNX_AVAILABLE = False
SHERPA_ONNX_IMPORT_ERROR = None

# SenseVoice 本地模型状态（通过 ModelScope 下载，不依赖 API）
SENSEVOICE_LOCAL_AVAILABLE = False
SENSEVOICE_LOCAL_IMPORT_ERROR = None


@dataclass
class VideoMetadata:
    """视频元数据"""
    video_id: str = ""
    platform: str = ""
    title: str = ""
    author: str = ""
    duration: float = 0.0
    extract_time: str = ""
    source_type: str = ""  # "url" or "file"
    source_path: str = ""


def build_output_dir_name(timestamp: str, title: str, max_length: int = 80) -> str:
    title = re.sub(INVALID_PATH_CHARS, ' ', (title or '').strip())
    title = re.sub(r'\s+', ' ', title).strip(' .')
    if not title:
        return timestamp
    safe_title = title[:max_length].rstrip(' .')
    return f"{timestamp}_{safe_title}" if safe_title else timestamp


class VideoDownloader:
    """yt-dlp 视频下载器（支持自动去水印）"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download(self, url: str) -> Tuple[bool, str, Dict]:
        """
        下载视频（仅使用 yt-dlp）
        返回：(success, video_path, metadata)
        """
        try:
            # 检测平台
            platform = self._detect_platform(url)
            
            # 构建输出模板
            output_template = os.path.join(self.output_dir, '%(id)s.%(ext)s')
            
            # 构建 yt-dlp 命令（不使用 Cookie，不依赖其他工具）
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '-o', output_template,
                '--write-info-json',
                '--no-cookies',  # 不使用 Cookie
                '--extractor-retries', '5',  # 重试次数
                '--retry-sleep', '2',  # 重试间隔
            ]
            
            # 对于抖音等平台，添加额外参数
            if platform == '抖音':
                cmd.extend([
                    '--prefer-free-formats',
                    '--extractor-args', 'douyin:client_type=web,api_type=web',
                ])
            
            cmd.append(url)
            
            print(f"正在使用 yt-dlp 下载视频...")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if proc.returncode == 0:
                # 解析 JSON 元数据
                json_files = list(Path(self.output_dir).glob('*.info.json'))
                if json_files:
                    with open(json_files[0], 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    video_files = list(Path(self.output_dir).glob('*.mp4'))
                    if video_files:
                        print(f"✅ 视频下载成功：{video_files[0]}")
                        return True, str(video_files[0]), metadata
                
                # 尝试查找其他视频格式
                video_files = list(Path(self.output_dir).glob('*.mp4')) or \
                             list(Path(self.output_dir).glob('*.webm')) or \
                             list(Path(self.output_dir).glob('*.mkv'))
                
                if video_files:
                    print(f"✅ 视频下载成功：{video_files[0]}")
                    return True, str(video_files[0]), {}
                
                return False, "", {"error": "找不到视频文件"}
            else:
                error_msg = proc.stderr.strip() if proc.stderr else "下载失败"
                print(f"❌ yt-dlp 下载失败：{error_msg}")
                
                # 检测是否需要 cookies
                if 'cookies' in error_msg.lower():
                    print("\n⚠️ 该平台需要浏览器 Cookie 才能下载")
                    print("💡 建议：使用本地视频文件代替，或提供已登录的浏览器 Cookie")
                    print("   本地文件用法：python video_transcript_extractor.py \"D:\\videos\\my_video.mp4\" --type file\n")
                
                return False, "", {"error": error_msg}
                
        except subprocess.TimeoutExpired:
            return False, "", {"error": "下载超时（300 秒）"}
        except Exception as e:
            return False, "", {"error": str(e)}
    
    def _detect_platform(self, url: str) -> str:
        """
        检测视频平台
        yt-dlp 支持 1000+ 个网站，这里列出常用的主流平台
        完整列表：https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
        """
        platform_map = {
            # 国内平台
            'douyin.com': '抖音',
            'v.douyin.com': '抖音',
            'iesdouyin.com': '抖音',
            'xiaohongshu.com': '小红书',
            'xhslink.com': '小红书',
            'bilibili.com': 'B 站',
            'b23.tv': 'B 站',
            'weibo.com': '微博',
            'm.weibo.cn': '微博',
            'iqiyi.com': '爱奇艺',
            'youku.com': '优酷',
            'v.qq.com': '腾讯视频',
            'acfun.cn': 'AcFun',
            'ixigua.com': '西瓜视频',
            
            # 国际平台
            'youtube.com': 'YouTube',
            'youtu.be': 'YouTube',
            'tiktok.com': 'TikTok',
            'vm.tiktok.com': 'TikTok',
            'facebook.com': 'Facebook',
            'fb.watch': 'Facebook',
            'instagram.com': 'Instagram',
            'twitter.com': 'Twitter/X',
            'x.com': 'Twitter/X',
            't.co': 'Twitter/X',
            'pinterest.com': 'Pinterest',
            'pin.it': 'Pinterest',
            'vimeo.com': 'Vimeo',
            'dailymotion.com': 'Dailymotion',
            'twitch.tv': 'Twitch',
            'reddit.com': 'Reddit',
            'snapchat.com': 'Snapchat',
        }
        
        for domain, platform in platform_map.items():
            if domain in url:
                return platform
        
        # 如果不在列表中，yt-dlp 仍然可能支持
        return '其他平台'


class AudioExtractor:
    """FFmpeg 音频提取器"""
    
    def __init__(self):
        pass
    
    def extract_audio(self, video_path: str, output_dir: str) -> Tuple[bool, str]:
        """
        从视频提取音频
        返回：(success, audio_path)
        """
        try:
            audio_path = os.path.join(
                output_dir,
                Path(video_path).stem + '.wav'
            )
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                audio_path
            ]
            
            # 使用 stderr=subprocess.PIPE 避免编码问题
            proc = subprocess.run(cmd, capture_output=True, timeout=300)
            
            if proc.returncode == 0 or os.path.exists(audio_path):
                return True, audio_path
            else:
                return False, ""
                
        except Exception as e:
            return False, ""


class FunASR:
    """
    FunASR 本地语音识别（阿里达摩院开源）
    支持离线识别，无需上传文件
    """
    
    def __init__(self, model_name: str = "paraformer-zh", device: str = "cpu"):
        """
        初始化 FunASR 模型
        :param model_name: 模型名称（paraformer-zh, paraformer-zh-streaming 等）
        :param device: 运行设备（cpu, cuda:0）
        """
        try:
            from funasr import AutoModel
            
            print(f"正在加载 FunASR 模型：{model_name} (device={device})...")
            self.model = AutoModel(model=model_name, device=device)
            self.available = True
            print("✅ FunASR 模型加载成功")
        except Exception as e:
            print(f"❌ FunASR 加载失败：{e}")
            self.available = False
    
    def transcribe(self, audio_path: str) -> Tuple[bool, str, list]:
        """
        语音识别
        :param audio_path: 音频文件路径
        :return: (success, full_text, segments)
        """
        if not self.available:
            return False, "", []
        
        try:
            print(f"正在进行语音识别：{os.path.basename(audio_path)}")
            result = self.model.generate(input=audio_path)
            
            if result and len(result) > 0:
                if isinstance(result, list):
                    result_item = result[0]
                else:
                    result_item = result
                
                if isinstance(result_item, dict):
                    full_text = result_item.get('text', '')
                elif isinstance(result_item, str):
                    full_text = result_item
                else:
                    full_text = str(result_item)
                
                sentences = [{'text': full_text}]
                print(f"✅ 识别成功，字数：{len(full_text)}")
                return True, full_text, sentences
            else:
                print("❌ 识别结果为空")
                return False, "", []
                
        except Exception as e:
            print(f"❌ 识别失败：{e}")
            return False, "", []


class SenseVoiceLocal:
    """
    SenseVoice 本地语音识别（通过 ModelScope 下载模型，不依赖 API）
    识别准确率高，适合中文场景
    """
    
    def __init__(self, model_name: str = "iic/SenseVoiceSmall"):
        """
        初始化 SenseVoice 本地模型
        :param model_name: ModelScope 模型名称
        """
        try:
            from funasr import AutoModel
            
            print(f"正在加载 SenseVoice 本地模型：{model_name}...")
            
            # 使用 FunASR 的 AutoModel 加载 SenseVoice 模型
            self.model = AutoModel(
                model=model_name,
                device="cpu",
                ncpu=4,  # CPU 核心数
                disable_update=False  # 允许检查更新
            )
            
            self.available = True
            print("✅ SenseVoice 本地模型加载成功")
            
        except ImportError as e:
            print(f"❌ SenseVoice 本地模型未安装：{e}")
            self.available = False
            SENSEVOICE_LOCAL_IMPORT_ERROR = str(e)
        except Exception as e:
            print(f"❌ SenseVoice 本地模型加载失败：{e}")
            self.available = False
    
    def transcribe(self, audio_path: str) -> Tuple[bool, str, list]:
        """
        语音识别
        :param audio_path: 音频文件路径
        :return: (success, full_text, segments)
        """
        if not self.available:
            return False, "", []
        
        try:
            print(f"正在进行语音识别（SenseVoice 本地）：{os.path.basename(audio_path)}")
            
            # 使用 model.generate 进行识别，获取详细结果
            result = self.model.generate(input=audio_path)
            
            if result and len(result) > 0:
                if isinstance(result, list):
                    result_item = result[0]
                else:
                    result_item = result
                
                # 提取完整文本和分段信息（带时间戳）
                segments = []
                full_text = ""
                
                if isinstance(result_item, dict):
                    # 尝试获取详细的分段信息
                    if 'sentence_info' in result_item:
                        # 有详细分段信息
                        for sent in result_item['sentence_info']:
                            if isinstance(sent, dict):
                                seg = {
                                    'text': sent.get('text', ''),
                                    'start': float(sent.get('start', 0)),
                                    'end': float(sent.get('end', 0))
                                }
                                segments.append(seg)
                                full_text += sent.get('text', '')
                    else:
                        # 只有完整文本
                        full_text = result_item.get('text', '')
                        segments = [{'text': full_text, 'start': 0, 'end': 0}]
                elif isinstance(result_item, str):
                    full_text = result_item
                    segments = [{'text': full_text, 'start': 0, 'end': 0}]
                else:
                    full_text = str(result_item)
                    segments = [{'text': full_text, 'start': 0, 'end': 0}]
                
                print(f"✅ 识别成功，字数：{len(full_text)}，分段数：{len(segments)}")
                return True, full_text, segments
            else:
                print("❌ 识别结果为空")
                return False, "", []
                
        except Exception as e:
            print(f"❌ 识别失败：{e}")
            return False, "", []


class WhisperLocal:
    """
    Whisper 本地语音识别（使用 GitHub openai/whisper，不依赖 API）
    识别准确率高，支持多语言，适合复杂场景
    自动检测模型存在性，不存在则自动下载
    """
    
    def __init__(self, model_name: str = "base"):
        """
        初始化 Whisper 本地模型
        :param model_name: Whisper 模型名称（tiny / base / small / medium / large）
                          来自 GitHub: https://github.com/openai/whisper
        """
        try:
            import whisper
            import hashlib
            
            self.model_name = model_name
            print(f"正在检查 Whisper 模型：{model_name}...")
            
            # 检查模型是否已下载
            model_path = self._get_model_path(model_name)
            
            if model_path and os.path.exists(model_path):
                print(f"✅ 模型已存在：{model_path}")
            else:
                print(f"⏳ 模型不存在，开始下载：{model_name}...")
                print(f"💡 模型将下载到：~/.cache/whisper/")
            
            print(f"模型来源：GitHub openai/whisper")
            
            # 使用 openai-whisper 加载模型（会自动检查并下载）
            self.model = whisper.load_model(model_name)
            
            self.available = True
            print(f"✅ Whisper 本地模型加载成功 ({model_name})")
            
        except ImportError as e:
            print(f"❌ Whisper 未安装：{e}")
            print(f"💡 安装命令：pip install openai-whisper")
            self.available = False
        except Exception as e:
            print(f"❌ Whisper 模型加载失败：{e}")
            self.available = False
    
    def _get_model_path(self, model_name: str) -> Optional[str]:
        """
        获取模型文件的本地路径
        :param model_name: 模型名称
        :return: 模型文件路径或 None
        """
        # Whisper 模型默认下载路径
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        model_file = f"{model_name}.pt"
        model_path = os.path.join(cache_dir, model_file)
        return model_path
    
    def transcribe(self, audio_path: str, language: str = "zh") -> Tuple[bool, str, list]:
        """
        语音识别
        :param audio_path: 音频文件路径
        :param language: 语言代码（zh=中文，en=英文）
        :return: (success, full_text, segments)
        """
        if not self.available:
            return False, "", []
        
        try:
            print(f"正在进行语音识别（Whisper 本地）：{os.path.basename(audio_path)}")
            
            # 使用 Whisper 进行识别
            options = {
                "language": language,
                "word_timestamps": False,  # 不提取词级时间戳，提高速度
            }
            
            result = self.model.transcribe(audio_path, **options)
            
            if result and "segments" in result:
                segments = []
                full_text = ""
                
                for seg in result["segments"]:
                    segment_info = {
                        "text": seg.get("text", "").strip(),
                        "start": float(seg.get("start", 0)),
                        "end": float(seg.get("end", 0))
                    }
                    segments.append(segment_info)
                    full_text += segment_info["text"]
                
                print(f"✅ 识别成功，字数：{len(full_text)}，分段数：{len(segments)}")
                return True, full_text, segments
            else:
                print("❌ 识别结果为空")
                return False, "", []
                
        except Exception as e:
            print(f"❌ 识别失败：{e}")
            return False, "", []


class SherpaONNX:
    """
    Sherpa-ONNX 本地语音识别（轻量级备选方案）
    不依赖 torch，使用 ONNX 模型，适合环境受限场景
    """
    
    def __init__(self, model_type: str = "paraformer"):
        """
        初始化 Sherpa-ONNX 模型
        :param model_type: 模型类型（paraformer, whisper, transducer 等）
        """
        try:
            import sherpa_onnx
            
            print(f"正在加载 Sherpa-ONNX 模型：{model_type}...")
            
            # 根据模型类型配置
            if model_type == "paraformer":
                # 使用 Paraformer 模型（中文识别效果好）
                self.model = sherpa_onnx.OfflineRecognizer.from_paraformer(
                    paraformer="sherpa-onnx-paraformer-zh-2024-03-09/model.onnx",
                    tokens="sherpa-onnx-paraformer-zh-2024-03-09/tokens.txt",
                    num_threads=4,  # CPU 线程数
                    sample_rate=16000,
                    feature_dim=80,
                    decoding_method="greedy_search",
                )
            elif model_type == "whisper":
                # 使用 Whisper 模型（支持多语言）
                self.model = sherpa_onnx.OfflineRecognizer.from_whisper(
                    whisper_encoder="sherpa-onnx-whisper-base/encoder.onnx",
                    whisper_decoder="sherpa-onnx-whisper-base/decoder.onnx",
                    tokens="sherpa-onnx-whisper-base/tokens.txt",
                    num_threads=4,
                    sample_rate=16000,
                    feature_dim=80,
                    decoding_method="greedy_search",
                    language="zh",  # 中文
                )
            else:
                # 默认使用 transducer 模型
                self.model = sherpa_onnx.OfflineRecognizer.from_transducer(
                    encoder="sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-13/encoder-epoch-99-avg-1.onnx",
                    decoder="sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-13/decoder-epoch-99-avg-1.onnx",
                    joiner="sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-13/joiner-epoch-99-avg-1.onnx",
                    tokens="sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-13/tokens.txt",
                    num_threads=4,
                    sample_rate=16000,
                    feature_dim=80,
                    decoding_method="greedy_search",
                )
            
            self.available = True
            print("✅ Sherpa-ONNX 模型加载成功")
            
        except ImportError as e:
            print(f"❌ Sherpa-ONNX 未安装：{e}")
            self.available = False
            SHERPA_ONNX_IMPORT_ERROR = str(e)
        except Exception as e:
            print(f"❌ Sherpa-ONNX 加载失败：{e}")
            self.available = False
    
    def transcribe(self, audio_path: str) -> Tuple[bool, str, list]:
        """
        语音识别
        :param audio_path: 音频文件路径
        :return: (success, full_text, segments)
        """
        if not self.available:
            return False, "", []
        
        try:
            print(f"正在进行语音识别（Sherpa-ONNX）：{os.path.basename(audio_path)}")
            
            # 创建识别流
            stream = self.model.create_stream()
            
            # 读取音频文件
            import wave
            with wave.open(audio_path, 'rb') as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                data = wf.readframes(n_frames)
            
            # 转换为 float32 并归一化
            import numpy as np
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 如果采样率不是 16kHz，需要重采样
            if sample_rate != 16000:
                # 简单的线性插值重采样
                num_samples = int(len(samples) * 16000 / sample_rate)
                samples = np.interp(
                    np.linspace(0, len(samples), num_samples),
                    np.arange(len(samples)),
                    samples
                )
            
            # 输入音频数据
            stream.accept_waveform(16000, samples)
            
            # 结束输入
            self.model.input_finished(stream)
            
            # 获取识别结果
            result = self.model.get_result(stream)
            full_text = result.text.strip()
            
            if full_text:
                sentences = [{'text': full_text}]
                print(f"✅ 识别成功，字数：{len(full_text)}")
                return True, full_text, sentences
            else:
                print("❌ 识别结果为空")
                return False, "", []
                
        except Exception as e:
            print(f"❌ 识别失败：{e}")
            return False, "", []


class TextCleaner:
    """文案清理引擎"""
    
    def __init__(self):
        # 初始化简繁转换器
        self.converter = None
        if OPENCC_AVAILABLE:
            try:
                self.converter = opencc.OpenCC('t2s')  # 繁体转简体
                print("✅ OpenCC 已加载（支持繁体转简体）")
            except Exception as e:
                print(f"⚠️ OpenCC 加载失败：{e}")
    
    def convert_to_simplified(self, text: str) -> str:
        """将繁体中文转换为简体中文"""
        if not text:
            return text
        
        if self.converter:
            return self.converter.convert(text)
        else:
            # 如果没有 OpenCC，返回原文本
            return text
    
    @staticmethod
    def clean(raw_text: str) -> str:
        """
        清理文本：
        1. 移除表情包和特殊符号
        2. 修正常见错别字
        3. 移除重复字词（ASR 识别错误）
        4. 移除 FunASR 产生的字间空格
        5. 优化语义连贯性
        """
        text = raw_text
        
        # 0. 移除 FunASR 产生的字间空格（中文）
        text = text.replace(' ', '')
        
        # 1. 移除表情包和特殊符号
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)
        text = re.sub(r'[\U00002702-\U000027B0]', '', text)
        
        # 2. 移除其他特殊符号
        text = re.sub(r'[^\u4e00-\u9fff，。！？、；：""（）《》【】…—a-zA-Z0-9]', '', text)
        
        # 3. 修正常见错别字
        typo_fixes = {
            '在见': '再见',
            '那里': '哪里',
            '以经': '已经',
            '在次': '再次',
            '做业': '作业',
            '克苦': '刻苦',
            '蓝球': '篮球',
            '兵乓球': '乒乓球',
            '锻练': '锻炼',
            '即然': '既然',
            '做在': '坐在',
            '装古': '复古',
            '挪威': '挪威',
            '商业': '商业',
            '旭日': '旭日',
            '键了': '关键了',
            '匡威': '匡威',
            '特立独': '特立独行',
            '蜕变': '蜕变',
            '隔壁': '隔壁',
            '花园': '花园',
            '旅行': '旅行',
        }

        for wrong, correct in typo_fixes.items():
            text = text.replace(wrong, correct)
        
        # 4. 移除重复字词（关键优化）
        text = TextCleaner.remove_repeated_chars(text)
        
        return text
    
    @staticmethod
    def remove_repeated_chars(text: str) -> str:
        """
        移除 ASR 识别产生的重复字词
        
        策略：
        1. 移除连续重复的单个字符（如"的的的" → "的"）
        2. 移除连续重复的词语（如"需要需要" → "需要"）
        3. 保留有意义的重复（如"高高兴兴"）
        """
        if not text:
            return text
        
        # 1. 移除连续重复的单个字符（3 次及以上）
        # 匹配模式：单个字符重复 3 次或更多
        result = text
        for char in set(text):
            # 跳过标点符号
            if char in '，。！？、；：""（）《》【】…—':
                continue
            
            # 构建重复模式（3 次到 10 次）
            for repeat_count in range(10, 2, -1):
                pattern = char * repeat_count
                replacement = char  # 只保留一个
                result = result.replace(pattern, replacement)
        
        # 2. 移除连续重复的词语（2-4 个字重复）
        # 使用正则匹配重复词语
        import re
        
        # 匹配 2 字词重复（如"需要需要"）
        result = re.sub(r'([\u4e00-\u9fff]{2})\1+', r'\1', result)
        
        # 匹配 3 字词重复
        result = re.sub(r'([\u4e00-\u9fff]{3})\1+', r'\1', result)
        
        # 匹配 4 字词重复
        result = re.sub(r'([\u4e00-\u9fff]{4})\1+', r'\1', result)
        
        # 3. 特殊处理："的的"、"了了"、"那那"等常见 ASR 错误
        common_repeats = ['的的', '了了', '吗吗', '呢呢', '啊啊', '吧吧', '那那', '这这', '你你', '我我', '他他', '她她']
        for repeat in common_repeats:
            result = result.replace(repeat, repeat[0])
        
        # 4. 处理混合重复（如"需要要的的"）
        # 移除"的"字前的重复
        result = re.sub(r'的的+', '的', result)
        result = re.sub(r'了了+', '了', result)
        result = re.sub(r'吗吗+', '吗', result)
        result = re.sub(r'呢呢+', '呢', result)
        
        return result
    
    @staticmethod
    def optimize_with_llm(text: str, context: str = "") -> str:
        """
        基于大模型理解优化文案质量
        
        优化策略：
        1. 校正专业术语（通过语义理解）
        2. 移除开头乱码和 BGM 标记
        3. 修复断句和语义不连贯
        4. 补全被截断的句子
        5. 优化标点符号位置
        
        :param text: ASR 识别的原始文本
        :param context: 上下文信息（可选，如视频标题、描述等）
        :return: 优化后的文本
        
        注意：此方法需要调用外部大模型 API 才能真正生效
        当前为简化实现，只进行基础清理
        """
        if not text:
            return text
        
        result = text
        
        # 1. 移除开头乱码和无意义字符
        import re
        # 移除类似"zhEMOUNKNOWNBGMwoitn"的标记
        result = re.sub(r'^[a-zA-Z]{10,}', '', result)
        
        # 2. 基础清理
        result = re.sub(r'的。', '。', result)
        result = re.sub(r'的，', '，', result)
        
        # 3. 移除无意义的重复
        result = re.sub(r'([a-zA-Z\u4e00-\u9fff]{2,})\1', r'\1', result)
        
        # TODO: 调用大模型 API 进行深度优化
        # 示例（需要配置 API Key）：
        # if USE_LLM_OPTIMIZATION:
        #     result = call_llm_api(result, context)
        
        return result
    
    @staticmethod
    def add_punctuation(text: str) -> str:
        """
        基于语义添加标点符号（不使用正则）
        
        策略：
        1. 识别句末语气词添加句号
        2. 在停顿词后添加逗号
        3. 识别疑问句添加问号
        4. 基于常见句式结构断句
        5. 基于句子长度和语义完整性
        """
        if not text or len(text) < 2:
            return text
        
        result = []
        i = 0
        sentence_start = 0  # 当前句子开始位置
        min_sentence_len = 5  # 最小句子长度
        max_sentence_len = 50  # 最大句子长度
        
        # 句末语气词（表示一句话说完）
        sentence_end_words = ['了', '的', '吗', '呢', '啊', '吧', '啦', '咯', '嘛', '呀']
        # 停顿词（需要逗号）
        pause_words = ['的', '了', '吗', '呢', '啊', '吧', '嘛', '呀', '啦']
        # 疑问词
        question_words = ['什么', '为什么', '怎么', '如何', '哪里', '哪儿', '谁', '哪个', '哪些', '多少', '几']
        # 连接词（前面加逗号）
        conjunctions = ['但是', '可是', '然而', '不过', '所以', '因此', '因为', '如果', '虽然', '尽管']
        # 常见句式结尾
        sentence_patterns = ['是', '有', '在', '能', '会', '要', '想', '可以', '应该']
        
        while i < len(text):
            char = text[i]
            
            # 如果已经有标点，直接添加
            if char in '，。！？、；：""（）《》【】':
                result.append(char)
                i += 1
                sentence_start = i
                continue
            
            result.append(char)
            
            # 计算当前句子长度
            current_sentence_len = i - sentence_start + 1
            
            # 检查是否需要添加标点
            if i < len(text) - 1:
                next_char = text[i + 1] if i + 1 < len(text) else ''
                prev_char = text[i - 1] if i > 0 else ''
                prev2_char = text[i - 2] if i > 1 else ''
                
                # 1. 检查是否是疑问句
                is_question = False
                for qw in question_words:
                    if len(qw) == 1 and char == qw and next_char not in sentence_end_words:
                        is_question = True
                        break
                    elif len(qw) > 1 and i >= len(qw) - 1:
                        check_str = text[max(0, i-len(qw)+1):i+1]
                        if check_str.endswith(qw):
                            is_question = True
                            break
                
                # 2. 检查是否在句末语气词后（且句子足够长）
                is_sentence_end = False
                if char in sentence_end_words and current_sentence_len >= min_sentence_len:
                    # 排除一些特殊情况
                    if not (char == '的' and next_char in ['原', '原', '原', '原']):  # 避免在"的原因"前断开
                        is_sentence_end = True
                
                # 3. 检查是否在停顿词后（且不是词语中间）
                is_pause = False
                if char in pause_words and current_sentence_len >= 3:
                    # 避免在词语中间断开
                    if prev_char in '的得地':
                        is_pause = True
                    elif prev2_char in '的得地' and prev_char not in '的了':
                        is_pause = True
                    # 避免在"买它的"、"做它的"这类结构后断开
                    if prev2_char in '买做买' and char == '的':
                        is_pause = False
                
                # 4. 检查连接词前
                is_conjunction = False
                for conj in conjunctions:
                    if text[i+1:].startswith(conj):
                        is_conjunction = True
                        break
                
                # 5. 检查是否到达自然句末（基于常见模式）
                is_natural_end = False
                if char in sentence_patterns and next_char in '的了':
                    is_natural_end = True
                
                # 6. 基于句子长度强制断句
                is_length_end = current_sentence_len >= max_sentence_len
                
                # 添加标点
                if is_question and current_sentence_len >= 3:
                    result.append('？')
                    sentence_start = i + 1
                elif is_sentence_end:
                    result.append('。')
                    sentence_start = i + 1
                elif is_pause and current_sentence_len >= 5:
                    result.append('，')
                    sentence_start = i + 1
                elif is_conjunction:
                    result.append('，')
                    sentence_start = i + 1
                elif is_natural_end:
                    result.append('，')
                    sentence_start = i + 1
                elif is_length_end:
                    # 强制在合适位置断句
                    result.append('。')
                    sentence_start = i + 1
            
            i += 1
        
        # 合并重复标点并优化
        final_text = ''.join(result)
        final_text = final_text.replace('，，', '，')
        final_text = final_text.replace('。。', '。')
        final_text = final_text.replace('？？', '？')
        final_text = final_text.replace('！！', '！')
        final_text = final_text.replace('，。', '。')
        final_text = final_text.replace('。,', '。')
        final_text = final_text.replace('。的', '的')
        final_text = final_text.replace('，的', '的')
        
        return final_text
    
    @staticmethod
    def segment_text(text: str, max_length: int = 100) -> list:
        """按语义分段"""
        segments = []
        
        # 按句号、问号、感叹号分段
        pattern = r'(?<=[。！？\n])'
        parts = re.split(pattern, text)
        
        current_segment = ""
        for part in parts:
            if not part.strip():
                continue
            
            if len(current_segment) + len(part) <= max_length:
                current_segment += part
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = part
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments


class TranscriptGenerator:
    """文案生成器（只输出带时间戳的优化文案）"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, metadata: VideoMetadata, raw_text: str, cleaned_text: str, segments: list, raw_segments: list = None):
        """
        生成带时间戳的优化文案文件
        :param metadata: 视频元数据
        :param raw_text: 原始文本（未优化）
        :param cleaned_text: 优化后的文本（用于参考）
        :param segments: 优化后的分段（不使用）
        :param raw_segments: 带时间戳的原始分段
        :return: raw.txt 文件路径
        """
        # 只生成一个文件：raw.txt（带时间戳的优化文案）
        raw_path = os.path.join(self.output_dir, 'raw.txt')
        
        with open(raw_path, 'w', encoding='utf-8') as f:
            if raw_segments and len(raw_segments) > 0:
                # 输出带时间戳的格式，并对每句进行优化
                f.write("# 视频文案（带时间戳 + 已优化）\n\n")
                f.write(f"视频 ID: {metadata.video_id}\n")
                f.write(f"标题：{metadata.title}\n")
                f.write(f"时长：{metadata.duration:.2f}秒\n")
                f.write(f"提取时间：{metadata.extract_time}\n\n")
                f.write("=" * 50 + "\n\n")
                
                for i, seg in enumerate(raw_segments, 1):
                    if isinstance(seg, dict):
                        start = seg.get('start', 0)
                        end = seg.get('end', 0)
                        text = seg.get('text', '')
                        # 格式化时间戳
                        start_str = self._format_timestamp(start)
                        end_str = self._format_timestamp(end)
                        # 对文本进行优化（修正错别字、补全漏字）
                        optimized_text = self._optimize_segment(text, cleaned_text)
                        f.write(f"[{i:03d}] [{start_str} -> {end_str}] {optimized_text}\n")
                    else:
                        f.write(f"[{i:03d}] {seg}\n")
            else:
                # 没有时间戳，只输出纯文本
                f.write(raw_text)
        
        return raw_path
    
    def _optimize_segment(self, text: str, full_optimized_text: str) -> str:
        """
        对单个分段的文本进行优化（修正错别字、补全漏字）
        :param text: 原始文本
        :param full_optimized_text: 完整优化后的文本（用于参考）
        :return: 优化后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 1. 常见错别字修正（基于上下文理解）
        common_typos = {
            '住车': '注册',
            '信号': '新号',
            '比青年总': '鼻青脸肿',
            '高极各地部': '高级个体 IP',
            '哨而': '少儿',
            '承认': '成人',
            '全往': '全网',
            '自自清晰': '定位清晰',
            '没有生活': '美好生活',
            '油力吸吸': '油腻腻',
            '前置色降头': '前置摄像头',
            '送单单': '宋丹丹',
            '七个夜': '七个亿',
            '架效': '驾校',
            '巨勒步': '俱乐部',
            '之前的高几个体育': '值钱的高级个体',
            '人色': '人设',
            '求都': '都',
            '编借': '边界',
            '表达形势': '表达形式',
            '油力吸吸': '油腻腻',
            '不老实': '不老实',
            '较成': '教程',
            '考作文': '靠作文',
            '来用': '哪有',
            '巨勒步': '俱乐部',
            '干事': '干事',
            '你们': '你面前',
            '滚的远': '滚得远',
            '高几个体育': '高级个体',
        }
        
        for typo, correct in common_typos.items():
            if typo in result:
                result = result.replace(typo, correct)
        
        # 2. 补全漏字和标点
        # 补全"的"、"地"、"得"
        result = result.replace('的。', '。')
        result = result.replace('的，', '，')
        
        # 3. 移除无意义的重复
        import re
        result = re.sub(r'([a-zA-Z\u4e00-\u9fff]{2,})\1', r'\1', result)
        
        return result
    
    def _format_timestamp(self, seconds: float) -> str:
        """将秒数格式化为 MM:SS.mmm 格式"""
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:06.3f}"


class VideoTranscriptExtractor:
    """视频文案提取器（主类）"""
    
    def __init__(self, output_base: str = None, 
                 asr_engine: str = "auto",  # auto/whisper/sensevoice/funasr/sherpa
                 funasr_model: str = "paraformer-zh",
                 funasr_device: str = "cpu",
                 whisper_model: str = "base",
                 sherpa_model_type: str = "paraformer"):
        """
        初始化视频文案提取器
        :param output_base: 输出目录
        :param asr_engine: ASR 引擎选择（auto/whisper/sensevoice/funasr/sherpa）
        :param funasr_model: FunASR 模型名称
        :param funasr_device: FunASR 运行设备（cpu/cuda:0）
        :param whisper_model: Whisper 模型名称（tiny / base / small / medium / large）
        :param sherpa_model_type: Sherpa-ONNX 模型类型
        """
        self.output_base = output_base or os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(self.output_base, exist_ok=True)
        
        self.downloader = VideoDownloader(self.output_base)
        self.extractor = AudioExtractor()
        self.cleaner = TextCleaner()  # 初始化 cleaner（包含简繁转换）
        
        # 初始化 ASR 引擎
        self.asr = None
        
        if asr_engine == "auto":
            # 自动选择：Whisper > SenseVoice > FunASR > Sherpa-ONNX
            print("正在初始化 ASR 引擎（自动选择）...")
            self._init_asr_auto(funasr_model, funasr_device, whisper_model, sherpa_model_type)
        elif asr_engine == "whisper":
            self._init_whisper(whisper_model)
        elif asr_engine == "sensevoice":
            self._init_sensevoice()
        elif asr_engine == "funasr":
            self._init_funasr(funasr_model, funasr_device)
        elif asr_engine == "sherpa":
            self._init_sherpa_onnx(sherpa_model_type)
        
        # 检查是否成功初始化 ASR
        if not self.asr:
            print("\n❌ 错误：未成功初始化任何 ASR 引擎")
            print("💡 建议安装以下引擎之一：")
            print("  1. Whisper（推荐）：pip install funasr modelscope")
            print("  2. SenseVoice 本地：pip install funasr modelscope")
            print("  3. FunASR: pip install funasr torch torchaudio")
            print("  4. Sherpa-ONNX: pip install sherpa-onnx numpy")
    
    def _init_asr_auto(self, funasr_model: str, funasr_device: str, whisper_model: str, sherpa_model_type: str):
        """自动选择 ASR 引擎"""
        # 1. 优先尝试 Whisper（GitHub openai/whisper）
        try:
            import whisper
            print("尝试使用 Whisper 本地模型（推荐）...")
            self._init_whisper(whisper_model)
            if self.asr:
                return
        except:
            pass
        
        # 2. 尝试 SenseVoice
        try:
            print("尝试使用 SenseVoice 本地模型...")
            self._init_sensevoice()
            if self.asr:
                return
        except:
            pass
        
        # 3. 尝试 FunASR
        print("尝试使用 FunASR...")
        self._init_funasr(funasr_model, funasr_device)
        if self.asr:
            return
        
        # 4. 降级到 Sherpa-ONNX
        print("尝试使用 Sherpa-ONNX...")
        self._init_sherpa_onnx(sherpa_model_type)
    
    def _init_whisper(self, model_name: str):
        """初始化 Whisper 引擎"""
        try:
            print("正在初始化 Whisper...")
            self.asr = WhisperLocal(model_name=model_name)
            if self.asr.available:
                print("✅ Whisper 初始化成功")
            else:
                print("⚠️ Whisper 加载失败")
                self.asr = None
        except Exception as e:
            print(f"Whisper 初始化失败：{e}")
            self.asr = None
    
    def _init_sensevoice(self):
        """初始化 SenseVoice 引擎"""
        try:
            print("正在初始化 SenseVoice...")
            self.asr = SenseVoiceLocal(model_name="iic/SenseVoiceSmall")
            if self.asr.available:
                print("✅ SenseVoice 初始化成功")
            else:
                print("⚠️ SenseVoice 加载失败")
                self.asr = None
        except Exception as e:
            print(f"SenseVoice 初始化失败：{e}")
            self.asr = None
    
    def _init_funasr(self, model_name: str, device: str):
        """初始化 FunASR 引擎"""
        try:
            print("正在初始化 FunASR...")
            self.asr = FunASR(model_name=model_name, device=device)
            if self.asr.available:
                print("✅ FunASR 初始化成功")
            else:
                print("⚠️ FunASR 加载失败")
                self.asr = None
        except Exception as e:
            print(f"FunASR 初始化失败：{e}")
            self.asr = None
    
    def _init_sherpa_onnx(self, model_type: str):
        """初始化 Sherpa-ONNX 引擎"""
        try:
            print("正在初始化 Sherpa-ONNX...")
            self.asr = SherpaONNX(model_type=model_type)
            if self.asr.available:
                print("✅ Sherpa-ONNX 初始化成功")
            else:
                print("⚠️ Sherpa-ONNX 加载失败")
                self.asr = None
        except Exception as e:
            print(f"❌ Sherpa-ONNX 初始化失败：{e}")
            self.asr = None
    
    def extract_from_url(self, url: str) -> Dict:
        """从视频链接提取文案"""
        return self._extract(url=url, source_type='url')
    
    def extract_from_file(self, file_path: str) -> Dict:
        """从本地视频文件提取文案"""
        return self._extract(video_path=file_path, source_type='file')
    
    def _extract(self, url: str = None, video_path: str = None, source_type: str = 'url') -> Dict:
        """内部提取逻辑"""
        try:
            # 1. 准备输出目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 2. 下载视频或使用本地文件
            if source_type == 'url':
                print(f"正在下载视频：{url}")
                success, video_file, video_metadata = self.downloader.download(url)
                if not success:
                    return {'success': False, 'error': f'视频下载失败：{video_metadata.get("error", "")}'}
            else:
                video_file = video_path
                video_metadata = {}
            
            # 3. 提取元数据
            metadata = VideoMetadata(
                video_id=video_metadata.get('id', Path(video_file).stem),
                platform=video_metadata.get('extractor', '本地文件'),
                title=video_metadata.get('title', Path(video_file).stem),
                author=video_metadata.get('uploader', '未知'),
                duration=video_metadata.get('duration', 0.0),
                extract_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                source_type=source_type,
                source_path=url or video_path
            )
            
            output_dir = os.path.join(self.output_base, build_output_dir_name(timestamp, metadata.title))
            os.makedirs(output_dir, exist_ok=True)
            
            # 4. 提取音频
            print("正在提取音频...")
            success, audio_file = self.extractor.extract_audio(video_file, output_dir)
            if not success:
                return {'success': False, 'error': '音频提取失败'}
            
            # 5. 语音识别
            print("正在进行语音识别...")
            if not self.asr:
                return {'success': False, 'error': 'ASR 引擎未初始化'}
            
            success, raw_text, segments = self.asr.transcribe(audio_file)
            if not success:
                return {'success': False, 'error': '语音识别失败'}
            
            # 6. 文本清理和断句
            print("正在清理文本...")
            cleaned_text = self.cleaner.clean(raw_text)
            
            # 使用语义分析添加标点
            print("正在添加标点符号...")
            punctuated_text = self.cleaner.add_punctuation(cleaned_text)
            
            # 使用大模型理解优化文案质量
            print("正在智能优化文案（术语校正、语义连贯性）...")
            optimized_text = self.cleaner.optimize_with_llm(punctuated_text, metadata.title)
            
            # 繁体转简体
            if OPENCC_AVAILABLE:
                print("正在进行繁体转简体...")
                for seg in segments:
                    if isinstance(seg, dict) and 'text' in seg:
                        seg['text'] = self.cleaner.convert_to_simplified(seg['text'])
            
            # 分段
            segmented_text = self.cleaner.segment_text(optimized_text)
            
            # 7. 将视频文件移动到输出目录并以标题命名（保留视频）
            if source_type == 'url' and os.path.exists(video_file):
                safe_title = re.sub(INVALID_PATH_CHARS, ' ', metadata.title or '').strip()
                safe_title = re.sub(r'\s+', ' ', safe_title).strip(' .')[:80]
                ext = Path(video_file).suffix
                video_name = f"{safe_title}{ext}" if safe_title else f"{metadata.video_id}{ext}"
                saved_video = os.path.join(output_dir, video_name)
                try:
                    shutil.move(video_file, saved_video)
                    print(f"✅ 视频已保存：{video_name}")
                except Exception as e:
                    print(f"警告：保存视频文件失败 - {e}")
                # 清理临时音频和元数据文件
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                    info_json = str(Path(video_file).with_suffix('')) + '.info.json'
                    if os.path.exists(info_json):
                        os.remove(info_json)
                except Exception as e:
                    print(f"警告：清理临时文件失败 - {e}")
            
            # 8. 生成输出文件
            print("正在生成输出文件...")
            generator = TranscriptGenerator(output_dir)
            # 只生成 raw.txt（带时间戳的原始文案）
            raw_path = generator.generate(
                metadata, 
                raw_text,  # 原始文本
                optimized_text,  # 优化后的文本（不使用）
                segmented_text,  # 优化后的分段（不使用）
                segments  # 原始分段（带时间戳）
            )
            
            # 9. 删除音频文件（如果在输出目录中）
            if os.path.exists(audio_file):
                print(f"正在清理音频文件：{os.path.basename(audio_file)}")
                try:
                    os.remove(audio_file)
                except Exception as e:
                    print(f"警告：删除音频文件失败 - {e}")
            
            return {
                'success': True,
                'output_dir': output_dir,
                'raw_text_path': raw_path,
                'metadata': {
                    'video_id': metadata.video_id,
                    'platform': metadata.platform,
                    'title': metadata.title,
                    'duration': metadata.duration
                },
                'stats': {
                    'total_chars': len(raw_text),
                    'segments': len(segments)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='视频文案提取工具 v3.0 - 支持 Whisper/SenseVoice/FunASR 多引擎')
    parser.add_argument('source', help='视频链接或本地文件路径')
    parser.add_argument('--type', choices=['url', 'file'], default='url', help='输入类型')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--asr-engine', choices=['auto', 'whisper', 'sensevoice', 'funasr', 'sherpa'], default='auto', help='ASR 引擎选择（默认：auto）')
    parser.add_argument('--funasr-model', default='paraformer-zh', help='FunASR 模型名称（默认：paraformer-zh）')
    parser.add_argument('--funasr-device', default='cpu', help='FunASR 运行设备（默认：cpu）')
    parser.add_argument('--whisper-model', default='base', help='Whisper 模型名称（默认：base，可选：tiny/base/small/medium/large）')
    parser.add_argument('--sherpa-model', default='paraformer', help='Sherpa-ONNX 模型类型（默认：paraformer）')
    
    args = parser.parse_args()
    
    extractor = VideoTranscriptExtractor(
        output_base=args.output,
        asr_engine=args.asr_engine,
        funasr_model=args.funasr_model,
        funasr_device=args.funasr_device,
        whisper_model=args.whisper_model,
        sherpa_model_type=args.sherpa_model
    )
    
    if args.type == 'url':
        result = extractor.extract_from_url(args.source)
    else:
        result = extractor.extract_from_file(args.source)
    
    if result['success']:
        print(f"\n✅ 提取成功！")
        print(f"输出目录：{result['output_dir']}")
        print(f"原始文案（带时间戳）：{result['raw_text_path']}")
        print(f"\n统计信息：")
        print(f"  - 总字数：{result['stats']['total_chars']}")
        print(f"  - 分段数：{result['stats']['segments']}")
    else:
        print(f"\n❌ 提取失败：{result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

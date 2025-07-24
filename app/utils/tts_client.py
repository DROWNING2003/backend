"""
文本转语音客户端工具类
支持多种TTS服务提供商
"""

import os
import httpx
import logging
from typing import Dict, Any, List
import uuid
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class TTSClient:
    """TTS客户端类"""
    
    def __init__(self):
        self.api_key = os.getenv("TTS_API_KEY", "")
        self.base_url = os.getenv("TTS_BASE_URL", "")
        self.timeout = 120
        
        # 支持的语音列表
        self.available_voices = [
            {"name": "zh-CN-XiaoxiaoNeural", "language": "中文", "gender": "女"},
            {"name": "zh-CN-YunxiNeural", "language": "中文", "gender": "男"},
            {"name": "zh-CN-YunyangNeural", "language": "中文", "gender": "男"},
            {"name": "zh-CN-XiaoyiNeural", "language": "中文", "gender": "女"},
            {"name": "en-US-AriaNeural", "language": "英文", "gender": "女"},
            {"name": "en-US-DavisNeural", "language": "英文", "gender": "男"}
        ]
        
        # 音频文件存储目录
        self.audio_dir = os.getenv("AUDIO_DIR", "static/audio")
        os.makedirs(self.audio_dir, exist_ok=True)
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        文本转语音
        """
        try:
            # 如果没有配置TTS服务，返回模拟响应
            if not self.api_key or not self.base_url:
                logger.warning("未配置TTS服务，返回模拟响应")
                return self._get_mock_audio_response(text, format)
            
            # 调用真实的TTS服务
            return await self._call_tts_service(text, voice, speed, pitch, volume, format)
        
        except Exception as e:
            logger.error(f"TTS转换失败: {str(e)}")
            # 返回模拟响应作为降级处理
            return self._get_mock_audio_response(text, format)
    
    async def _call_tts_service(
        self,
        text: str,
        voice: str,
        speed: float,
        pitch: float,
        volume: float,
        format: str
    ) -> Dict[str, Any]:
        """
        调用真实的TTS服务
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "pitch": pitch,
            "volume": volume,
            "format": format
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/tts/generate",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"TTS API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"TTS API调用失败: {response.status_code}")
            
            result = response.json()
            
            # 如果返回的是base64编码的音频数据，保存到文件
            if "audio_data" in result:
                audio_data = base64.b64decode(result["audio_data"])
                filename = f"tts_{uuid.uuid4().hex}.{format}"
                file_path = os.path.join(self.audio_dir, filename)
                
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                
                audio_url = f"/static/audio/{filename}"
            else:
                audio_url = result.get("audio_url", "")
            
            return {
                "audio_url": audio_url,
                "duration": result.get("duration"),
                "file_size": result.get("file_size", len(audio_data) if "audio_data" in result else None)
            }
    
    def _get_mock_audio_response(self, text: str, format: str) -> Dict[str, Any]:
        """
        获取模拟音频响应（用于测试）
        """
        # 创建一个简单的模拟音频文件URL
        filename = f"mock_tts_{uuid.uuid4().hex}.{format}"
        audio_url = f"/static/audio/{filename}"
        
        # 估算音频时长（假设每分钟150字）
        estimated_duration = len(text) / 150 * 60
        
        logger.info(f"生成模拟TTS响应: {filename}")
        
        return {
            "audio_url": audio_url,
            "duration": round(estimated_duration, 2),
            "file_size": len(text.encode('utf-8')) * 100  # 模拟文件大小
        }
    
    async def check_health(self) -> bool:
        """
        检查TTS服务健康状态
        """
        try:
            if not self.api_key or not self.base_url:
                return True  # 模拟模式下认为服务正常
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=headers
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"TTS健康检查失败: {str(e)}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        获取可用语音列表
        """
        return self.available_voices

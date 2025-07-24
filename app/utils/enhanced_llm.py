"""
增强版LLM调用工具
基于原有call_llm.py，集成多种LLM API并支持缓存
"""

import os
import json
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


class EnhancedLLMClient:
    """增强版LLM客户端，支持多种API和缓存"""
    
    def __init__(self):
        # 配置缓存
        self.cache_file = "llm_cache.json"
        self.cache_enabled = True
        
        # Kimi API配置
        self.kimi_api_key = os.getenv("KIMI_API_KEY", "sk-8ktQlDnxXoVQDXHVROHVZw7HvjzouiCZEnsXqEhuP0jfPG6k")
        self.kimi_base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
        
        # SiliconFlow API配置
        self.siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY", "sk-ozqugiditsrmdfgpkihvlvruadjtyurfenwfcrsrdjzektop")
        self.siliconflow_base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        
        # OpenAI API配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        log_directory = os.getenv("LOG_DIR", "logs")
        os.makedirs(log_directory, exist_ok=True)
        
        log_file = os.path.join(
            log_directory, f"enhanced_llm_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        
        # 添加到logger
        llm_logger = logging.getLogger("enhanced_llm")
        llm_logger.setLevel(logging.INFO)
        llm_logger.propagate = False
        
        # 避免重复添加处理器
        if not llm_logger.handlers:
            llm_logger.addHandler(file_handler)
    
    async def call_llm(
        self,
        prompt: str,
        model: str = "moonshot-v1-8k",
        use_cache: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        调用LLM进行对话
        
        参数:
            prompt: 输入提示
            model: 使用的模型
            use_cache: 是否使用缓存
            temperature: 温度参数
            max_tokens: 最大token数
            
        返回:
            LLM响应文本
        """
        # 记录提示
        logger.info(f"PROMPT: {prompt[:200]}...")
        
        # 检查缓存
        if use_cache:
            cached_response = self._get_from_cache(prompt, model)
            if cached_response:
                logger.info(f"CACHE HIT: {cached_response[:200]}...")
                return cached_response
        
        # 调用LLM API
        try:
            response_text = await self._call_api(prompt, model, temperature, max_tokens)
            
            # 记录响应
            logger.info(f"RESPONSE: {response_text[:200]}...")
            
            # 保存到缓存
            if use_cache:
                self._save_to_cache(prompt, model, response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            return f"抱歉，LLM调用失败: {str(e)}"
    
    async def _call_api(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用具体的API"""
        messages = [{"role": "user", "content": prompt}]
        
        # 根据模型选择API
        if model.startswith("moonshot") and self.kimi_api_key:
            return await self._call_kimi_api(messages, model, temperature, max_tokens)
        elif model.startswith("deepseek") and self.siliconflow_api_key:
            return await self._call_siliconflow_api(messages, model, temperature, max_tokens)
        elif model.startswith("gpt") and self.openai_api_key:
            return await self._call_openai_api(messages, model, temperature, max_tokens)
        else:
            # 默认使用SiliconFlow
            return await self._call_siliconflow_api(messages, "deepseek-ai/DeepSeek-R1", temperature, max_tokens)
    
    async def _call_kimi_api(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用Kimi API"""
        headers = {
            "Authorization": f"Bearer {self.kimi_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.kimi_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Kimi API调用失败: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_siliconflow_api(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用SiliconFlow API"""
        headers = {
            "Authorization": f"Bearer {self.siliconflow_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.siliconflow_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"SiliconFlow API调用失败: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_openai_api(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API调用失败: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """生成缓存键"""
        content = f"{prompt}|{model}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, prompt: str, model: str) -> Optional[str]:
        """从缓存获取响应"""
        if not self.cache_enabled:
            return None
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                
                cache_key = self._get_cache_key(prompt, model)
                return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
        
        return None
    
    def _save_to_cache(self, prompt: str, model: str, response: str):
        """保存响应到缓存"""
        if not self.cache_enabled:
            return
        
        try:
            # 加载现有缓存
            cache = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            
            # 添加新响应
            cache_key = self._get_cache_key(prompt, model)
            cache[cache_key] = response
            
            # 保存缓存
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            logger.info("缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                
                file_size = os.path.getsize(self.cache_file)
                return {
                    "cache_entries": len(cache),
                    "cache_file_size": file_size,
                    "cache_enabled": self.cache_enabled
                }
            else:
                return {
                    "cache_entries": 0,
                    "cache_file_size": 0,
                    "cache_enabled": self.cache_enabled
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"error": str(e)}

"""
LLM客户端工具类
支持多种LLM服务提供商
"""

import os
import httpx
import logging
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端类"""

    def __init__(self):
        # 优先使用Kimi API
        self.kimi_api_key = os.getenv("KIMI_API_KEY", "sk-8ktQlDnxXoVQDXHVROHVZw7HvjzouiCZEnsXqEhuP0jfPG6k")
        self.kimi_base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")

        # 备用OpenAI API
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        # SiliconFlow API (备用)
        self.siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY", "sk-ozqugiditsrmdfgpkihvlvruadjtyurfenwfcrsrdjzektop")
        self.siliconflow_base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")

        self.timeout = 60

        # 支持的模型列表
        self.available_models = [
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "gpt-3.5-turbo",
            "gpt-4",
            "deepseek-ai/DeepSeek-R1"
        ]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        调用LLM进行对话，优先使用Kimi API
        """
        try:
            # 尝试使用Kimi API
            if self.kimi_api_key and model.startswith("moonshot"):
                return await self._call_kimi_api(messages, model, temperature, max_tokens)

            # 尝试使用OpenAI API
            if self.openai_api_key and model.startswith("gpt"):
                return await self._call_openai_api(messages, model, temperature, max_tokens)

            # 尝试使用SiliconFlow API
            if self.siliconflow_api_key:
                return await self._call_siliconflow_api(messages, model, temperature, max_tokens)

            # 如果没有配置任何API密钥，返回模拟响应
            logger.warning("未配置任何LLM API密钥，返回模拟响应")
            return self._get_mock_response(messages[-1]["content"])

        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            # 返回错误处理响应
            return self._get_error_response(str(e))

    async def _call_kimi_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.kimi_base_url}/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"Kimi API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"Kimi API调用失败: {response.status_code}")

            result = response.json()

            return {
                "message": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": model
            }

    async def _call_openai_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API调用失败: {response.status_code}")

            result = response.json()

            return {
                "message": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": model
            }

    async def _call_siliconflow_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.siliconflow_base_url}/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"SiliconFlow API调用失败: {response.status_code} - {response.text}")
                raise Exception(f"SiliconFlow API调用失败: {response.status_code}")

            result = response.json()

            return {
                "message": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": model
            }
    
    def _get_mock_response(self, user_message: str) -> Dict[str, Any]:
        """
        获取模拟响应（用于测试）
        """
        mock_responses = [
            "我是GitHub仓库学习助手，很高兴为您服务！我可以帮助您理解代码、解答编程问题。",
            "这是一个很好的问题！让我来为您详细解释一下。",
            "根据您的问题，我建议您可以从以下几个方面来学习：1. 先了解基础概念 2. 查看相关文档 3. 实践编写代码",
            "感谢您的提问！如果您需要更多帮助，请随时告诉我。"
        ]
        
        # 简单的关键词匹配
        response = mock_responses[0]
        if "代码" in user_message or "编程" in user_message:
            response = mock_responses[2]
        elif "?" in user_message or "？" in user_message:
            response = mock_responses[1]
        
        return {
            "message": response,
            "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
            "model": "mock-model"
        }
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        获取错误响应
        """
        return {
            "message": f"抱歉，我现在无法处理您的请求。错误信息：{error_message}",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "model": "error"
        }
    
    async def check_status(self) -> bool:
        """
        检查LLM服务状态
        """
        try:
            if not self.api_key:
                return True  # 模拟模式下认为服务正常
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"LLM状态检查失败: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        """
        return self.available_models

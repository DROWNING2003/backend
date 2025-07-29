#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token管理工具，用于处理LLM token限制问题
"""

import tiktoken
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class TokenManager:
    """Token管理器，用于控制prompt长度"""
    
    def __init__(self, model_name: str = "gpt-4", max_tokens: int = 120000):
        """
        初始化Token管理器
        
        Args:
            model_name: 模型名称，用于选择合适的tokenizer
            max_tokens: 最大token数量，留出一些余量给响应
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        
        # 尝试获取tokenizer，如果失败则使用默认的cl100k_base
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.encoding.encode(text))
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """截断文本到指定token数量"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def truncate_files_content(self, files_data: Dict[str, str], max_tokens_per_file: int = 2000) -> Dict[str, str]:
        """
        截断文件内容，确保每个文件不超过指定token数量
        
        Args:
            files_data: 文件路径到内容的映射
            max_tokens_per_file: 每个文件的最大token数量
            
        Returns:
            截断后的文件数据
        """
        truncated_files = {}
        
        for path, content in files_data.items():
            token_count = self.count_tokens(content)
            
            if token_count > max_tokens_per_file:
                # 截断内容并添加提示
                truncated_content = self.truncate_text(content, max_tokens_per_file - 100)
                truncated_content += f"\n\n[... 文件内容被截断，原始长度: {token_count} tokens ...]"
                truncated_files[path] = truncated_content
                logger.info(f"文件 {path} 被截断: {token_count} -> {self.count_tokens(truncated_content)} tokens")
            else:
                truncated_files[path] = content
                
        return truncated_files
    
    def truncate_diff_content(self, diff_lines: List[str], max_lines: int = 100) -> List[str]:
        """
        截断diff内容，保留最重要的变更
        
        Args:
            diff_lines: diff行列表
            max_lines: 最大行数
            
        Returns:
            截断后的diff行列表
        """
        if len(diff_lines) <= max_lines:
            return diff_lines
        
        # 优先保留添加和删除的行
        important_lines = []
        context_lines = []
        
        for line in diff_lines:
            if line.startswith(('+', '-', '@@')):
                important_lines.append(line)
            else:
                context_lines.append(line)
        
        # 如果重要行数就超过限制，只保留重要行
        if len(important_lines) >= max_lines:
            truncated = important_lines[:max_lines-1]
            truncated.append(f"[... diff内容被截断，原始行数: {len(diff_lines)} ...]")
            return truncated
        
        # 否则添加一些上下文行
        remaining_slots = max_lines - len(important_lines) - 1
        context_to_add = context_lines[:remaining_slots]
        
        result = important_lines + context_to_add
        result.append(f"[... diff内容被截断，原始行数: {len(diff_lines)} ...]")
        
        return result
    
    def optimize_prompt_for_abstractions(self, 
                                       context: str, 
                                       file_listing: str, 
                                       base_prompt: str,
                                       max_context_tokens: int = 80000) -> Tuple[str, str]:
        """
        为抽象概念识别优化prompt
        
        Args:
            context: 文件内容上下文
            file_listing: 文件列表
            base_prompt: 基础prompt模板
            max_context_tokens: 上下文最大token数量
            
        Returns:
            优化后的(context, 完整prompt)
        """
        # 计算基础prompt的token数量
        base_tokens = self.count_tokens(base_prompt + file_listing)
        available_tokens = max_context_tokens - base_tokens
        
        if available_tokens <= 0:
            logger.error("基础prompt太长，无法添加上下文")
            return "", base_prompt
        
        # 截断上下文
        context_tokens = self.count_tokens(context)
        if context_tokens > available_tokens:
            truncated_context = self.truncate_text(context, available_tokens)
            logger.info(f"上下文被截断: {context_tokens} -> {self.count_tokens(truncated_context)} tokens")
            return truncated_context, base_prompt
        
        return context, base_prompt
    
    def optimize_prompt_for_level_generation(self, 
                                           buffer: str, 
                                           base_prompt: str,
                                           max_buffer_tokens: int = 60000) -> Tuple[str, str]:
        """
        为关卡生成优化prompt
        
        Args:
            buffer: 变更详情buffer
            base_prompt: 基础prompt模板
            max_buffer_tokens: buffer最大token数量
            
        Returns:
            优化后的(buffer, 完整prompt)
        """
        buffer_tokens = self.count_tokens(buffer)
        
        if buffer_tokens > max_buffer_tokens:
            # 尝试智能截断buffer
            truncated_buffer = self._smart_truncate_buffer(buffer, max_buffer_tokens)
            logger.info(f"变更详情被截断: {buffer_tokens} -> {self.count_tokens(truncated_buffer)} tokens")
            return truncated_buffer, base_prompt
        
        return buffer, base_prompt
    
    def _smart_truncate_buffer(self, buffer: str, max_tokens: int) -> str:
        """
        智能截断buffer，保留最重要的信息
        """
        lines = buffer.split('\n')
        
        # 分类行
        header_lines = []  # 提交头信息
        diff_lines = []    # diff内容
        other_lines = []   # 其他内容
        
        for line in lines:
            if line.startswith('=== 提交') or line.startswith('文件变化详情'):
                header_lines.append(line)
            elif any(line.strip().startswith(prefix) for prefix in ['+', '-', '@@']):
                diff_lines.append(line)
            else:
                other_lines.append(line)
        
        # 优先保留头信息
        result_lines = header_lines[:]
        remaining_tokens = max_tokens - self.count_tokens('\n'.join(result_lines))
        
        # 添加重要的diff行
        important_diff = [line for line in diff_lines if line.strip().startswith(('+', '-'))]
        
        for line in important_diff:
            line_tokens = self.count_tokens(line)
            if remaining_tokens > line_tokens + 50:  # 留一些余量
                result_lines.append(line)
                remaining_tokens -= line_tokens
            else:
                break
        
        # 添加截断提示
        if len(result_lines) < len(lines):
            result_lines.append(f"\n[... 内容被截断以控制token数量，原始行数: {len(lines)} ...]")
        
        return '\n'.join(result_lines)


# 全局token管理器实例
token_manager = TokenManager()


def safe_call_llm(prompt: str, use_cache: bool = True, max_tokens: int = 120000) -> str:
    """
    安全的LLM调用，自动处理token限制
    
    Args:
        prompt: 原始prompt
        use_cache: 是否使用缓存
        max_tokens: 最大token数量
        
    Returns:
        LLM响应
    """
    from agentflow.utils.call_llm import call_llm
    
    # 检查token数量
    prompt_tokens = token_manager.count_tokens(prompt)
    
    if prompt_tokens > max_tokens:
        logger.warning(f"Prompt过长 ({prompt_tokens} tokens)，尝试截断到 {max_tokens} tokens")
        truncated_prompt = token_manager.truncate_text(prompt, max_tokens)
        return call_llm(truncated_prompt, use_cache)
    
    return call_llm(prompt, use_cache)


# 便捷函数
def count_tokens(text: str) -> int:
    """计算文本token数量的便捷函数"""
    return token_manager.count_tokens(text)


def truncate_text(text: str, max_tokens: int) -> str:
    """截断文本的便捷函数"""
    return token_manager.truncate_text(text, max_tokens)
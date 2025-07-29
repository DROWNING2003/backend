#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试token管理功能
"""

from agentflow.utils.call_llm import call_llm
from agentflow.utils.token_manager import token_manager, count_tokens
import tiktoken

def test_token_counting():
    """测试token计数功能"""
    print("=== 测试Token计数功能 ===")
    
    test_text = "Hello, this is a test message for token counting."
    token_count = count_tokens(test_text)
    print(f"测试文本: {test_text}")
    print(f"Token数量: {token_count}")
    
    # 验证与tiktoken的一致性
    encoding = tiktoken.get_encoding("cl100k_base")
    expected_count = len(encoding.encode(test_text))
    print(f"期望Token数量: {expected_count}")
    print(f"计数是否一致: {token_count == expected_count}")
    print()

def test_text_truncation():
    """测试文本截断功能"""
    print("=== 测试文本截断功能 ===")
    
    # 创建一个长文本
    long_text = "这是一个很长的测试文本。" * 1000
    original_tokens = count_tokens(long_text)
    print(f"原始文本Token数量: {original_tokens}")
    
    # 截断到100个token
    truncated_text = token_manager.truncate_text(long_text, 100)
    truncated_tokens = count_tokens(truncated_text)
    print(f"截断后Token数量: {truncated_tokens}")
    print(f"截断是否成功: {truncated_tokens <= 100}")
    print()

def test_files_truncation():
    """测试文件内容截断功能"""
    print("=== 测试文件内容截断功能 ===")
    
    # 模拟文件数据
    files_data = {
        "short_file.py": "print('hello')",
        "long_file.py": "# 这是一个很长的文件\n" + "print('line')\n" * 1000,
        "medium_file.py": "def function():\n    pass\n" * 100
    }
    
    print("原始文件Token数量:")
    for path, content in files_data.items():
        tokens = count_tokens(content)
        print(f"  {path}: {tokens} tokens")
    
    # 截断文件内容
    truncated_files = token_manager.truncate_files_content(files_data, max_tokens_per_file=500)
    
    print("\n截断后文件Token数量:")
    for path, content in truncated_files.items():
        tokens = count_tokens(content)
        print(f"  {path}: {tokens} tokens")
    print()

def test_diff_truncation():
    """测试diff内容截断功能"""
    print("=== 测试Diff内容截断功能 ===")
    
    # 模拟diff内容
    diff_lines = []
    diff_lines.append("@@ -1,10 +1,15 @@")
    for i in range(50):
        diff_lines.append(f"+新增行 {i}")
        diff_lines.append(f"-删除行 {i}")
        diff_lines.append(f" 上下文行 {i}")
    
    print(f"原始diff行数: {len(diff_lines)}")
    
    # 截断diff内容
    truncated_diff = token_manager.truncate_diff_content(diff_lines, max_lines=20)
    print(f"截断后diff行数: {len(truncated_diff)}")
    
    # 检查是否保留了重要行
    important_lines = [line for line in truncated_diff if line.startswith(('+', '-', '@@'))]
    print(f"重要行数量: {len(important_lines)}")
    print()

def test_prompt_optimization():
    """测试prompt优化功能"""
    print("=== 测试Prompt优化功能 ===")
    
    # 创建一个长上下文
    long_context = "这是文件内容。\n" * 10000
    file_listing = "- 0 # file1.py\n- 1 # file2.py"
    base_prompt = "请分析以下代码："
    
    print(f"原始上下文Token数量: {count_tokens(long_context)}")
    
    # 优化prompt
    optimized_context, optimized_prompt = token_manager.optimize_prompt_for_abstractions(
        long_context, file_listing, base_prompt, max_context_tokens=5000
    )
    
    print(f"优化后上下文Token数量: {count_tokens(optimized_context)}")
    print()

def test_call_llm_with_long_prompt():
    """测试带有长prompt的LLM调用"""
    print("=== 测试长Prompt的LLM调用 ===")
    
    # 创建一个可能超过token限制的prompt
    long_prompt = "请分析以下代码：\n" + "print('test')\n" * 50000
    
    print(f"原始prompt Token数量: {count_tokens(long_prompt)}")
    
    try:
        # 这应该会自动截断prompt
        response = call_llm(long_prompt, use_cache=False, max_tokens=1000)
        print("✅ LLM调用成功，prompt被自动截断")
        print(f"响应长度: {len(response)} 字符")
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
    print()

if __name__ == "__main__":
    print("🚀 开始测试Token管理功能")
    print("=" * 60)
    
    test_token_counting()
    test_text_truncation()
    test_files_truncation()
    test_diff_truncation()
    test_prompt_optimization()
    
    # 注意：这个测试会实际调用LLM，可能产生费用
    # test_call_llm_with_long_prompt()
    
    print("🎉 Token管理功能测试完成！")
from typing import Dict, List
from utils.call_llm import call_llm

def analyze_results(query: str, results: List[Dict]) -> Dict:
    """使用大语言模型分析搜索结果
    
    Args:
        query (str): 原始搜索查询
        results (List[Dict]): 待分析的搜索结果列表
        
    Returns:
        Dict: 包含摘要、关键点和后续查询的分析结果
    """
    # 格式化搜索结果用于提示词
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_results.append(f"""
结果 {i}:
标题: {result['title']}
摘要: {result['snippet']}
链接: {result['link']}
""")
    
    # 构建LLM提示词
    prompt = f"""
请分析以下针对查询「{query}」的搜索结果：

{'\n'.join(formatted_results)}

请提供：
1. 简洁的发现摘要（2-3句话）
2. 关键事实或要点（最多5条）
3. 建议的后续查询（2-3个）

用YAML格式输出：
```yaml
summary: >
    此处放摘要
key_points:
    - 要点1
    - 要点2
follow_up_queries:
    - 查询1
    - 查询2
"""
    
    try:
    # 调用大语言模型
    response = call_llm(prompt)
    # 提取YAML内容
    yaml_str = response.split("```yaml")[1].split("```")[0].strip()
    
    import yaml
    analysis = yaml.safe_load(yaml_str)
    
    # 验证返回字段
    assert "summary" in analysis
    assert "key_points" in analysis
    assert "follow_up_queries" in analysis
    assert isinstance(analysis["key_points"], list)
    assert isinstance(analysis["follow_up_queries"], list)
    
    return analysis
    
except Exception as e:
    print(f"分析结果时出错: {str(e)}")
    return {
        "summary": "结果分析失败",
        "key_points": [],
        "follow_up_queries": []
    }
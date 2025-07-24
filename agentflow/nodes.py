import os
import re
from tools.search import TavilySearchTool
import yaml
from pocketflow import Node, BatchNode
from utils.call_llm import call_llm


def analyze_results(query, results):
    """Analyze search results using LLM"""
    if not results or not results.get('results'):
        return {
            "summary": "No search results to analyze",
            "key_points": [],
            "follow_up_queries": []
        }
    
    # Format results for LLM analysis
    formatted_results = ""
    for i, result in enumerate(results.get('results', [])[:5], 1):
        formatted_results += f"\n{i}. {result.get('title', 'No title')}\n"
        formatted_results += f"   URL: {result.get('url', 'No URL')}\n"
        formatted_results += f"   Content: {result.get('content', 'No content')[:500]}...\n"
    
    prompt = f"""
    分析以下搜索结果，针对查询: "{query}"
    
    搜索结果:
    {formatted_results}
    
    请提供:
    1. 简要总结 (2-3句话)
    2. 关键要点 (3-5个要点)
    3. 建议的后续查询 (2-3个相关查询)
    
    请以JSON格式回复:
    {{
        "summary": "总结内容",
        "key_points": ["要点1", "要点2", "要点3"],
        "follow_up_queries": ["查询1", "查询2", "查询3"]
    }}
    """
    
    try:
        response = call_llm(prompt)
        # Try to parse JSON response
        import json
        analysis = json.loads(response)
        return analysis
    except Exception as e:
        return {
            "summary": f"分析失败: {str(e)}",
            "key_points": ["无法解析搜索结果"],
            "follow_up_queries": []
        }

class SearchNode(Node):
    """搜索节点用于补充技术细节"""
    
    def prep(self, shared):
        return shared.get("query"), shared.get("num_results", 5)
        
    def exec(self, inputs):
        query, num_results = inputs
        if not query:
            return []
            
        searcher = TavilySearchTool()
        return searcher.search(query, num_results)
        
    def post(self, shared, prep_res, exec_res):
        shared["search_results"] = exec_res
        return "default"

class AnalyzeResultsNode(Node):
    """Node to analyze search results using LLM"""
    
    def prep(self, shared):
        return shared.get("query"), shared.get("search_results", [])
        
    def exec(self, inputs):
        query, results = inputs
        if not results:
            return {
                "summary": "No search results to analyze",
                "key_points": [],
                "follow_up_queries": []
            }
            
        return analyze_results(query, results)
        
    def post(self, shared, prep_res, exec_res):
        shared["analysis"] = exec_res
        
        # Print analysis
        print("\nSearch Analysis:")
        print("\nSummary:", exec_res["summary"])
        
        print("\nKey Points:")
        for point in exec_res["key_points"]:
            print(f"- {point}")
            
        print("\nSuggested Follow-up Queries:")
        for query in exec_res["follow_up_queries"]:
            print(f"- {query}")
            
        return "default"

# class CommitToLevelConverter(Node):
#     def prep(self, shared):
#         """Get the search query from the shared store."""
#         return shared["search_query"]
        
#     def exec(self, search_query):
#         """Search the web for the given query."""
#         # Call the search utility function
#         print(f"🌐 Searching the web for: {search_query}")
#         results = search_web_duckduckgo(search_query)
#         return results
    
#     def post(self, shared, prep_res, exec_res):
#         """Save the search results and go back to the decision node."""
#         # Add the search results to the context in the shared store
#         previous = shared.get("context", "")
#         shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res
        
#         print(f"📚 Found information, analyzing results...")
        
#         # Always go back to the decision node after searching
#         return "decide"
    
# class DecideAction(Node):
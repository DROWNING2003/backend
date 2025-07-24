import os
from typing import Dict, List, Optional
from tavily import TavilyClient

class TavilySearchTool:
    """Tavily 专用搜索工具，支持网页内容、图片和域名过滤"""
    def __init__(
        self,
        api_key: Optional[str] = None,
        include_images: bool = False,
        default_domains: Optional[List[str]] = None
    ):
        """初始化Tavily搜索工具
        
        Args:
            api_key (str, optional): Tavily API密钥，默认从环境变量TAVILY_API_KEY获取
            include_images (bool): 是否包含图片结果（默认False）
            default_domains (List[str]): 默认包含的域名列表
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.include_images = include_images
        self.default_domains = default_domains or []
        
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
            
        # 初始化Tavily客户端
        self.client = TavilyClient(api_key=self.api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict:
        """执行搜索查询
        
        Args:
            query (str): 搜索关键词
            max_results (int): 返回结果数量（默认5）
            include_domains (List[str]): 指定包含的域名
            exclude_domains (List[str]): 指定排除的域名
            
        Returns:
            Dict: 包含原始内容、链接和图片（如果启用）的搜索结果
        """
        response = self.client.search(
            query=query,
            max_results=max_results,
            include_domains=include_domains or self.default_domains,
            exclude_domains=exclude_domains or [],
            include_raw_content=True,
            include_images=self.include_images,
            include_image_descriptions=self.include_images
        )
        return response

  
if __name__ == "__main__":
    # 测试配置（实际使用时请替换为你的TAVILY_API_KEY）
    test_config = {
        "api_key": "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",  # 替换为实际API密钥或设置为None从环境变量读取
        "include_images": False,
    }

    print("=== Tavily搜索工具测试 ===")
    
    # 初始化搜索工具
    try:
        searcher = TavilySearchTool(
            api_key=test_config["api_key"],
            include_images=test_config["include_images"],
        )
        print("✅ 工具初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        exit(1)

    # 测试1：基础搜索
    print("\n--- 测试1：基础搜索 ---")
    try:
        basic_results = searcher.search("Python 3.12 新特性", max_results=2)
        print(f"结果数量: {len(basic_results.get('results', []))}")
        print("第一条结果摘要:")
        print(basic_results.get('results', [{}])[0].get('content', '')[:200] + "...")
        print("✅ 基础搜索测试通过")
    except Exception as e:
        print(f"❌ 基础搜索失败: {e}")
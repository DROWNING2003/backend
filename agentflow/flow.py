from pocketflow import Flow
from nodes import SearchNode, AnalyzeResultsNode

def create_flow() -> Flow:
    """创建搜索节点
    
    Returns:
        Flow: Configured flow ready to run
    """
    # Create nodes
    search = SearchNode()
    analyze = AnalyzeResultsNode()
    
    # Connect nodes
    search >> analyze
    
    # Create flow starting with search
    return Flow(start=search)

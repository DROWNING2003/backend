from pocketflow import Flow
from nodes import IdentifyAbstractions, ToLevelConverter
#  repo_url = "https://github.com/zengyi-thinking/auto_mate_test3_call"
#     shared = {
#         "currentIndex":6,
#         "language":"中文",
#         "use_cache":True,
#         "max_abstraction_num":5,
#         "project_name": repo_url, 
#     }
    
    
#     flow = create_flow()
#     flow.run(shared)
#     print(shared["res"])
def create_flow() -> Flow:
    identifyAbstractions = IdentifyAbstractions()
    toLevelConverter = ToLevelConverter()
    # Create nodes
    # search = SearchNode()
    # analyze = AnalyzeResultsNode()
    identifyAbstractions >> toLevelConverter
    # # Connect nodes
    # search >> analyze
    
    # Create flow starting with search
    return Flow(start=identifyAbstractions)

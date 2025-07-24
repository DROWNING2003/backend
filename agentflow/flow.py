from pocketflow import Flow
from nodes import IdentifyAbstractions

def create_flow() -> Flow:
    identifyAbstractions = IdentifyAbstractions()
    # Create nodes
    # search = SearchNode()
    # analyze = AnalyzeResultsNode()
    
    # # Connect nodes
    # search >> analyze
    
    # Create flow starting with search
    return Flow(start=identifyAbstractions)

from pocketflow import Flow
from .nodes import IdentifyAbstractions, ToLevelConverter

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

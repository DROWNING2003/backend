from pocketflow import Flow

from agentflow.nodes import IdentifyAbstractions, ToLevelConverter

def create_flow() -> Flow:
    identifyAbstractions = IdentifyAbstractions()
    toLevelConverter = ToLevelConverter()
    identifyAbstractions >> toLevelConverter
    return Flow(start=identifyAbstractions)

def check_flow() -> Flow:
    """
    创建检查用户提交是否满足关卡要求的流程
    
    流程步骤：
    1. 获取关卡信息和要求 - 从数据库获取关卡详情和课程Git URL
    2. 克隆仓库并重置到指定提交 - 获取标准答案的代码状态
    3. 获取标准答案代码 - 读取当前提交的所有代码文件
    4. 分析用户提交的文件树 - 解析用户IDE中的文件结构和内容
    5. 使用LLM对比分析并给出评判结果 - AI智能评判是否满足关卡要求
    
    输入参数（通过shared传递）：
    - level_id: 关卡ID
    - course_id: 课程ID  
    - user_file_tree: 用户提交的文件树结构
    - language: 输出语言（默认"chinese"）
    - use_cache: 是否使用LLM缓存（默认True）
    
    输出结果（存储在shared中）：
    - judgment_result: 包含passed、score、feedback、suggestions等字段的评判结果
    """
    from agentflow.nodes import GetLevelInfoNode, CloneRepoNode, GetStandardCodeNode, AnalyzeUserCodeNode, CompareAndJudgeNode
    
    # 创建节点实例
    get_level_info = GetLevelInfoNode()
    clone_repo = CloneRepoNode()
    get_standard_code = GetStandardCodeNode()
    analyze_user_code = AnalyzeUserCodeNode()
    compare_and_judge = CompareAndJudgeNode()
    
    # 构建流程链：按顺序执行各个检查步骤
    get_level_info >> clone_repo >> get_standard_code >> analyze_user_code >> compare_and_judge
    
    return Flow(start=get_level_info)
from pocketflow import Flow

from agentflow.nodes import IdentifyAbstractions, ToLevelConverter, EvaluateContextWorthiness, SkipToNextCommitNode

def create_flow() -> Flow:
    identifyAbstractions = IdentifyAbstractions()
    toLevelConverter = ToLevelConverter()
    identifyAbstractions >> toLevelConverter
    return Flow(start=identifyAbstractions)

def create_adaptive_flow() -> Flow:
    """
    创建自适应的关卡生成流程，会评估上下文价值并自动累积多个提交
    
    流程步骤：
    1. 识别抽象概念 - 分析代码库提取核心知识点
    2. 评估上下文价值 - 判断当前变更是否值得作为关卡，如不够则累积更多提交
    3. 转换为关卡 - 基于累积的变更生成关卡内容
    
    输入参数（通过shared传递）：
    - tmpdirname: 临时目录路径
    - project_name: 项目名称
    - currentIndex: 当前提交索引
    - repo: Git仓库对象
    - language: 输出语言（默认"chinese"）
    - use_cache: 是否使用LLM缓存（默认True）
    
    输出结果（存储在shared中）：
    - knowledge: 识别的抽象概念列表
    - context_evaluation: 上下文评估结果
    - res: 生成的关卡内容
    """
    from agentflow.nodes import IdentifyAbstractions, EvaluateContextWorthiness, ToLevelConverter, SkipToNextCommitNode
    
    # 创建节点实例
    identify_abstractions = IdentifyAbstractions()
    evaluate_context = EvaluateContextWorthiness()
    to_level_converter = ToLevelConverter()
    skip_to_next = SkipToNextCommitNode()
    
    # 构建流程链
    identify_abstractions >> evaluate_context
    
    # 根据评估结果选择不同路径
    evaluate_context - "worthy" >> to_level_converter
    evaluate_context - "not_worthy" >> skip_to_next
    
    # 如果跳转成功，重新开始评估流程
    skip_to_next - "continue" >> identify_abstractions
    skip_to_next - "end" >> to_level_converter
    
    return Flow(start=identify_abstractions)

def create_test_flow() -> Flow:
    '''
    测试流程：简化的关卡生成流程，用于测试核心功能
    
    流程步骤：
    1. 评估上下文价值 - 判断当前变更是否值得作为关卡，如不够则累积更多提交
    2. 转换为关卡 - 基于累积的变更生成关卡内容
    
    '''
    from agentflow.nodes import EvaluateContextWorthiness, ToLevelConverter, SkipToNextCommitNode
    
    # 创建节点实例
    evaluate_context = EvaluateContextWorthiness()
    to_level_converter = ToLevelConverter()
    skip_to_next = SkipToNextCommitNode()
    
    # 根据评估结果选择不同路径
    evaluate_context - "worthy" >> to_level_converter
    evaluate_context - "not_worthy" >> skip_to_next
    
    # 如果跳转成功，重新开始评估流程
    skip_to_next - "continue" >> evaluate_context
    skip_to_next - "end" >> to_level_converter
    
    return Flow(start=evaluate_context)

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


# 使用示例：
# 
# # 创建自适应关卡生成流程
# flow = create_adaptive_flow()
# 
# # 设置输入参数
# shared_data = {
#     "tmpdirname": "/path/to/repo",
#     "project_name": "MyProject", 
#     "currentIndex": 1,
#     "repo": git_repo_object,
#     "language": "chinese",
#     "use_cache": True
# }
# 
# # 执行流程
# result = flow.run(shared=shared_data)
# 
# # 获取结果
# if result.shared.get("context_evaluation", {}).get("is_worthy"):
#     level_content = result.shared["res"]
#     print("生成的关卡内容:", level_content)
# else:
#     print("当前上下文不足以生成关卡")
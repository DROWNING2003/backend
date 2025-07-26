from dotenv import load_dotenv
from agentflow.utils.crawl_github_files import checkout_to_commit, get_full_commit_history, get_or_clone_repository
from agentflow.flow import create_adaptive_flow
load_dotenv()

def test_adaptive_flow():
    """测试自适应的关卡生成流程"""
    print("\n=== 测试自适应流程 ===")
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test4_complex"
    
    try:
        # 克隆或获取仓库
        print("正在克隆/获取仓库...")
        repo = get_or_clone_repository(repo_url, update_to_latest=False)
        tmpdirname = repo.working_dir
        checkout_to_commit(repo, commit_index=2)
        commits = get_full_commit_history(repo)
        # 设置共享数据
        shared = {
            "accumulated_changes":[],#累计差异
            "fullcommits": commits,
            "max_commits_to_check":4, #最多commit
            "commits_to_check":0, #当前累计commit
            "tmpdirname": tmpdirname,
            "project_name": repo_url,
            "currentIndex": 2,  # 从较早的提交开始测试
            "repo": repo,
            "language": "中文",
            "use_cache": True,
            "max_abstraction_num": 5,
        }
        
        print(f"开始从提交索引 {shared['currentIndex']} 进行自适应分析...")
        
        # 创建并运行自适应流程
        flow = create_adaptive_flow()
        result = flow.run(shared)
        
        # 输出结果
        print("\n=== 自适应流程执行结果 ===")
        
        # 检查上下文评估结果
        context_eval = shared.get("context_evaluation", {})
        if context_eval:
            print(f"✅ 上下文评估完成:")
            print(f"   - 是否值得作为关卡: {context_eval.get('is_worthy', False)}")
            print(f"   - 最终提交索引: {context_eval.get('final_commit_index', 'N/A')}")
            print(f"   - 处理的提交数: {context_eval.get('commits_processed', 'N/A')}")
            print(f"   - 评估原因: {context_eval.get('evaluation', {}).get('reason', 'N/A')}")
            
            if context_eval.get('is_worthy'):
                print(f"   - 关键概念: {context_eval.get('evaluation', {}).get('key_concepts', [])}")
        
        # 检查知识点识别结果
        knowledge = shared.get("knowledge", [])
        if knowledge:
            print(f"\n📚 识别的知识点 ({len(knowledge)}个):")
            for i, concept in enumerate(knowledge, 1):
                print(f"   {i}. {concept.get('name', 'N/A')}")
                print(f"      描述: {concept.get('description', 'N/A')[:100]}...")
        
        # 检查生成的关卡内容
        level_content = shared.get("res")
        if level_content:
            print(f"\n🎯 生成的关卡内容:")
            if isinstance(level_content, list):
                for i, level in enumerate(level_content, 1):
                    print(f"   关卡 {i}: {level.get('name', 'N/A')}")
                    print(f"   描述: {level.get('description', 'N/A')[:150]}...")
                    print(f"   要求: {level.get('requirements', 'N/A')[:100]}...")
                    print()
            else:
                print(f"   {level_content}")
        else:
            print("❌ 未生成关卡内容")
            
        # 检查最终的提交索引
        final_index = shared.get("currentIndex")
        print(f"\n📍 最终提交索引: {final_index}")
        
    except Exception as e:
        print(f"❌ 自适应流程执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
test_adaptive_flow()
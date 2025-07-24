"""
基于Git提交历史生成游戏化关卡的示例脚本
"""

import sys
import os
from pathlib import Path
import argparse
import json
import logging

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from agentflow.nodes import create_git_game_flow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("git_game_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="基于Git提交历史生成游戏化关卡")
    
    parser.add_argument(
        "--repo-url",
        type=str,
        required=True,
        help="Git仓库URL (SSH或HTTPS格式)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="game_levels.json",
        help="输出文件路径 (默认: game_levels.json)"
    )
    
    parser.add_argument(
        "--max-commits",
        type=int,
        default=50,
        help="最大分析的提交数量 (默认: 50)"
    )
    
    parser.add_argument(
        "--branch",
        type=str,
        default="main",
        help="要分析的分支名称 (默认: main)"
    )
    
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="禁用LLM增强关卡描述"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    try:
        logger.info(f"开始处理仓库: {args.repo_url}")
        
        # 创建游戏化关卡流程
        flow = create_git_game_flow(
            repo_url=args.repo_url,
            output_path=args.output,
            max_commits=args.max_commits,
            branch=args.branch,
            use_llm=not args.no_llm
        )
        
        # 运行流程
        logger.info("开始运行流程...")
        result = flow.run()
        
        # 检查结果
        if "export_result" in result and result["export_result"]["status"] == "success":
            logger.info(f"游戏关卡已成功生成并导出到: {result['export_result']['output_path']}")
            logger.info(f"共生成 {result['game_levels']['level_count']} 个关卡")
            
            # 打印关卡摘要
            print("\n===== 游戏关卡摘要 =====")
            for level in result["game_levels"]["levels"]:
                print(f"\n[关卡 {level['id']}] {level['name']}")
                print(f"难度: {level['difficulty']}")
                print(f"描述: {level['description']}")
                print(f"包含 {len(level['challenges'])} 个挑战")
                
                # 打印前3个挑战的摘要
                for i, challenge in enumerate(level["challenges"][:3]):
                    print(f"  - 挑战 {challenge['id']}: {challenge['title']}")
                
                if len(level["challenges"]) > 3:
                    print(f"  - ... 以及 {len(level['challenges']) - 3} 个更多挑战")
            
            print(f"\n完整关卡数据已保存到: {result['export_result']['output_path']}")
            
            return 0
        else:
            logger.error("游戏关卡生成失败")
            if "error" in result:
                logger.error(f"错误: {result['error']}")
            return 1
    
    except Exception as e:
        logger.exception(f"处理过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
import os
import tempfile
from dotenv import load_dotenv
from flow import create_flow
from utils.crawl_github_files import clone_repository, filter_and_read_files, get_commit_changes, get_commit_changes_detailed, get_exclude_patterns, get_file_patterns, reset_to_commit
# Load environment variables from .env file
load_dotenv()

def main():
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test3_call"
    shared = {
        "currentIndex":6,
        "language":"中文",
        "use_cache":True,
        "max_abstraction_num":5,
        "project_name": repo_url, 
    }
    
    
    flow = create_flow()
    flow.run(shared)
    print(shared["res"])
    # # Results are in shared["analysis"]
    
if __name__ == "__main__":
    main()

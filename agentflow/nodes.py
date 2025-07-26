import tempfile
from agentflow.utils.yamltool import robust_yaml_parse
from agentflow.utils.crawl_github_files import clone_repository, get_or_clone_repository, filter_and_read_files, get_commit_changes_detailed, get_exclude_patterns, get_file_patterns, checkout_to_commit
from agentflow.tools.search import TavilySearchTool
import yaml
from pocketflow import Node, BatchNode
from agentflow.utils.call_llm import call_llm


def analyze_results(query, results):
    """Analyze search results using LLM"""
    if not results or not results.get('results'):
        return {
            "summary": "No search results to analyze",
            "key_points": [],
            "follow_up_queries": []
        }
    
    # Format results for LLM analysis
    formatted_results = ""
    for i, result in enumerate(results.get('results', [])[:5], 1):
        formatted_results += f"\n{i}. {result.get('title', 'No title')}\n"
        formatted_results += f"   URL: {result.get('url', 'No URL')}\n"
        formatted_results += f"   Content: {result.get('content', 'No content')[:500]}...\n"
    
    prompt = f"""
    分析以下搜索结果，针对查询: "{query}"
    
    搜索结果:
    {formatted_results}
    
    请提供:
    1. 简要总结 (2-3句话)
    2. 关键要点 (3-5个要点)
    3. 建议的后续查询 (2-3个相关查询)
    
    请以JSON格式回复:
    {{
        "summary": "总结内容",
        "key_points": ["要点1", "要点2", "要点3"],
        "follow_up_queries": ["查询1", "查询2", "查询3"]
    }}
    """
    
    try:
        response = call_llm(prompt)
        # Try to parse JSON response
        import json
        analysis = json.loads(response)
        return analysis
    except Exception as e:
        return {
            "summary": f"分析失败: {str(e)}",
            "key_points": ["无法解析搜索结果"],
            "follow_up_queries": []
        }

class SearchNode(Node):
    """搜索节点用于补充技术细节"""
    
    def prep(self, shared):
        return shared.get("query"), shared.get("num_results", 5)
        
    def exec(self, inputs):
        query, num_results = inputs
        if not query:
            return []
            
        searcher = TavilySearchTool()
        return searcher.search(query, num_results)
        
    def post(self, shared, prep_res, exec_res):
        shared["search_results"] = exec_res
        return "default"


class IdentifyAbstractions(Node):
    """抽象知识点节点：使用LLM分析代码结构，提取核心知识点,"""
    def prep(self, shared):
        tmpdirname = shared["tmpdirname"]
        project_name = shared["project_name"]
        result = filter_and_read_files(
            tmpdirname,
            max_file_size=1 * 1024 * 1024,
            include_patterns=get_file_patterns("code"),  # 预定义Python模式
            exclude_patterns=get_exclude_patterns("common")  # 排除常见无用文件
        )
        files = result["files"]
        shared["files"] = files
        # 准备阶段：构建LLM分析所需的上下文

        language = shared.get("language", "chinese")  # 默认为中文输出
        use_cache = shared.get("use_cache", True)  # 默认启用缓存
        max_abstraction_num = shared.get("max_abstraction_num", 5)  # 限制最大概念数量
        print(files)
        # 格式化代码内容供LLM分析
        def create_llm_context(files_data):
            context = ""
            file_info = []  # 存储(索引, 路径)元组
            for i, (path, content) in enumerate(files_data.items()):
                # 为每个文件添加带索引的标记
                entry = f"--- File Index {i}: {path} ---\n{content}\n\n"
                context += entry
                file_info.append((i, path))
            return context, file_info

        # 生成LLM所需的上下文和文件列表
        context, file_info = create_llm_context(files)
        
        file_listing_for_prompt = "\n".join(
            [f"- {idx} # {path}" for idx, path in file_info]
        )
        
        # 返回预处理结果元组
        return (
            context,
            file_listing_for_prompt,
            len(files),
            project_name,
            language,
            use_cache,
            max_abstraction_num,
        )

    def exec(self, prep_res):
        # 执行阶段：调用LLM进行概念识别
        (
            context,
            file_listing_for_prompt,
            file_count,
            project_name,
            language,
            use_cache,
            max_abstraction_num,
        ) = prep_res  # 解包预处理结果

        # 根据输出语言配置提示词
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            # 非英语输出时需要特殊标记
            language_instruction = f"IMPORTANT: Generate the `name` and `description` in **{language.capitalize()}**\n\n"
            name_lang_hint = f" ({language} output)"
            desc_lang_hint = f" ({language} output)"

        # 构建完整的LLM提示词
        prompt = f"""
请分析项目 `{project_name}` 的代码库：

代码上下文：
{context}

{language_instruction}请识别5-{max_abstraction_num}个核心知识点：

每个概念需要提供：
1. `name`{name_lang_hint}：知识点名称
2. `description`（约100字）{desc_lang_hint}：知识点描述
3. `file_indices`：相关文件索引列表

文件索引对照表：
{file_listing_for_prompt}

请用YAML格式输出：

```yaml
- name: |
    示例概念{name_lang_hint}
  description: |
    这里是该知识概念的详细说明，描述其核心功能和设计意图。
    建议使用类比方式解释技术原理。{desc_lang_hint}
  file_indices:
    - 0 # 文件路径示例.py"""

        # 调用LLM并处理响应
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        # 提取和验证YAML响应
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        abstractions = yaml.safe_load(yaml_str)

        # 验证响应数据结构
        if not isinstance(abstractions, list):
            raise ValueError("LLM应返回列表格式")

        validated_abstractions = []
        for item in abstractions:
            # 检查必需字段
            if not all(k in item for k in ["name", "description", "file_indices"]):
                raise ValueError("抽象概念缺少必需字段")
                
            # 验证文件索引有效性
            valid_indices = []
            for idx_entry in item["file_indices"]:
                try:
                    idx = int(str(idx_entry).split("#")[0].strip())
                    if not 0 <= idx < file_count:
                        raise ValueError(f"文件索引{idx}越界")
                    valid_indices.append(idx)
                except (ValueError, TypeError):
                    raise ValueError("无效的文件索引格式")

            # 存储验证后的数据
            validated_abstractions.append({
                "name": item["name"],
                "description": item["description"],
                "files": sorted(set(valid_indices))  # 去重排序
            })

        return validated_abstractions

    def post(self, shared, prep_res, exec_res):
        print(exec_res)
        shared["knowledge"] = exec_res
        
class ToLevelConverter(Node):
    def prep(self, shared):
        
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        files_data = shared["files"]  # 获取文件数据
        currentIndex = shared["currentIndex"]  # 获取文件数据
        project_name = shared["project_name"]  # 从共享数据获取项目名称
        repo = shared["repo"]  # 从共享数据获取项目名称
        knowledge = shared["knowledge"]  # 从共享数据获取项目名称
        language = shared.get("language", "chinese")
        
        language_instruction = ""
        name_lang_hint = ""
        desc_lang_hint = ""
        if language.lower() != "english":
            # 非英语输出时需要特殊标记
            language_instruction = f"IMPORTANT: Generate the `name` and `description` in **{language.capitalize()}**\n\n"
            name_lang_hint = f" ({language} output)"
            desc_lang_hint = f" ({language} output)"
        
        #增量代码
        print(f"url：{project_name} 当前关卡：{currentIndex}")
        detailed_changes = get_commit_changes_detailed(repo, currentIndex, include_diff_content=True)
        buffer = []
        buffer.append("\n文件变化详情:")
        print(detailed_changes)
        for i, file_change in enumerate(detailed_changes['file_changes']):  # 显示所有文件
            # 显示diff内容（如果有）
            if file_change.get('diff_content') and file_change['diff_content'] != "[Binary file diff]":
                diff_lines = file_change['diff_content'].split('\n')[:]
                buffer.append(f"     Diff内容:")
                buffer.append(f"  {i+1}. {file_change['path']} ({file_change['type']})")
                for line in diff_lines:
                    if line.startswith('+'):
                        buffer.append(f"       {line}")
                    elif line.startswith('-'):
                        buffer.append(f"       {line}")
                    elif line.startswith('@@'):
                        buffer.append(f"       {line}")
            # else:
            #     buffer.append(f"获取详细变化失败: {detailed_changes.get('error', '未知错误')}")
        
        buffer = '\n'.join(buffer)
        shared["diff"] = buffer
        print(buffer)
        return (
            buffer,
            language_instruction,
            desc_lang_hint,
            name_lang_hint,
            files_data,
            knowledge,
            use_cache,
            project_name,
            language,
        )
        
    def exec(self, prep_res):
        (
            buffer,
            use_cache,
            language_instruction,
            desc_lang_hint,
            name_lang_hint,
            files_data,
            knowledge,
            project_name,
            language,
          
        ) = prep_res  # Unpack use_cache
        prompt = f"""
▲▲▲ 必须遵守的YAML生成规则 ▲▲▲
请根据项目 `{project_name}` 的代码库设计编程学习关卡，关卡描述使用markdown输出：

### 输入上下文
1. 代码变更详情：
{buffer}
2. 全局知识点：
{knowledge}

### 关卡设计规范
每个知识点关卡必须包含：
1. **知识点引入** - 用生活案例类比技术概念
2. **任务要求** - 具体的代码实现目标
3. **示例参考** - 可模仿的代码片段

### 输出格式要求
```yaml
  name: |
    关卡主题(8字以内) {name_lang_hint}
  description: |
    ▸ 知识点介绍
    ▸ 简单例子
    ▸ 语法说明
    ▸ 保持简洁明了
  requirements: |
    ▸ 通过语言描述代码功能
    ▸ 描述应有适当挑战性
    ▸ 用户能根据描述复现代码
---
### 示例
```yaml
  name: 数组
  
  description: |
    如果你想建立一个集合，可以用 _数组_ 这样的数据类型。Solidity 支持两种数组: _静态_ 数组和 _动态_ 数组:
    ```solidity
    // 固定长度为2的静态数组:
    uint[2] fixedArray;
    // 固定长度为5的string类型的静态数组:
    string[5] stringArray;
    // 动态数组，长度不固定，可以动态添加元素:
    uint[] dynamicArray;
    ```
    你也可以建立一个结构体类型的数组，例如，上一章提到的 Person:
    ```solidity
    Person[] people; // 这是动态数组，我们可以不断添加元素
    ```
    
    ## 公共数组
    你可以定义 public 数组，Solidity 会自动创建 getter 方法。语法如下:
    ```solidity
    Person[] public people;
    ```
    其它的合约可以从这个数组读取数据（但不能写入数据），所以这在合约中是一个有用的保存公共数据的模式。
    
  requirements: |
    为了把一个僵尸部队保存在我们的APP里，并且能够让其它APP看到这些僵尸，我们需要一个公共数组。
    创建一个数据类型为 Zombie 的结构体数组，用 public 修饰，命名为：zombies。
---
### 关键注意事项
1.严格保持2空格缩进层级
2.代码块必须用三重反引号明确闭合
3.避免在YAML中使用未转义的特殊符号
"""  
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        # --- Validation ---
        print(response)
        # yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        # Level_raw = yaml.safe_load(yaml_str)
        # print(Level_raw)
        Level_raw = robust_yaml_parse(response)
        # print(Level_raw)
        if not isinstance(Level_raw, list):
            raise ValueError("LLM output is not a list")
        # print("__________________输出_______________________")
        # print(Level_raw)
        return Level_raw
    
    def post(self, shared, prep_res, exec_res):
        shared["res"] = exec_res
        return


class GetLevelInfoNode(Node):
    """获取关卡信息节点：从数据库获取关卡要求和描述"""
    
    def __init__(self):
        super().__init__()
        self.cur_retry = 0
    
    def prep(self, shared):
        level_id = shared.get("level_id")
        course_id = shared.get("course_id")
        
        if not level_id or not course_id:
            raise ValueError("缺少必要参数：level_id 和 course_id")
        
        return level_id, course_id
    
    def exec(self, prep_res):
        level_id, course_id = prep_res
        
        try:
            # 这里需要导入数据库相关模块
            from app.database.connection import SessionLocal
            from app.models.level import Level
            from app.models.course import Course
            
            db = SessionLocal()
            try:
                # 获取关卡信息
                level = db.query(Level).filter(
                    Level.id == level_id,
                    Level.course_id == course_id
                ).first()
                
                if not level:
                    raise ValueError(f"未找到关卡 {level_id}")
                
                # 获取课程信息
                course = db.query(Course).filter(Course.id == course_id).first()
                if not course:
                    raise ValueError(f"未找到课程 {course_id}")
                
                return {
                    "level": {
                        "id": level.id,
                        "title": level.title,
                        "description": level.description,
                        "requirements": level.requirements,
                        "order_number": level.order_number
                    },
                    "course": {
                        "id": course.id,
                        "title": course.title,
                        "git_url": course.git_url
                    }
                }
                
            finally:
                db.close()
                
        except Exception as e:
            raise Exception(f"获取关卡信息失败: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        shared["level_info"] = exec_res["level"]
        shared["course_info"] = exec_res["course"]
        return "default"


class CloneRepoNode(Node):
    """克隆仓库节点：克隆课程仓库并重置到指定提交"""
    
    def prep(self, shared):
        course_info = shared.get("course_info")
        level_info = shared.get("level_info")
        
        if not course_info or not level_info:
            raise ValueError("缺少课程或关卡信息")
        
        git_url = course_info["git_url"]
        order_number = level_info["order_number"]
        
        # 计算提交索引（关卡顺序号 + 1，因为从第2个提交开始）
        commit_index = order_number + 1
        
        return git_url, commit_index
    
    def exec(self, prep_res):
        git_url, commit_index = prep_res
        
        try:
            # 使用共享目录获取或克隆仓库
            repo = get_or_clone_repository(git_url,update_to_latest=False)
            
            # 获取所有提交
            commits = list(repo.iter_commits(reverse=True))
            
            # 验证并调整提交索引
            if commit_index > len(commits):
                print(f"警告: 提交索引 {commit_index} 超出范围，仓库只有 {len(commits)} 个提交，使用最后一个提交")
                commit_index = len(commits)
            elif commit_index < 1:
                print(f"警告: 提交索引 {commit_index} 无效，使用第一个提交")
                commit_index = 1
            
            # 切换到指定提交
            checkout_to_commit(repo, commit_index)
            
            return {
                "repo": repo,
                "tmpdirname": repo.working_dir,
                "commits": commits,
                "commit_index": commit_index
            }
            
        except Exception as e:
            raise Exception(f"克隆仓库失败: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        # 将仓库信息存储到shared中，供后续节点使用
        shared["repo_info"] = exec_res
        shared["repo"] = exec_res["repo"]
        shared["tmpdirname"] = exec_res["tmpdirname"]
        shared["commits"] = exec_res["commits"]
        shared["commit_index"] = exec_res["commit_index"]
        return "default"


class GetStandardCodeNode(Node):
    """获取标准答案代码节点：从指定提交获取标准实现代码"""
    
    def prep(self, shared):
        repo_info = shared.get("repo_info")
        if not repo_info:
            raise ValueError("缺少仓库信息")
        
        tmpdirname = repo_info["tmpdirname"]
        return tmpdirname
    
    def exec(self, prep_res):
        tmpdirname = prep_res
        
        try:
            # 读取当前提交的所有代码文件
            result = filter_and_read_files(
                tmpdirname,
                max_file_size=1 * 1024 * 1024,
                include_patterns=get_file_patterns("code"),
                exclude_patterns=get_exclude_patterns("common")
            )
            
            return result["files"]
            
        except Exception as e:
            raise Exception(f"获取标准代码失败: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        shared["standard_code"] = exec_res
        return "default"


class AnalyzeUserCodeNode(Node):
    """分析用户代码节点：解析用户提交的文件树结构和代码内容"""
    
    def prep(self, shared):
        user_file_tree = shared.get("user_file_tree")
        if not user_file_tree:
            raise ValueError("缺少用户文件树数据")
        
        return user_file_tree
    
    def exec(self, prep_res):
        user_file_tree = prep_res
        
        try:
            # 解析文件树，提取文件内容
            user_files = {}
            
            def extract_files(node, current_path=""):
                if node.get("type") == "file":
                    file_path = node.get("uri", "").replace("file://", "")
                    if current_path:
                        relative_path = file_path.replace(current_path, "").lstrip("/")
                    else:
                        relative_path = file_path.split("/")[-1]  # 只取文件名
                    
                    content = node.get("content", "")
                    if content:
                        user_files[relative_path] = content
                
                elif node.get("type") == "directory":
                    children = node.get("children", [])
                    for child in children:
                        extract_files(child, current_path)
            
            extract_files(user_file_tree)
            
            return user_files
            
        except Exception as e:
            raise Exception(f"分析用户代码失败: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        shared["user_code"] = exec_res
        return "default"


class CompareAndJudgeNode(Node):
    """对比判断节点：使用LLM对比用户代码和标准答案，给出评判结果"""
    
    def __init__(self):
        super().__init__()
        self.cur_retry = 0  # 添加重试计数器
    
    def prep(self, shared):
        level_info = shared.get("level_info")
        standard_code = shared.get("standard_code")
        user_code = shared.get("user_code")
        
        if not all([level_info, standard_code, user_code]):
            raise ValueError("缺少必要的对比数据")
        
        use_cache = shared.get("use_cache", True)
        language = shared.get("language", "chinese")
        
        return level_info, standard_code, user_code, use_cache, language
    
    def exec(self, prep_res):
        level_info, standard_code, user_code, use_cache, language = prep_res
        
        try:
            # 构建标准代码内容字符串
            standard_code_str = "\n".join([
                f"=== {path} ===\n{content}\n"
                for path, content in standard_code.items()
            ])
            
            # 构建用户代码内容字符串
            user_code_str = "\n".join([
                f"=== {path} ===\n{content}\n"
                for path, content in user_code.items()
            ])
            
            # 构建LLM提示词
            prompt = f"""
你是一个编程学习平台的智能评判系统。请根据关卡要求，对比用户提交的代码和标准答案，给出评判结果。

## 关卡信息
**标题**: {level_info['title']}
**描述**: {level_info['description']}
**通过要求**: {level_info['requirements']}

## 标准答案代码
{standard_code_str}

## 用户提交代码
{user_code_str}

## 评判要求
请从以下几个维度进行评判：
1. **功能完整性**: 用户代码是否实现了关卡要求的功能
2. **代码正确性**: 语法是否正确，逻辑是否合理
3. **代码质量**: 代码风格、命名规范等
4. **创新性**: 是否有独特的实现思路

## 输出格式
请以JSON格式输出评判结果：
```json
{{
    "passed": true/false,
    "feedback": "详细的反馈信息，包括做得好的地方和需要改进的地方",
    "suggestions": [
        "具体的改进建议1",
        "具体的改进建议2"
    ],
    "praise": "如果通过了，给出鼓励性的话语",
    "detailed_analysis": {{
        "functionality": "功能完整性分析",
        "correctness": "代码正确性分析", 
        "quality": "代码质量分析",
        "innovation": "创新性分析"
    }}
}}
```

注意：
- 如果用户代码基本满足要求，即使有小问题也应该给予通过
- 反馈要具体、建设性，避免过于严厉
- 如果通过了要给予鼓励和肯定
"""
            
            # 调用LLM
            response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
            
            # 解析JSON响应
            import json
            try:
                # 提取JSON部分
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                result = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ["passed", "feedback"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"缺少必要字段: {field}")
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                # 如果JSON解析失败，返回基本结果
                return {
                    "passed": False,
                    "feedback": f"评判系统出现错误，无法解析LLM响应: {str(e)}",
                    "suggestions": ["请检查代码格式和语法"],
                    "error": str(e)
                }
                
        except Exception as e:
            return {
                "passed": False,
                "feedback": f"评判过程中出现错误: {str(e)}",
                "suggestions": ["请稍后重试"],
                "error": str(e)
            }
    
    def post(self, shared, prep_res, exec_res):
        shared["judgment_result"] = exec_res
        return "default"
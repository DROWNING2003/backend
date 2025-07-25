import os
import re
from tools.search import TavilySearchTool
import yaml
from pocketflow import Node, BatchNode
from utils.call_llm import call_llm


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
    """识别抽象概念节点：使用LLM分析代码结构，提取核心概念,"""
    def prep(self, shared):
        # 准备阶段：构建LLM分析所需的上下文
        files_data = shared["files"]  # 获取文件数据
        project_name = shared["project_name"]  # 从共享数据获取项目名称
        language = shared.get("language", "chinese")  # 默认为中文输出
        use_cache = shared.get("use_cache", True)  # 默认启用缓存
        max_abstraction_num = shared.get("max_abstraction_num", 5)  # 限制最大概念数量

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
        context, file_info = create_llm_context(files_data)
        file_listing_for_prompt = "\n".join(
            [f"- {idx} # {path}" for idx, path in file_info]
        )
        
        # 返回预处理结果元组
        return (
            context,
            file_listing_for_prompt,
            len(files_data),
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
        # 将结果存入共享上下文
        shared["knowledge"] = exec_res
        
class ToLevelConverter(Node):
    def prep(self, shared):
        use_cache = shared.get("use_cache", True)  # Get use_cache flag, default to True
        files_data = shared["files"]  # 获取文件数据
        project_name = shared["project_name"]  # 从共享数据获取项目名称
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
        return (
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
请根据项目 `{project_name}` 的代码库设计编程学习关卡：

代码上下文：
{files_data}
知识点：
{knowledge}

### 关卡设计规范
每个知识点关卡需包含：
1. **知识点引入** - 用生活案例类比技术概念
2. **任务要求** - 具体的代码实现目标
3. **示例参考** - 可模仿的代码片段

### 输出格式要求
```yaml
- name: |
    关卡主题{name_lang_hint}
  description: |
    ▸ 知识点介绍
    ▸ 简单例子
    ▸ 语法说明
    ▸ 简洁明了
  requirements: |
    ▸ 把代码通过语言描述
    ▸ 描述不应太过直白，需要有点挑战
    ▸ 用户可以根据描述完成复刻代码
```
### 示例
```yaml
- name: |
    数组
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
    你也可以建立一个 结构体类型的数组，例如，上一章提到的 Person:
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
```
"""
        response = call_llm(prompt, use_cache=(use_cache and self.cur_retry == 0))
        # --- Validation ---
        yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
        Level_raw = yaml.safe_load(yaml_str)
        if not isinstance(Level_raw, list):
            raise ValueError("LLM output is not a list")
        print("__________________输出_______________________")
        print(Level_raw)
        return Level_raw
    
    def post(self, shared, prep_res, exec_res):
        """Save the search results and go back to the decision node."""
        # Add the search results to the context in the shared store
        # previous = shared.get("context", "")
        # shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res
        
        # print(f"📚 Found information, analyzing results...")
        
        # Always go back to the decision node after searching
        return
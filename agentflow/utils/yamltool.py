import re
import yaml
from yaml import SafeLoader
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('yaml_parser')

def robust_yaml_parse(response):
    """
    鲁棒的 YAML 解析器，能够处理各种格式问题
    """
    try:
        # 1. 提取原始 YAML 内容
        yaml_content = extract_yaml_block(response)
        if not yaml_content:
            logger.warning("No YAML block found in response")
            return []
        
        # 2. 预处理和清理
        sanitized = preprocess_yaml(yaml_content)
        
        # 3. 处理多文档
        documents = []
        for doc in split_yaml_documents(sanitized):
            try:
                # 4. 修复缩进和格式
                fixed_doc = fix_yaml_indentation(doc)
                
                # 5. 尝试解析
                parsed = yaml.safe_load(fixed_doc)
                if parsed:
                    # 6. 验证结构
                    if validate_yaml_structure(parsed):
                        documents.append(parsed)
                    else:
                        logger.warning("Invalid YAML structure, skipping document")
                else:
                    logger.debug("Empty document after parsing")
            except yaml.YAMLError as e:
                logger.error(f"YAML parsing error: {e}")
                # 7. 尝试激进恢复
                recovered = try_recover_document(doc)
                if recovered:
                    documents.append(recovered)
    except Exception as e:
        logger.exception(f"Unexpected error in YAML parsing: {e}")
    
    return documents

def extract_yaml_block(text):
    """提取 YAML 代码块（兼容末尾没有```的情况）"""
    # 情况1：标准 ```yaml...``` 格式
    standard_pattern = r'```yaml\n(.*?)\n```'
    match = re.search(standard_pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    
    # 情况2：只有开始 ```yaml 没有结束 ```
    open_pattern = r'```yaml\n(.*)'
    match = re.search(open_pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    
    # 情况3：没有代码块标记，但可能是纯YAML内容
    if any(keyword in text.lower() for keyword in ['name:', 'description:', 'requirements:']):
        return text.strip()
    
    return None

def preprocess_yaml(yaml_text):
    """预处理 YAML 文本"""
    # 统一特殊字符
    sanitized = (
        yaml_text
        .replace('‘', "'").replace('’', "'")
        .replace('“', '"').replace('”', '"')
        .replace('•', '-')
        .replace('\t', '    ')  # Tab 转空格
    )
    
    # 修复常见格式问题
    sanitized = re.sub(r'^(\s*)(name|description|requirements):', r'  \2:', sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r'^(\s*)-', r'    -', sanitized, flags=re.MULTILINE)
    
    return sanitized

def split_yaml_documents(yaml_text):
    """分割多文档 YAML"""
    return re.split(r'\n---\n', yaml_text)

def fix_yaml_indentation(doc):
    """修复缩进问题"""
    lines = doc.split('\n')
    fixed_lines = []
    
    for line in lines:
        # 处理顶级字段
        if re.match(r'^\s*(name|description|requirements):', line):
            fixed_lines.append(line.strip())
        # 处理列表项
        elif re.match(r'^\s*-\s', line):
            fixed_lines.append('    ' + line.strip())
        # 其他内容保持原样
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def validate_yaml_structure(data):
    """验证 YAML 结构完整性"""
    if not isinstance(data, dict):
        return False
    
    required_keys = {'name', 'description', 'requirements'}
    if not required_keys.issubset(data.keys()):
        return False
    
    # 检查值类型
    return all(isinstance(data[k], str) for k in required_keys)

def try_recover_document(doc):
    """尝试恢复格式错误的文档"""
    try:
        # 激进修复：移除所有缩进
        minimal_doc = '\n'.join(line.strip() for line in doc.split('\n') if line.strip())
        
        # 尝试解析为列表
        parsed = yaml.safe_load(minimal_doc)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[0]
        
        # 尝试解析为字典
        if isinstance(parsed, dict):
            return parsed
        
        return None
    except:
        return None

# 示例使用
if __name__ == "__main__":
    # 模拟 AI 响应
    ai_response = """
```yaml
name: 给僵尸工厂添加“造僵尸”的方法
description: |-
  上一章我们把僵尸的 DNA 和名字封装成了一个叫 `Zombie` 的结构体，也学会了用 `public` 数组把它公开出去。
  现在我们要真正“造”出僵尸来，也就是写一个函数，把新的僵尸塞进数组里。

  ## 函数的基本写法
  在 Solidity 里，函数长这样：

  ```solidity
  function 函数名(参数类型 参数名, …) public {
      // 函数体：要执行的代码
  }
  ```

  举个最简单的例子，把两个数字加起来：

  ```solidity
  function add(uint a, uint b) public pure returns (uint) {
      return a + b;
  }
  ```

  注意：
  - `public` 表示任何人都能调用这个函数（包括别的合约、前端网页）。
  - 如果函数只是“做一件事”而不返回结果，可以省略 `returns (...)`。

  ## 往数组里塞东西
  数组有一个内置方法 `push()`，可以把新元素追加到末尾：

  ```solidity
  uint[] numbers;        // 声明一个动态数组
  numbers.push(42);      // 现在数组里有一个元素 42
  ```

  结构体也一样：

  ```solidity
  Person[] people;
  people.push(Person("Alice", 18));
  ```

  也就是说：
  1. 先“打包”好一个结构体变量；
  2. 再把它 `push` 进数组。

requirements: |
  在 `ZombieFactory` 合约里写一个 `createZombie` 函数：
  - 函数名：`createZombie`
  - 参数：`_name`（string 类型）、`_dna`（uint 类型）
  - 可见性：`public`
  - 函数体：用传入的 `_name` 与 `_dna` 创建一个新的 `Zombie` 结构体，并把它 `push` 到 `zombies` 数组中。

  提示：可以先在函数里写 `Zombie memory newZombie = Zombie(_name, _dna);` 再 `zombies.push(newZombie);`
  请不要照抄，自己敲一遍！
  ```
    """
    
    # 解析 YAML
    parsed_data = robust_yaml_parse(ai_response)
    
    # 输出结果
    if parsed_data:
        print("成功解析的文档:")
        for i, doc in enumerate(parsed_data):
            print(f"\n文档 {i+1}:")
            print(f"名称: {doc.get('name', '')}")
            print(f"描述: {doc.get('description', '')[:100]}...")
            print(f"要求: {doc.get('requirements', '')[:100]}...")
    else:
        print("未解析到有效文档")
from openai import OpenAI
import os
import logging
import readline
import json
import requests
from datetime import datetime
# ====================== 日志配置模块 ======================
# 设置日志存储目录（默认'logs'），确保目录存在
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)

# 创建带日期戳的日志文件路径
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"

def call_llm(prompt: str, use_cache: bool = True, max_tokens: int = 120000) -> str:
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")

    # Check and truncate prompt if too long
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        prompt_tokens = len(encoding.encode(prompt))
        
        if prompt_tokens > max_tokens:
            logger.warning(f"Prompt过长 ({prompt_tokens} tokens)，截断到 {max_tokens} tokens")
            # 截断prompt，保留重要部分
            tokens = encoding.encode(prompt)
            truncated_tokens = tokens[:max_tokens]
            prompt = encoding.decode(truncated_tokens)
            prompt += "\n\n[... 内容被截断以控制token数量 ...]"
            
    except ImportError:
        logger.warning("tiktoken未安装，无法检查token数量")
    except Exception as e:
        logger.warning(f"Token检查失败: {e}")

    # Check cache if enabled
    if use_cache:
        # Load cache from disk
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except:
                logger.warning(f"Failed to load cache, starting with empty cache")

        # Return from cache if exists
        if prompt in cache:
            logger.info(f"RESPONSE: {cache[prompt]}")
            return cache[prompt]

    try:
        client = OpenAI(
        api_key = "sk-8ktQlDnxXoVQDXHVROHVZw7HvjzouiCZEnsXqEhuP0jfPG6k",
        base_url = "https://api.moonshot.cn/v1")
     
        response = client.chat.completions.create(
        model = "kimi-k2-0711-preview",
        messages = [{"role": "user", "content": prompt}],
        temperature = 0.6)

        
        response_text = response.choices[0].message.content

        logger.info(f"RESPONSE: {response_text}")

        # Update cache if enabled
        if use_cache:
            # Load cache again to avoid overwrites
            cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                except:
                    pass

            # Add to cache and save
            cache[prompt] = response_text
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")

        return response_text
        
    except Exception as e:
        if "token limit" in str(e).lower():
            logger.error(f"Token限制错误: {e}")
            # 如果还是超限，进一步截断
            if max_tokens > 50000:
                logger.info("尝试进一步截断prompt")
                return call_llm(prompt, use_cache, max_tokens=50000)
        raise e

def call_MiniMax_llm(prompt: str) -> str:
    group_id = os.getenv("MINIMAX_GROUP_ID")
    api_key = os.getenv("MINIMAX_API_KEY")
    print("________",api_key)
    url = f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}"
    headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
    }
    payload = {
        "model": "MiniMax-M1",
        "messages": [
        {
            "content": prompt,
            "role": "user",
            "name": "auto-mate"
        }
        ],
        "stream": False,
        "max_tokens": 3186,
        "temperature": 1,
        "top_p": 0.95
        }
    response = requests.post(url, headers=headers, json=payload)
    return response.text
"""
API测试脚本
"""

import asyncio
import httpx
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def test_health_check():
    """测试健康检查"""
    logger.info("🔍 测试健康检查...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            logger.info(f"健康检查响应: {response.status_code}")
            logger.info(f"响应内容: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False


async def test_api_info():
    """测试API信息"""
    logger.info("📋 测试API信息...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/info")
            logger.info(f"API信息响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API信息获取失败: {e}")
            return False


async def test_course_list():
    """测试课程列表"""
    logger.info("📚 测试课程列表...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/courses/list")
            logger.info(f"课程列表响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"课程列表获取失败: {e}")
            return False


async def test_create_course():
    """测试创建课程"""
    logger.info("➕ 测试创建课程...")
    
    course_data = {
        "title": "Python基础编程测试课程",
        "tag": "编程语言",
        "description": "这是一个用于测试的Python基础编程课程",
        "git_url": "https://github.com/python/cpython"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/courses/create",
                json=course_data
            )
            logger.info(f"创建课程响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                course_id = response.json().get("id")
                logger.info(f"✅ 成功创建课程，ID: {course_id}")
                return course_id
            else:
                logger.error(f"❌ 创建课程失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"创建课程异常: {e}")
            return None


async def test_get_course(course_id: int):
    """测试获取课程详情"""
    logger.info(f"🔍 测试获取课程详情: {course_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/courses/get/{course_id}")
            logger.info(f"获取课程详情响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"获取课程详情失败: {e}")
            return False


async def test_generate_levels():
    """测试生成关卡"""
    logger.info("🤖 测试AI生成关卡...")
    
    generate_data = {
        "git_url": "https://github.com/python/cpython",
        "project_name": "Python官方项目",
        "language": "chinese",
        "max_levels": 5
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/levels/generate-from-git",
                json=generate_data
            )
            logger.info(f"生成关卡响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"生成关卡失败: {e}")
            return False


async def test_get_generated_levels():
    """测试获取生成的关卡"""
    logger.info("📋 测试获取生成的关卡...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/levels/get-generated")
            logger.info(f"获取生成关卡响应: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"获取生成关卡失败: {e}")
            return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始API测试...")
    
    tests = [
        ("健康检查", test_health_check),
        ("API信息", test_api_info),
        ("课程列表", test_course_list),
        ("生成关卡", test_generate_levels),
        ("获取生成关卡", test_get_generated_levels),
    ]
    
    results = []
    course_id = None
    
    # 执行基础测试
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            logger.info(f"{'✅' if result else '❌'} {test_name}: {'通过' if result else '失败'}")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 测试创建课程
    try:
        course_id = await test_create_course()
        if course_id:
            results.append(("创建课程", True))
            logger.info("✅ 创建课程: 通过")
            
            # 测试获取课程详情
            get_result = await test_get_course(course_id)
            results.append(("获取课程详情", get_result))
            logger.info(f"{'✅' if get_result else '❌'} 获取课程详情: {'通过' if get_result else '失败'}")
        else:
            results.append(("创建课程", False))
            logger.info("❌ 创建课程: 失败")
    except Exception as e:
        logger.error(f"❌ 创建课程测试异常: {e}")
        results.append(("创建课程", False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n📊 测试结果统计:")
    logger.info(f"总测试数: {total}")
    logger.info(f"通过数: {passed}")
    logger.info(f"失败数: {total - passed}")
    logger.info(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有测试通过！API系统运行正常")
    else:
        logger.warning("⚠️ 部分测试失败，请检查系统状态")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())

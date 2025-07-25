#!/usr/bin/env python3
"""
FastAPI路由示例
展示如何在API中使用改进后的CourseService
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="课程管理API示例", version="1.0.0")

# 导入必要的模块
try:
    from app.services.course_service import CourseService
    from app.schemas.course import CourseCreate, CourseResponse, CourseGenerationStatusResponse, CourseListResponse
    from app.database.connection import get_db
    
    # 创建CourseService实例（会自动配置数据库）
    course_service = CourseService()
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    course_service = None

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "课程管理API示例",
        "version": "1.0.0",
        "database_configured": course_service is not None and course_service.SessionLocal is not None
    }

@app.post("/courses/", response_model=CourseResponse)
async def create_course(course_data: CourseCreate, db: Session = Depends(get_db)):
    """
    创建课程
    
    - 立即返回课程信息
    - 在后台异步生成关卡
    - 用户会收到"正在生成中"的提示
    """
    if not course_service:
        raise HTTPException(status_code=500, detail="课程服务未初始化")
    
    try:
        # 创建课程，会自动启动异步关卡生成
        course_response = course_service.create_course(db, course_data)
        return course_response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/courses/", response_model=CourseListResponse)
async def get_courses(db: Session = Depends(get_db)):
    """获取所有课程列表"""
    if not course_service:
        raise HTTPException(status_code=500, detail="课程服务未初始化")
    
    try:
        courses_response = course_service.get_all_courses(db)
        return courses_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: Session = Depends(get_db)):
    """根据ID获取课程信息"""
    if not course_service:
        raise HTTPException(status_code=500, detail="课程服务未初始化")
    
    try:
        course = course_service.get_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/status", response_model=CourseGenerationStatusResponse)
async def get_course_generation_status(course_id: int, db: Session = Depends(get_db)):
    """
    获取课程关卡生成状态
    
    - 用于轮询检查关卡生成进度
    - 返回当前状态和已生成的关卡数量
    """
    if not course_service:
        raise HTTPException(status_code=500, detail="课程服务未初始化")
    
    try:
        status = course_service.get_course_generation_status(db, course_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return CourseGenerationStatusResponse(**status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        db_status = course_service.test_database_connection() if course_service else False
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "course_service": "initialized" if course_service else "not_initialized"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# 使用示例的注释
"""
API使用示例：

1. 创建课程：
POST /courses/
{
    "title": "Python基础编程",
    "tag": "编程语言", 
    "description": "学习Python基础知识",
    "git_url": "https://github.com/example/python-course"
}

响应：
{
    "id": 1,
    "title": "Python基础编程",
    "message": "课程创建成功，关卡正在生成中，请稍后刷新查看",
    "generation_status": "generating",
    "is_completed": false,
    "levels": [],
    "total_levels": 0
}

2. 检查生成状态：
GET /courses/1/status

响应：
{
    "course_id": 1,
    "status": "generating",
    "message": "关卡生成中，已生成 3 个关卡",
    "level_count": 3,
    "is_completed": false
}

3. 获取课程信息：
GET /courses/1

响应：
{
    "id": 1,
    "title": "Python基础编程",
    "is_completed": true,
    "levels": [
        {"id": 1, "title": "变量和数据类型", "order_number": 1},
        {"id": 2, "title": "控制流程", "order_number": 2}
    ],
    "total_levels": 2
}

前端轮询示例（JavaScript）：

async function createCourseAndMonitor(courseData) {
    // 1. 创建课程
    const response = await fetch('/courses/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(courseData)
    });
    const course = await response.json();
    
    if (course.generation_status === 'generating') {
        showMessage(course.message);
        
        // 2. 轮询状态
        const pollStatus = async () => {
            const statusResponse = await fetch(`/courses/${course.id}/status`);
            const status = await statusResponse.json();
            
            updateProgress(status.message);
            
            if (status.status === 'completed') {
                showSuccess('关卡生成完成！');
                refreshCourseData();
            } else if (status.status === 'generating') {
                setTimeout(pollStatus, 3000); // 3秒后再次检查
            }
        };
        
        pollStatus();
    }
}
"""

if __name__ == "__main__":
    import uvicorn
    print("启动API服务器...")
    print("访问 http://localhost:8000/docs 查看API文档")
    uvicorn.run(app, host="0.0.0.0", port=8000)
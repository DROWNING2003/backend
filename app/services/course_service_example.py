"""
CourseService 使用示例
展示如何正确初始化和使用 CourseService
"""

from app.services.course_service import CourseService
from app.database.connection import get_db, engine
from app.schemas.course import CourseCreate

# 方案1：传入数据库URL初始化
def create_course_service_with_url():
    """使用数据库URL初始化CourseService"""
    database_url = "sqlite:///./test.db"  # 替换为你的实际数据库URL
    course_service = CourseService(database_url=database_url)
    return course_service

# 方案2：使用现有的数据库引擎初始化
def create_course_service_with_engine():
    """使用现有数据库引擎初始化CourseService"""
    course_service = CourseService()
    # 假设你已经有了数据库引擎
    from app.database.connection import engine
    course_service.set_database_engine(engine)
    return course_service

# 方案3：在API路由中的使用示例
def api_usage_example():
    """在API路由中的使用示例"""
    
    # 在应用启动时初始化服务
    course_service = create_course_service_with_engine()
    
    # 在路由处理函数中使用
    def create_course_endpoint(course_data: CourseCreate, db = get_db()):
        try:
            # 创建课程，会自动启动异步关卡生成
            course_response = course_service.create_course(db, course_data)
            return course_response
        except Exception as e:
            raise Exception(f"创建课程失败: {str(e)}")
    
    # 检查生成状态
    def get_course_status_endpoint(course_id: int, db = get_db()):
        try:
            status = course_service.get_course_generation_status(db, course_id)
            return status
        except Exception as e:
            raise Exception(f"获取状态失败: {str(e)}")

# 完整的FastAPI示例
def fastapi_example():
    """完整的FastAPI使用示例"""
    
    from fastapi import FastAPI, Depends, HTTPException
    from sqlalchemy.orm import Session
    from app.database.connection import get_db, engine
    
    app = FastAPI()
    
    # 全局初始化CourseService
    course_service = CourseService()
    course_service.set_database_engine(engine)
    
    @app.post("/courses/")
    async def create_course(course_data: CourseCreate, db: Session = Depends(get_db)):
        """创建课程API"""
        try:
            course_response = course_service.create_course(db, course_data)
            return {
                "success": True,
                "data": course_response,
                "message": "课程创建成功，关卡正在后台生成中"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/courses/{course_id}/status")
    async def get_course_status(course_id: int, db: Session = Depends(get_db)):
        """获取课程生成状态API"""
        try:
            status = course_service.get_course_generation_status(db, course_id)
            if "error" in status:
                raise HTTPException(status_code=404, detail=status["error"])
            return {
                "success": True,
                "data": status
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

if __name__ == "__main__":
    # 测试示例
    print("CourseService 使用示例")
    
    # 创建服务实例
    service = create_course_service_with_engine()
    
    print("服务初始化完成，可以开始使用")
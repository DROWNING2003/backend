"""
课程相关业务逻辑服务
"""

import tempfile
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.models.level import Level
from agentflow.flow import create_flow
from agentflow.utils.crawl_github_files import clone_repository, reset_to_commit
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseResponse, CourseListResponse
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class CourseService:
    """课程服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def get_all_courses(self, db: Session) -> CourseListResponse:
        """
        获取所有课程列表
        
        Args:
            db: 数据库会话
            
        Returns:
            CourseListResponse: 课程列表响应
        """
        try:
            courses = db.query(Course).all()
            
            course_responses = []
            for course in courses:
                course_dict = course.to_dict_with_levels()
                course_responses.append(CourseResponse(**course_dict))
            
            return CourseListResponse(
                courses=course_responses,
                total=len(course_responses)
            )
            
        except SQLAlchemyError as e:
            logger.error(f"获取课程列表失败: {e}")
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取课程列表异常: {e}")
            raise Exception(f"获取课程列表失败: {str(e)}")
    
    def create_course(self, db: Session, course_data: CourseCreate) -> CourseResponse:
   
    # 创建课程对象
        new_course = Course(
        title=course_data.title,
        tag=course_data.tag,
        description=course_data.description,
        git_url=course_data.git_url,
    )
    
    # 保存到数据库
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
    
        logger.info(f"成功创建课程: {new_course.id} - {new_course.title}")
    
    # 异步生成关卡（错误不中断主流程）
        self._generate_levels_for_course(db,new_course.id, course_data.git_url)
    
    # 返回课程信息
        course_dict = new_course.to_dict_with_levels()
        return CourseResponse(**course_dict)
    
    def get_course_by_id(self, db: Session, course_id: int) -> Optional[CourseResponse]:
        """
        根据ID获取课程信息
        
        Args:
            db: 数据库会话
            course_id: 课程ID
            
        Returns:
            Optional[CourseResponse]: 课程信息，如果不存在则返回None
        """
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            
            if not course:
                return None
            
            course_dict = course.to_dict_with_levels()
            return CourseResponse(**course_dict)
            
        except SQLAlchemyError as e:
            logger.error(f"获取课程失败: {e}")
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取课程异常: {e}")
            raise Exception(f"获取课程失败: {str(e)}")
    
    def _generate_default_image_url(self, tag: str) -> str:
        """
        生成默认图片URL
        
        Args:
            tag: 课程标签
            
        Returns:
            str: 默认图片URL
        """
        # 这里可以根据标签生成不同的默认图片
        # 暂时返回一个基于标签的固定URL
        tag_hash = abs(hash(tag)) % 10  # 生成0-9的数字
        return f"https://picsum.photos/400/300?random={tag_hash}"
    
    def _generate_levels_for_course(self, db: Session,course:int, git_url: str):
        """
        为课程生成关卡
        
        Args:
            db: 数据库会话
            course: 课程对象
            git_url: Git仓库URL
        """
        # try:
            # 调用AI服务生成关卡
            # generated_levels = self.ai_service.generate_levels_from_git(
            #     git_url=git_url,
            #     project_name=course.title
            # )
        repo_url = git_url
        tmpdirname = tempfile.mkdtemp()
            
        repo = clone_repository(repo_url, tmpdirname)
        commits = list(repo.iter_commits(reverse=True))
        for i in range(2,len(commits)+1):
                shared = {
                "fullcommits":commits,
                "currentIndex":i,
                "language":"中文",
                "use_cache":True,
                "max_abstraction_num":5,
                "project_name": repo_url, 
                "repo":repo,
                "tmpdirname":tmpdirname,
                }
                
                reset_to_commit(repo,commits, i)
                flow = create_flow()
                flow.run(shared)
                if shared["res"]:
                    print(shared["res"][0]["name"])
                course = db.query(Course).filter(Course.id == course).first()
                if not course:
                    raise Exception(f"课程 {course.id} 不存在")
                
                new_level = Level(
                course_id=course.id,
                title=shared["res"][0]["name"],
                description=shared["res"][0]["description"],
                requirements=shared["res"][0]["requirements"],
                order_number=i-1,
            )
            
            # 保存到数据库
                db.add(new_level)
                db.commit()
                db.refresh(new_level)
                
                logger.info(f'为课程 {shared["res"][0]["name"]} 成功生成 {i} 个关卡')
            
            # else:
            #     logger.warning(f"为课程 {course.id} 生成关卡失败")
                
        # except Exception as e:
        #     logger.error(f"为课程生成关卡时出错: {e}")

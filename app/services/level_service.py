"""
关卡相关业务逻辑服务
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.level import Level
from app.models.course import Course
from app.schemas.level import LevelResponse, LevelCheckResponse, GeneratedLevel
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


class LevelService:
    """关卡服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def get_level_by_id(self, db: Session, level_id: int) -> Optional[LevelResponse]:
        """
        根据ID获取关卡详细信息
        
        Args:
            db: 数据库会话
            level_id: 关卡ID
            
        Returns:
            Optional[LevelResponse]: 关卡详细信息，如果不存在则返回None
        """
        try:
            level = db.query(Level).filter(Level.id == level_id).first()
            
            if not level:
                return None
            
            level_dict = level.to_dict_with_course()
            return LevelResponse(**level_dict)
            
        except SQLAlchemyError as e:
            logger.error(f"获取关卡失败: {e}")
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取关卡异常: {e}")
            raise Exception(f"获取关卡失败: {str(e)}")
    
    def check_level_completion(self, db: Session, level_id: int, user_answer: str) -> LevelCheckResponse:
        """
        检查关卡完成状态
        
        Args:
            db: 数据库会话
            level_id: 关卡ID
            user_answer: 用户提交的答案/代码
            
        Returns:
            LevelCheckResponse: 检查结果
        """
        try:
            # 获取关卡信息
            level = db.query(Level).filter(Level.id == level_id).first()
            
            if not level:
                raise Exception(f"关卡 {level_id} 不存在")
            
            # 调用AI服务进行答案检查
            check_result = self.ai_service.check_user_answer(
                level_title=level.title,
                level_description=level.description,
                requirements=level.requirements,
                user_answer=user_answer,
                level_content=level.content
            )
            
            logger.info(f"关卡 {level_id} 检查完成，结果: {'通过' if check_result.passed else '未通过'}")
            
            return check_result
            
        except SQLAlchemyError as e:
            logger.error(f"检查关卡完成状态失败: {e}")
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"检查关卡完成状态异常: {e}")
            raise Exception(f"检查关卡完成状态失败: {str(e)}")
    
    def create_level_from_generated(self, db: Session, course_id: int, generated_level: GeneratedLevel) -> Level:
        """
        从生成的关卡数据创建关卡记录
        
        Args:
            db: 数据库会话
            course_id: 课程ID
            generated_level: 生成的关卡数据
            
        Returns:
            Level: 创建的关卡对象
        """
        try:
            # 检查课程是否存在
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise Exception(f"课程 {course_id} 不存在")
            
            # 创建关卡对象
            new_level = Level(
                course_id=course_id,
                title=generated_level.name,
                description=generated_level.description,
                requirements=generated_level.requirements,
                order_number=generated_level.order_number,
                content={
                    "generated": True,
                    "source": "ai_generated",
                    "level_type": "coding_challenge"
                }
            )
            
            # 保存到数据库
            db.add(new_level)
            db.commit()
            db.refresh(new_level)
            
            logger.info(f"成功创建关卡: {new_level.id} - {new_level.title}")
            
            return new_level
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"创建关卡失败: {e}")
            raise Exception(f"数据库操作失败: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"创建关卡异常: {e}")
            raise Exception(f"创建关卡失败: {str(e)}")
    
    def get_levels_by_course_id(self, db: Session, course_id: int) -> list[LevelResponse]:
        """
        根据课程ID获取所有关卡
        
        Args:
            db: 数据库会话
            course_id: 课程ID
            
        Returns:
            list[LevelResponse]: 关卡列表
        """
        try:
            levels = db.query(Level).filter(Level.course_id == course_id).order_by(Level.order_number).all()
            
            level_responses = []
            for level in levels:
                level_dict = level.to_dict_with_course()
                level_responses.append(LevelResponse(**level_dict))
            
            return level_responses
            
        except SQLAlchemyError as e:
            logger.error(f"获取课程关卡失败: {e}")
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取课程关卡异常: {e}")
            raise Exception(f"获取课程关卡失败: {str(e)}")
    
    def update_level_content(self, db: Session, level_id: int, content: dict) -> Optional[LevelResponse]:
        """
        更新关卡内容
        
        Args:
            db: 数据库会话
            level_id: 关卡ID
            content: 新的内容
            
        Returns:
            Optional[LevelResponse]: 更新后的关卡信息
        """
        try:
            level = db.query(Level).filter(Level.id == level_id).first()
            
            if not level:
                return None
            
            level.content = content
            db.commit()
            db.refresh(level)
            
            logger.info(f"成功更新关卡内容: {level_id}")
            
            level_dict = level.to_dict_with_course()
            return LevelResponse(**level_dict)
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"更新关卡内容失败: {e}")
            raise Exception(f"数据库操作失败: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"更新关卡内容异常: {e}")
            raise Exception(f"更新关卡内容失败: {str(e)}")

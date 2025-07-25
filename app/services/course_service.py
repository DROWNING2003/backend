"""
课程相关业务逻辑服务
"""

import tempfile
import uuid
import asyncio
import threading
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
    
    def __init__(self, database_url: str = None):
        self.ai_service = AIService()
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
        # 尝试自动配置数据库
        self.auto_configure_database()
        
        # 如果传入了database_url，则覆盖自动配置
        if database_url:
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info(f"使用传入的数据库URL: {database_url}")
    
    def set_database_engine(self, engine):
        """
        设置数据库引擎（用于异步任务）
        
        Args:
            engine: SQLAlchemy数据库引擎
        """
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("已设置数据库引擎用于异步任务")
    
    def auto_configure_database(self):
        """
        自动配置数据库连接
        尝试从多个来源获取数据库引擎
        """
        if self.SessionLocal:
            logger.info("数据库已配置，跳过自动配置")
            return True
        
        try:
            # 方案1：从app.database.connection导入引擎和SessionLocal
            try:
                from app.database.connection import engine, SessionLocal
                self.engine = engine
                self.SessionLocal = SessionLocal
                logger.info("自动配置：从app.database.connection获取引擎和SessionLocal成功")
                return True
            except (ImportError, AttributeError) as e:
                logger.warning(f"无法从app.database.connection导入: {e}")
            
            # 方案2：从环境变量获取数据库URL
            import os
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                engine = create_engine(database_url)
                self.set_database_engine(engine)
                logger.info("自动配置：从环境变量DATABASE_URL获取引擎成功")
                return True
            
            # 方案3：尝试使用默认的MySQL数据库（从connection.py中的默认值）
            default_url = "mysql+pymysql://root:Zhuqing5201314@localhost:3306/auto_mate"
            try:
                engine = create_engine(default_url)
                self.set_database_engine(engine)
                logger.info(f"自动配置：使用默认MySQL数据库成功")
                return True
            except Exception as mysql_error:
                logger.warning(f"MySQL连接失败: {mysql_error}")
            
            # 方案4：使用SQLite作为最后的备选
            sqlite_url = "sqlite:///./app.db"
            engine = create_engine(sqlite_url)
            self.set_database_engine(engine)
            logger.info(f"自动配置：使用SQLite数据库 {sqlite_url}")
            return True
            
        except Exception as e:
            logger.error(f"自动配置数据库失败: {e}")
            return False
    
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
        """
        创建课程并异步生成关卡
        
        Args:
            db: 数据库会话
            course_data: 课程创建数据
            
        Returns:
            CourseResponse: 课程响应，包含"正在生成关卡"的状态信息
        """
        # 开启事务
        try:
            # 创建课程对象
            new_course = Course(
                title=course_data.title,
                tag=course_data.tag,
                description=course_data.description,
                git_url=course_data.git_url,
                is_completed=False  # 设置为未完成，表示正在生成
            )
            
            # 保存到数据库
            db.add(new_course)
            db.commit()
            db.refresh(new_course)
            
            logger.info(f"成功创建课程: {new_course.id} - {new_course.title}")
            
            # 确保数据库已配置用于异步任务
            if not self.SessionLocal:
                logger.info("检测到数据库未配置，尝试自动配置...")
                self.auto_configure_database()
            
            # 异步生成关卡（错误不中断主流程）
            self._start_async_level_generation(new_course.id, course_data.git_url, db)
            
            # 返回课程信息，告知用户正在生成
            course_dict = new_course.to_dict_with_levels()
            course_dict['message'] = "课程创建成功，关卡正在生成中，请稍后刷新查看"
            course_dict['generation_status'] = "generating"
            
            return CourseResponse(**course_dict)
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"创建课程失败: {e}")
            raise Exception(f"数据库操作失败: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"创建课程异常: {e}")
            raise Exception(f"创建课程失败: {str(e)}")
    
    def _start_async_level_generation(self, course_id: int, git_url: str, db_session: Session = None):
        """
        启动异步关卡生成任务
        
        Args:
            course_id: 课程ID
            git_url: Git仓库URL
            db_session: 当前数据库会话（用于获取引擎信息）
        """
        def run_generation():
            async_db = None
            try:
                # 创建新的数据库会话用于异步任务
                async_db = self._create_async_db_session(db_session)
                
                if async_db:
                    logger.info(f"成功创建异步数据库会话，开始生成课程 {course_id} 的关卡")
                    
                    try:
                        self._generate_levels_for_course(async_db, course_id, git_url)
                        
                        # 更新课程状态为完成
                        course = async_db.query(Course).filter(Course.id == course_id).first()
                        if course:
                            course.is_completed = True
                            async_db.commit()
                            logger.info(f"课程 {course_id} 关卡生成完成")
                        
                    except Exception as e:
                        # 保持课程状态为未完成，表示生成失败
                        try:
                            async_db.rollback()
                            course = async_db.query(Course).filter(Course.id == course_id).first()
                            if course:
                                course.is_completed = False
                                async_db.commit()
                        except Exception as rollback_error:
                            logger.error(f"回滚失败: {rollback_error}")
                        logger.error(f"异步生成关卡失败: {e}")
                        
                else:
                    logger.error("无法创建数据库会话，跳过异步关卡生成")
                    
            except Exception as e:
                logger.error(f"异步任务执行失败: {e}")
            finally:
                if async_db:
                    try:
                        async_db.close()
                    except Exception as close_error:
                        logger.error(f"关闭数据库会话失败: {close_error}")
        
        # 在新线程中执行生成任务
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
        logger.info(f"已启动课程 {course_id} 的异步关卡生成任务")
    
    def _create_async_db_session(self, db_session: Session = None) -> Session:
        """
        创建异步任务用的数据库会话
        
        Args:
            db_session: 当前数据库会话（用于获取引擎信息）
            
        Returns:
            Session: 新的数据库会话，如果创建失败则返回None
        """
        try:
            # 方案1：使用预配置的SessionLocal
            if self.SessionLocal:
                session = self.SessionLocal()
                logger.info("使用预配置的SessionLocal创建会话")
                return session
            
            # 方案2：从当前会话获取引擎信息
            if db_session and hasattr(db_session, 'bind'):
                from sqlalchemy.orm import sessionmaker
                AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)
                session = AsyncSessionLocal()
                logger.info("从当前会话的bind创建新会话")
                return session
            
            # 方案3：尝试从app.database.connection导入
            try:
                from app.database.connection import SessionLocal
                session = SessionLocal()
                logger.info("从app.database.connection.SessionLocal创建会话")
                return session
            except (ImportError, AttributeError) as e:
                logger.warning(f"无法从app.database.connection导入SessionLocal: {e}")
            
            # 方案4：尝试从app.database.connection导入engine
            try:
                from app.database.connection import engine
                from sqlalchemy.orm import sessionmaker
                AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                session = AsyncSessionLocal()
                logger.info("从app.database.connection.engine创建会话")
                return session
            except (ImportError, AttributeError) as e:
                logger.warning(f"无法从app.database.connection导入engine: {e}")
            
            logger.error("所有创建数据库会话的方案都失败了")
            return None
            
        except Exception as e:
            logger.error(f"创建异步数据库会话失败: {e}")
            return None
    
    def test_database_connection(self) -> bool:
        """
        测试数据库连接是否正常
        
        Returns:
            bool: 连接是否成功
        """
        try:
            test_session = self._create_async_db_session()
            if test_session:
                # 尝试执行一个简单的查询
                from sqlalchemy import text
                test_session.execute(text("SELECT 1"))
                test_session.close()
                logger.info("数据库连接测试成功")
                return True
            else:
                logger.error("无法创建测试数据库会话")
                return False
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_course_generation_status(self, db: Session, course_id: int) -> dict:
        """
        获取课程关卡生成状态
        
        Args:
            db: 数据库会话
            course_id: 课程ID
            
        Returns:
            dict: 包含生成状态的字典
        """
        try:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return {"error": "课程不存在"}
            
            level_count = len(course.levels)
            
            if course.is_completed:
                status = "completed"
                message = f"关卡生成完成，共生成 {level_count} 个关卡"
            elif level_count == 0:
                status = "generating"
                message = "关卡正在生成中，请稍后刷新查看"
            else:
                status = "generating"
                message = f"关卡生成中，已生成 {level_count} 个关卡"
            
            return {
                "course_id": course_id,
                "status": status,
                "message": message,
                "level_count": level_count,
                "is_completed": course.is_completed
            }
            
        except Exception as e:
            logger.error(f"获取课程生成状态失败: {e}")
            return {"error": f"获取状态失败: {str(e)}"}

    
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
    
    def _generate_levels_for_course(self, db: Session, course_id: int, git_url: str):
        """
        为课程生成关卡
        
        Args:
            db: 数据库会话
            course_id: 课程ID
            git_url: Git仓库URL
        """
        tmpdirname = None
        try:
            logger.info(f"开始为课程 {course_id} 生成关卡，Git URL: {git_url}")
            
            # 验证课程是否存在
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise Exception(f"课程 {course_id} 不存在")
            
            # 克隆仓库
            repo_url = git_url
            tmpdirname = tempfile.mkdtemp()
            repo = clone_repository(repo_url, tmpdirname)
            commits = list(repo.iter_commits(reverse=True))
            
            logger.info(f"成功克隆仓库，共找到 {len(commits)} 个提交")
            
            # 生成关卡
            generated_count = 0
            for i in range(2, len(commits) + 1):
                try:
                    logger.info(f"正在生成第 {i-1} 个关卡 (提交 {i}/{len(commits)})")
                    
                    shared = {
                        "fullcommits": commits,
                        "currentIndex": i,
                        "language": "中文",
                        "use_cache": True,
                        "max_abstraction_num": 5,
                        "project_name": repo_url, 
                        "repo": repo,
                        "tmpdirname": tmpdirname,
                    }
                    
                    reset_to_commit(repo, commits, i)
                    flow = create_flow()
                    flow.run(shared)
                    
                    if shared.get("res") and len(shared["res"]) > 0:
                        level_data = shared["res"][0]
                        
                        # 创建关卡对象
                        new_level = Level(
                            course_id=course.id,
                            title=level_data.get("name", f"关卡 {i-1}"),
                            description=level_data.get("description", ""),
                            requirements=level_data.get("requirements", ""),
                            order_number=i-1,
                        )
                        
                        # 保存到数据库（使用事务）
                        db.add(new_level)
                        db.commit()
                        db.refresh(new_level)
                        
                        generated_count += 1
                        logger.info(f'成功生成关卡: {new_level.title} (第 {generated_count} 个)')
                        
                    else:
                        logger.warning(f"第 {i} 个提交未能生成有效的关卡数据")
                        
                except Exception as level_error:
                    logger.error(f"生成第 {i} 个关卡时出错: {level_error}")
                    # 继续处理下一个关卡，不中断整个流程
                    db.rollback()
                    continue
            
            logger.info(f'课程 {course_id} 关卡生成完成，共生成 {generated_count} 个关卡')
            
        except Exception as e:
            logger.error(f"为课程 {course_id} 生成关卡时出错: {e}")
            db.rollback()
            raise e
            
        finally:
            # 清理临时目录
            if tmpdirname:
                try:
                    import shutil
                    shutil.rmtree(tmpdirname)
                    logger.info("已清理临时目录")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时目录失败: {cleanup_error}")
    


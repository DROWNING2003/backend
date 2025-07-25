"""
API路由模块
"""

from .courses import router as courses_router
from .levels import router as levels_router

__all__ = ["courses_router", "levels_router"]

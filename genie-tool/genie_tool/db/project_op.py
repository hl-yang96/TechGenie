# -*- coding: utf-8 -*-
# =====================
# Project Database Operations
# 
# Author: AI Assistant
# Date: 2025/7/30
# =====================
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from genie_tool.db.db_engine import async_session_local
from genie_tool.db.project_table import Project

logger = logging.getLogger(__name__)


class ProjectOp:
    """项目数据库操作类"""

    @classmethod
    async def create_project(
        cls,
        name: str,
        path: str,
        description: Optional[str] = None
    ) -> Project:
        """
        创建新项目记录
        
        Args:
            name: 项目名称
            path: 项目绝对路径
            description: 项目描述
            
        Returns:
            Project: 创建的项目对象
            
        Raises:
            IntegrityError: 如果项目名称或路径已存在
        """
        try:
            project = Project(
                name=name,
                path=path,
                description=description
            )
            
            async with async_session_local() as session:
                session.add(project)
                await session.commit()
                await session.refresh(project)
            
            logger.info(f"Created project: {name} at {path}")
            return project
            
        except IntegrityError as e:
            logger.error(f"Failed to create project {name}: {e}")
            raise

    @classmethod
    async def list_projects(
        cls,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Project]:
        """
        获取项目列表
        
        Args:
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            List[Project]: 项目列表
        """
        try:
            async with async_session_local() as session:
                query = select(Project).order_by(Project.created_at.desc())
                
                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                projects = result.scalars().all()
                
            logger.info(f"Retrieved {len(projects)} projects")
            return list(projects)
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise

    @classmethod
    async def get_project_by_id(cls, project_id: int) -> Optional[Project]:
        """
        根据ID获取项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Project]: 项目对象或None
        """
        try:
            async with async_session_local() as session:
                query = select(Project).where(Project.id == project_id)
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
            if project:
                logger.info(f"Retrieved project: {project.name}")
            else:
                logger.warning(f"Project not found: {project_id}")
                
            return project
            
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise

    @classmethod
    async def delete_project(cls, project_id: int) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            async with async_session_local() as session:
                query = delete(Project).where(Project.id == project_id)
                result = await session.execute(query)
                await session.commit()
                
                deleted_count = result.rowcount
                
            if deleted_count > 0:
                logger.info(f"Deleted project: {project_id}")
                return True
            else:
                logger.warning(f"Project not found for deletion: {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            raise

    @classmethod
    async def count_projects(cls) -> int:
        """
        获取项目总数
        
        Returns:
            int: 项目总数
        """
        try:
            async with async_session_local() as session:
                from sqlalchemy import func
                query = select(func.count(Project.id))
                result = await session.execute(query)
                count = result.scalar()
                
            logger.info(f"Total projects count: {count}")
            return count or 0
            
        except Exception as e:
            logger.error(f"Failed to count projects: {e}")
            raise

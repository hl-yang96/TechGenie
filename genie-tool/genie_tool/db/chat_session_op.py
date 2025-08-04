# -*- coding: utf-8 -*-
# =====================
# Chat Session Database Operations
# 
# Author: AI Assistant
# Date: 2025/8/4
# =====================
import json
import os
import shutil
from datetime import datetime
from typing import Optional, List

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, select, delete

from .db_engine import async_session_local
from .chat_session_table import ChatSession


class ChatSessionOp:
    """聊天会话数据库操作类"""

    @classmethod
    async def create_session(
        cls,
        req_id: str,
        data: Optional[dict] = None
    ) -> ChatSession:
        """
        创建新的聊天会话记录
        
        Args:
            req_id: 请求ID
            data: 会话数据字典
            
        Returns:
            ChatSession: 创建的会话对象
            
        Raises:
            IntegrityError: 如果req_id已存在
        """
        try:
            session = ChatSession(
                req_id=req_id,
                data=json.dumps(data) if data else None
            )
            
            async with async_session_local() as db_session:
                db_session.add(session)
                await db_session.commit()
                await db_session.refresh(session)
            
            logger.info(f"Created chat session: {req_id}")
            return session
            
        except IntegrityError as e:
            logger.error(f"Failed to create chat session {req_id}: {e}")
            raise

    @classmethod
    async def get_session_by_req_id(cls, req_id: str) -> Optional[ChatSession]:
        """
        根据请求ID获取聊天会话

        Args:
            req_id: 请求ID

        Returns:
            ChatSession: 会话对象，如果不存在则返回None
        """
        try:
            async with async_session_local() as session:
                stmt = select(ChatSession).where(ChatSession.req_id == req_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get chat session {req_id}: {e}")
            return None

    @classmethod
    async def update_session_data(
        cls,
        req_id: str,
        data: dict
    ) -> bool:
        """
        更新聊天会话数据
        
        Args:
            req_id: 请求ID
            data: 新的会话数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            async with async_session_local() as session:
                stmt = (
                    update(ChatSession)
                    .where(ChatSession.req_id == req_id)
                    .values(
                        data=json.dumps(data),
                        updated_at=datetime.utcnow()
                    )
                )
                result = await session.execute(stmt)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Updated chat session: {req_id}")
                    return True
                else:
                    logger.warning(f"Chat session not found: {req_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update chat session {req_id}: {e}")
            return False

    @classmethod
    async def get_session_data(cls, req_id: str) -> Optional[dict]:
        """
        获取聊天会话数据
        
        Args:
            req_id: 请求ID
            
        Returns:
            dict: 会话数据字典，如果不存在则返回None
        """
        session = await cls.get_session_by_req_id(req_id)
        if session and session.data:
            try:
                return json.loads(session.data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse session data for {req_id}: {e}")
                return None
        return None

    @classmethod
    async def list_sessions(
        cls,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ChatSession]:
        """
        获取聊天会话列表

        Args:
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            List[ChatSession]: 会话列表，按创建时间倒序排列
        """
        try:
            async with async_session_local() as session:
                query = select(ChatSession).order_by(ChatSession.created_at.desc())

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                result = await session.execute(query)
                sessions = result.scalars().all()

            logger.info(f"Retrieved {len(sessions)} chat sessions")
            return list(sessions)

        except Exception as e:
            logger.error(f"Failed to list chat sessions: {e}")
            raise

    @classmethod
    async def count_sessions(cls) -> int:
        """
        获取聊天会话总数

        Returns:
            int: 会话总数
        """
        try:
            from sqlalchemy import func
            async with async_session_local() as session:
                stmt = select(func.count(ChatSession.id))
                result = await session.execute(stmt)
                count = result.scalar()

            logger.info(f"Total chat sessions count: {count}")
            return count or 0

        except Exception as e:
            logger.error(f"Failed to count chat sessions: {e}")
            return 0

    @classmethod
    async def delete_session(cls, req_id: str) -> bool:
        """
        删除聊天会话及其相关文件

        Args:
            req_id: 请求ID

        Returns:
            bool: 删除是否成功
        """
        try:
            async with async_session_local() as session:
                # 首先查询会话是否存在
                stmt = select(ChatSession).where(ChatSession.req_id == req_id)
                result = await session.execute(stmt)
                chat_session = result.scalar_one_or_none()

                if not chat_session:
                    logger.warning(f"Chat session {req_id} not found")
                    return False

                # 删除数据库记录
                delete_stmt = delete(ChatSession).where(ChatSession.req_id == req_id)
                await session.execute(delete_stmt)
                await session.commit()

                logger.info(f"Chat session {req_id} deleted from database")

                # 删除文件目录
                cls._delete_session_files(req_id)

                return True

        except Exception as e:
            logger.error(f"Failed to delete chat session {req_id}: {e}")
            return False

    @classmethod
    def _delete_session_files(cls, req_id: str):
        """
        删除会话相关的文件目录

        Args:
            req_id: 请求ID
        """
        try:
            # 构建文件目录路径
            file_db_dir = os.path.join(os.path.dirname(__file__), "..", "..", "file_db_dir")
            session_dir = os.path.join(file_db_dir, req_id)

            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                logger.info(f"Deleted session files directory: {session_dir}")
            else:
                logger.info(f"Session files directory not found: {session_dir}")

        except Exception as e:
            logger.error(f"Failed to delete session files for {req_id}: {e}")

    @classmethod
    async def check_session_has_files(cls, req_id: str) -> bool:
        """
        检查会话是否有文件

        Args:
            req_id: 请求ID

        Returns:
            bool: 是否有文件
        """
        try:
            # 构建文件目录路径
            file_db_dir = os.path.join(os.path.dirname(__file__), "..", "..", "file_db_dir")
            session_dir = os.path.join(file_db_dir, req_id)

            if os.path.exists(session_dir):
                # 检查目录是否为空
                files = os.listdir(session_dir)
                return len(files) > 0

            return False

        except Exception as e:
            logger.error(f"Failed to check files for session {req_id}: {e}")
            return False

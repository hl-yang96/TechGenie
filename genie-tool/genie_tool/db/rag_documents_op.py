# -*- coding: utf-8 -*-
# =====================
# RAG Documents Table Operations
# 
# Author: AI Assistant
# Date: 2025/7/29
# =====================
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlmodel import select, update
from sqlalchemy import text

from genie_tool.db.rag_documents_table import RagDocument
from genie_tool.db.db_engine import async_session_local
from genie_tool.util.log_util import timer
from loguru import logger


class RagDocumentOp:
    """RAG 文档数据库操作类"""

    @staticmethod
    def generate_unique_filename(base_filename: str, target_dir: str) -> str:
        """
        生成唯一的文件名，处理同名文件的情况
        
        Args:
            base_filename: 基础文件名
            target_dir: 目标目录
            
        Returns:
            唯一的文件名
        """
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 分离文件名和扩展名
        name_parts = Path(base_filename).stem, Path(base_filename).suffix
        base_name, extension = name_parts
        
        # 检查文件是否存在
        counter = 0
        final_filename = base_filename
        
        while (target_path / final_filename).exists():
            counter += 1
            final_filename = f"{base_name}_{counter}{extension}"
        
        return final_filename

    @classmethod
    @timer()
    async def create_document(
        cls,
        filename: str,
        file_path: str,
        collection_type: str,
        file_size: Optional[int] = None,
        file_description: Optional[str] = None,
        file_abstract: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> RagDocument:
        """
        创建新的 RAG 文档记录

        Args:
            filename: 文件名
            file_path: 文件路径
            collection_type: 集合类型
            file_size: 文件大小
            file_description: 文件描述
            file_abstract: 文件摘要
            document_id: 文档ID（可选，不提供则自动生成）

        Returns:
            创建的 RagDocument 对象
        """
        if document_id is None:
            document_id = str(uuid.uuid4())

        # 获取文件大小（如果未提供）
        if file_size is None and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        rag_document = RagDocument(
            id=document_id,
            filename=filename,
            file_path=file_path,
            collection_type=collection_type,
            file_size=file_size,
            file_description=file_description,
            file_abstract=file_abstract
        )
        
        async with async_session_local() as session:
            session.add(rag_document)
            await session.commit()
            await session.refresh(rag_document)
        
        logger.info(f"Created RAG document record: {document_id}")
        return rag_document

    @classmethod
    @timer()
    async def get_by_id(cls, document_id: str) -> Optional[RagDocument]:
        """根据文档ID获取文档记录"""
        async with async_session_local() as session:
            statement = select(RagDocument).where(RagDocument.id == document_id)
            result = await session.execute(statement)
            return result.scalars().one_or_none()

    @classmethod
    @timer()
    async def get_by_filename(cls, filename: str) -> List[RagDocument]:
        """根据文件名获取文档记录列表"""
        async with async_session_local() as session:
            statement = select(RagDocument).where(RagDocument.filename == filename)
            result = await session.execute(statement)
            return result.scalars().all()

    @classmethod
    @timer()
    async def get_by_collection_type(cls, collection_type: str) -> List[RagDocument]:
        """根据集合类型获取文档记录列表"""
        async with async_session_local() as session:
            statement = select(RagDocument).where(RagDocument.collection_type == collection_type)
            result = await session.execute(statement)
            return result.scalars().all()

    @classmethod
    @timer()
    async def get_all(cls) -> List[RagDocument]:
        """获取所有文档记录"""
        async with async_session_local() as session:
            statement = select(RagDocument)
            result = await session.execute(statement)
            return result.scalars().all()

    @classmethod
    @timer()
    async def update_document(
        cls,
        document_id: str,
        **kwargs
    ) -> Optional[RagDocument]:
        """
        更新文档记录

        Args:
            document_id: 文档ID
            **kwargs: 要更新的字段

        Returns:
            更新后的文档记录
        """
        async with async_session_local() as session:
            # 添加更新时间
            kwargs['updated_at'] = datetime.now()

            statement = (
                update(RagDocument)
                .where(RagDocument.id == document_id)
                .values(**kwargs)
            )
            await session.execute(statement)
            await session.commit()

        return await cls.get_by_id(document_id)

    @classmethod
    @timer()
    async def delete_by_id(cls, document_id: str) -> bool:
        """根据文档ID删除文档记录"""
        async with async_session_local() as session:
            statement = select(RagDocument).where(RagDocument.id == document_id)
            result = await session.execute(statement)
            document = result.scalars().one_or_none()
            
            if document:
                await session.delete(document)
                await session.commit()
                logger.info(f"Deleted RAG document record: {document_id}")
                return True
            return False

    @classmethod
    @timer()
    async def delete_by_collection_type(cls, collection_type: str) -> int:
        """根据集合类型删除文档记录"""
        async with async_session_local() as session:
            statement = select(RagDocument).where(RagDocument.collection_type == collection_type)
            result = await session.execute(statement)
            documents = result.scalars().all()
            
            count = 0
            for document in documents:
                await session.delete(document)
                count += 1
            
            await session.commit()
            logger.info(f"Deleted {count} RAG document records for collection: {collection_type}")
            return count



    @classmethod
    @timer()
    async def get_statistics(cls) -> Dict[str, Any]:
        """获取 RAG 文档统计信息"""
        async with async_session_local() as session:
            # 总文档数
            total_count_stmt = select(RagDocument)
            total_result = await session.execute(total_count_stmt)
            total_count = len(total_result.scalars().all())
            
            # 按集合类型统计
            collection_stats_stmt = text("""
                SELECT collection_type, COUNT(*) as count, SUM(file_size) as total_size
                FROM rag_documents 
                GROUP BY collection_type
            """)
            collection_result = await session.execute(collection_stats_stmt)
            collection_stats = {}
            
            for row in collection_result:
                collection_stats[row.collection_type] = {
                    "count": row.count,
                    "total_size": row.total_size or 0
                }
            
            return {
                "total_documents": total_count,
                "collection_statistics": collection_stats
            }

    @classmethod
    @timer()
    async def search_documents(
        cls,
        filename_pattern: Optional[str] = None,
        collection_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RagDocument]:
        """
        搜索文档记录

        Args:
            filename_pattern: 文件名模式（支持LIKE查询）
            collection_type: 集合类型
            limit: 结果限制数量
            offset: 偏移量

        Returns:
            匹配的文档记录列表
        """
        async with async_session_local() as session:
            statement = select(RagDocument)

            if filename_pattern:
                statement = statement.where(RagDocument.filename.like(f"%{filename_pattern}%"))

            if collection_type:
                statement = statement.where(RagDocument.collection_type == collection_type)

            statement = statement.offset(offset).limit(limit)

            result = await session.execute(statement)
            return result.scalars().all()

    @classmethod
    @timer()
    async def count_documents(
        cls,
        filename_pattern: Optional[str] = None,
        collection_type: Optional[str] = None
    ) -> int:
        """
        统计文档记录数量

        Args:
            filename_pattern: 文件名模式（支持LIKE查询）
            collection_type: 集合类型

        Returns:
            匹配的文档记录数量
        """
        async with async_session_local() as session:
            statement = select(RagDocument)

            if filename_pattern:
                statement = statement.where(RagDocument.filename.like(f"%{filename_pattern}%"))

            if collection_type:
                statement = statement.where(RagDocument.collection_type == collection_type)

            result = await session.execute(statement)
            return len(result.scalars().all())

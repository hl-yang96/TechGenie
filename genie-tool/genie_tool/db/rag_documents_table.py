# -*- coding: utf-8 -*-
# =====================
# RAG Documents Table Model
# 
# Author: AI Assistant
# Date: 2025/7/29
# =====================
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, text
from sqlmodel import SQLModel, Field


class RagDocument(SQLModel, table=True):
    """RAG 文档表模型"""
    __tablename__ = "rag_documents"

    id: str = Field(primary_key=True, description="文档唯一标识符")
    filename: str = Field(description="文件名")
    file_path: str = Field(description="文件路径")
    collection_type: str = Field(description="集合类型")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    file_description: Optional[str] = Field(default=None, description="文件描述")
    file_abstract: Optional[str] = Field(default=None, description="文件摘要")
    created_at: Optional[datetime] = Field(
        sa_type=DateTime, 
        default=None, 
        nullable=False,  
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        sa_type=DateTime, 
        default=None, 
        nullable=False,  
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="更新时间"
    )

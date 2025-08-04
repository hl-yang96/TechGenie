# -*- coding: utf-8 -*-
# =====================
# Chat Session Table Model
# 
# Author: AI Assistant
# Date: 2025/8/4
# =====================
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, text
from sqlmodel import SQLModel, Field


class ChatSession(SQLModel, table=True):
    """聊天会话表模型"""
    __tablename__ = "chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True, description="会话唯一标识符")
    req_id: str = Field(unique=True, description="请求ID，来自SSE响应")
    data: Optional[str] = Field(default=None, description="会话数据，JSON格式存储")
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

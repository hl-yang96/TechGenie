# -*- coding: utf-8 -*-
# =====================
# Project Table Model
# 
# Author: AI Assistant
# Date: 2025/7/30
# =====================
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, text
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    """项目代码库表模型"""
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True, description="项目唯一标识符")
    name: str = Field(description="项目名称")
    path: str = Field(description="项目绝对路径")
    description: Optional[str] = Field(default=None, max_length=50, description="项目描述(50字以内)")
    created_at: Optional[datetime] = Field(
        sa_type=DateTime, 
        default=None, 
        nullable=False,  
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        description="创建时间"
    )

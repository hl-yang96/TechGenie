# -*- coding: utf-8 -*-
# =====================
# Project Manager API
# 
# Author: AI Assistant
# Date: 2025/7/30
# =====================
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from genie_tool.db.project_op import ProjectOp
from genie_tool.util.middleware_util import RequestHandlerRoute
from genie_tool.tool.project_explain import project_explain_async


logger = logging.getLogger(__name__)

router = APIRouter(route_class=RequestHandlerRoute)


# Request Models
class ProjectCreateRequest(BaseModel):
    """创建项目请求模型"""
    name: str = Field(..., description="项目名称", min_length=1, max_length=100)
    path: str = Field(..., description="项目绝对路径", min_length=1)
    description: Optional[str] = Field(None, description="项目描述", max_length=1000)

    @validator('path')
    def validate_path(cls, v):
        """验证路径格式"""
        if not v.strip():
            raise ValueError('项目路径不能为空')
        
        # 检查是否为绝对路径
        path_obj = Path(v)
        if not path_obj.is_absolute():
            raise ValueError('必须提供绝对路径')
        
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        """验证项目名称"""
        if not v.strip():
            raise ValueError('项目名称不能为空')
        return v.strip()


class ProjectListRequest(BaseModel):
    """获取项目列表请求模型"""
    limit: Optional[int] = Field(None, description="限制返回数量", ge=1, le=100)
    offset: Optional[int] = Field(None, description="偏移量", ge=0)


class ProjectDeleteRequest(BaseModel):
    """删除项目请求模型"""
    project_id: int = Field(..., description="项目ID", gt=0)


# Response Models
class ProjectInfo(BaseModel):
    """项目信息模型"""
    id: int
    name: str
    path: str
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ProjectCreateResponse(BaseModel):
    """创建项目响应模型"""
    success: bool
    message: str
    project: Optional[ProjectInfo] = None


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    success: bool
    message: str
    projects: List[ProjectInfo] = []
    total: int = 0


class ProjectDeleteResponse(BaseModel):
    """删除项目响应模型"""
    success: bool
    message: str


# API Endpoints
@router.post("/create", response_model=ProjectCreateResponse)
async def create_project(request: ProjectCreateRequest):
    """
    创建新项目
    """
    try:
        user_description = request.description or ""
        result = await project_explain_async(
            path=request.path,
            question=f"\n用户给出的项目描述：{user_description}\n\n请参考用户给出的描述，并结合项目文档与代码，全面分析这个项目的架构/技术栈/主要功能，给出一个200字的项目概述，直接输出概述内容，不要创建任何文档。"
        )
        
        # 组合描述信息
        combined_description = f"### 用户描述: \n{user_description}\n### 代码分析助手:\n{result.strip()}"

        # 创建项目
        name_without_spaces = request.name.strip().replace(" ", "_")
        project = await ProjectOp.create_project(
            name=name_without_spaces,
            path=request.path,
            description=combined_description
        )
        
        # 转换为响应格式
        project_info = ProjectInfo(
            id=project.id,
            name=project.name,
            path=project.path,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else ""
        )
        
        return ProjectCreateResponse(
            success=True,
            message="项目创建成功",
            project=project_info
        )
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return ProjectCreateResponse(
            success=False,
            message=f"创建项目失败: {str(e)}"
        )


@router.post("/list", response_model=ProjectListResponse)
async def list_projects(request: ProjectListRequest):
    """
    获取项目列表
    """
    try:
        # 获取项目列表
        projects = await ProjectOp.list_projects(
            limit=request.limit,
            offset=request.offset
        )
        
        # 获取总数
        total = await ProjectOp.count_projects()
        
        # 转换为响应格式
        project_infos = [
            ProjectInfo(
                id=project.id,
                name=project.name,
                path=project.path,
                description=project.description,
                created_at=project.created_at.isoformat() if project.created_at else ""
            )
            for project in projects
        ]
        
        return ProjectListResponse(
            success=True,
            message="获取项目列表成功",
            projects=project_infos,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return ProjectListResponse(
            success=False,
            message=f"获取项目列表失败: {str(e)}"
        )


@router.post("/delete", response_model=ProjectDeleteResponse)
async def delete_project(request: ProjectDeleteRequest):
    """
    删除项目
    """
    try:
        # 删除项目
        success = await ProjectOp.delete_project(request.project_id)
        
        if success:
            return ProjectDeleteResponse(
                success=True,
                message="项目删除成功"
            )
        else:
            return ProjectDeleteResponse(
                success=False,
                message="项目不存在或已被删除"
            )
        
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return ProjectDeleteResponse(
            success=False,
            message=f"删除项目失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    try:
        # 简单的数据库连接检查
        count = await ProjectOp.count_projects()
        
        return JSONResponse(content={
            "status": "healthy",
            "total_projects": count
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

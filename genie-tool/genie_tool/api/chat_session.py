# -*- coding: utf-8 -*-
# =====================
# Chat Session API
# 
# Author: AI Assistant
# Date: 2025/8/4
# =====================
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from genie_tool.db.chat_session_op import ChatSessionOp
from genie_tool.util.middleware_util import RequestHandlerRoute


router = APIRouter(route_class=RequestHandlerRoute)


# Request Models
class ChatSessionCreateRequest(BaseModel):
    """创建聊天会话请求模型"""
    req_id: str = Field(..., alias="reqId", description="请求ID")
    data: Optional[Dict[str, Any]] = Field(None, description="会话数据")


class ChatSessionUpdateRequest(BaseModel):
    """更新聊天会话请求模型"""
    req_id: str = Field(..., alias="reqId", description="请求ID")
    data: Dict[str, Any] = Field(..., description="会话数据")


class ChatSessionGetRequest(BaseModel):
    """获取聊天会话请求模型"""
    req_id: str = Field(..., alias="reqId", description="请求ID")


class ChatSessionListRequest(BaseModel):
    """获取聊天会话列表请求模型"""
    limit: Optional[int] = Field(50, description="限制返回数量，默认50")
    offset: Optional[int] = Field(0, description="偏移量，默认0")


class ChatSessionDeleteRequest(BaseModel):
    """删除聊天会话请求模型"""
    req_id: str = Field(..., alias="reqId", description="请求ID")


# Response Models
class ChatSessionResponse(BaseModel):
    """聊天会话响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ChatSessionInfo(BaseModel):
    """聊天会话信息模型"""
    req_id: str = Field(..., alias="reqId", description="请求ID")
    chat_title: Optional[str] = Field(None, alias="chatTitle", description="聊天标题")
    created_at: str = Field(..., alias="createdAt", description="创建时间")
    updated_at: Optional[str] = Field(None, alias="updatedAt", description="更新时间")


class ChatSessionListResponse(BaseModel):
    """聊天会话列表响应模型"""
    success: bool
    message: str
    sessions: List[ChatSessionInfo] = Field(default_factory=list, description="会话列表")
    total: int = Field(0, description="总数量")


class ChatSessionDeleteResponse(BaseModel):
    """删除聊天会话响应模型"""
    success: bool
    message: str


# API Endpoints
@router.post("/create", response_model=ChatSessionResponse)
async def create_chat_session(request: ChatSessionCreateRequest):
    """
    创建新的聊天会话
    """
    try:
        session = await ChatSessionOp.create_session(
            req_id=request.req_id,
            data=request.data
        )
        
        return ChatSessionResponse(
            success=True,
            message="Chat session created successfully",
            data={"req_id": session.req_id}
        )
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=409,
                detail=f"Chat session with req_id {request.req_id} already exists"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create chat session: {str(e)}"
            )


@router.post("/update", response_model=ChatSessionResponse)
async def update_chat_session(request: ChatSessionUpdateRequest):
    """
    更新聊天会话数据
    """
    try:
        success = await ChatSessionOp.update_session_data(
            req_id=request.req_id,
            data=request.data
        )
        
        if success:
            return ChatSessionResponse(
                success=True,
                message="Chat session updated successfully"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session with req_id {request.req_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update chat session: {str(e)}"
        )


@router.post("/get", response_model=ChatSessionResponse)
async def get_chat_session(request: ChatSessionGetRequest):
    """
    获取聊天会话数据
    """
    try:
        data = await ChatSessionOp.get_session_data(req_id=request.req_id)
        
        if data is not None:
            return ChatSessionResponse(
                success=True,
                message="Chat session retrieved successfully",
                data=data
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session with req_id {request.req_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat session: {str(e)}"
        )


@router.post("/list", response_model=ChatSessionListResponse)
async def list_chat_sessions(request: ChatSessionListRequest):
    """
    获取聊天会话列表
    """
    try:
        # 获取会话列表
        sessions = await ChatSessionOp.list_sessions(
            limit=request.limit,
            offset=request.offset
        )

        # 获取总数
        total = await ChatSessionOp.count_sessions()

        # 转换为响应格式
        session_infos = []
        for session in sessions:
            # 解析会话数据获取标题
            chat_title = None
            if session.data:
                try:
                    import json
                    data = json.loads(session.data)
                    # 优先使用chatTitle，如果没有则从chatList中提取第一个query
                    chat_title = data.get('chatTitle')
                    if not chat_title:
                        chat_list = data.get('chatList', [])
                        if chat_list and len(chat_list) > 0:
                            first_chat = chat_list[0]
                            chat_title = first_chat.get('query', '未命名对话')
                except json.JSONDecodeError:
                    pass

            # 如果还是没有标题，使用默认值
            if not chat_title:
                chat_title = '未命名对话'

            session_infos.append(
                ChatSessionInfo(
                    reqId=session.req_id,
                    chatTitle=chat_title,
                    createdAt=session.created_at.isoformat() if session.created_at else "",
                    updatedAt=session.updated_at.isoformat() if session.updated_at else None
                )
            )

        return ChatSessionListResponse(
            success=True,
            message="获取聊天会话列表成功",
            sessions=session_infos,
            total=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list chat sessions: {str(e)}"
        )


@router.post("/delete", response_model=ChatSessionDeleteResponse)
async def delete_chat_session(request: ChatSessionDeleteRequest):
    """
    删除聊天会话
    """
    try:
        req_id = request.req_id

        # 执行删除操作
        success = await ChatSessionOp.delete_session(req_id)

        if success:
            return ChatSessionDeleteResponse(
                success=True,
                message="聊天会话删除成功"
            )
        else:
            return ChatSessionDeleteResponse(
                success=False,
                message="聊天会话删除失败，会话不存在"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat session: {str(e)}"
        )

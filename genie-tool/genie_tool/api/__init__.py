# -*- coding: utf-8 -*-
# =====================
#
#
# Author: liumin.423
# Date:   2025/7/7
# =====================
from fastapi import APIRouter

from .tool import router as tool_router
from .file_manage import router as file_router
from .rag_manager import router as rag_router
from .project_manager import router as project_router
from .chat_session import router as chat_session_router

api_router = APIRouter(prefix="/v1")

api_router.include_router(tool_router, prefix="/tool", tags=["tool"])
api_router.include_router(file_router, prefix="/file_tool", tags=["file_manage"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag_manager"])
api_router.include_router(project_router, prefix="/project", tags=["project_manager"])
api_router.include_router(chat_session_router, prefix="/session", tags=["chat_session"])


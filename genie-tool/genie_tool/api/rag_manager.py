# -*- coding: utf-8 -*-
# =====================
# RAG Manager API
# 
# Author: AI Assistant
# Date: 2025/7/29
# =====================
import logging
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from genie_tool.rag.document_store import get_document_store
from genie_tool.util.middleware_util import RequestHandlerRoute
from genie_tool.db.rag_documents_op import RagDocumentOp

logger = logging.getLogger(__name__)

router = APIRouter(route_class=RequestHandlerRoute)

# Request/Response Models
class RAGIngestRequest(BaseModel):
    """文档摄取请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    document_path: Optional[str] = Field(default=None, alias="documentPath", description="文档路径")
    document_content: Optional[str] = Field(default=None, alias="documentContent", description="文档内容")
    collection_type: Optional[str] = Field(default=None, alias="collectionType", description="集合类型")

class RAGQueryRequest(BaseModel):
    """文档查询请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    query_text: str = Field(alias="queryText", description="查询文本")
    collection_types: Optional[List[str]] = Field(default=None, alias="collectionTypes", description="集合类型列表")
    top_k: int = Field(default=15, alias="topK", description="返回结果数量")
    min_score: float = Field(default=0.4, alias="minScore", description="最小相似度分数阈值")

class RAGDeleteRequest(BaseModel):
    """文档删除请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    collection_type: Optional[str] = Field(default=None, alias="collectionType", description="集合类型，为空则删除所有")

class RAGDeleteDocumentRequest(BaseModel):
    """删除单个文档请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    document_id: str = Field(alias="documentId", description="文档ID")

class RAGListRequest(BaseModel):
    """文档列表查询请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    collection_type: Optional[str] = Field(default=None, alias="collectionType", description="集合类型过滤")
    filename_pattern: Optional[str] = Field(default=None, alias="filenamePattern", description="文件名模式过滤")
    limit: int = Field(default=10, alias="limit", description="返回结果数量限制")
    offset: int = Field(default=0, alias="offset", description="偏移量")

class RAGContentRequest(BaseModel):
    """文档内容查询请求"""
    request_id: str = Field(alias="requestId", description="Request ID")
    document_id: str = Field(alias="documentId", description="文档ID")



# API Endpoints
@router.post("/ingest")
async def ingest_document(body: RAGIngestRequest):
    """Ingest documents from file path or text content with automatic classification."""
    import json
    from pathlib import Path

    try:
        store = get_document_store()

        # 0. Validate input - either document_path or content must be provided
        if not body.document_path and not body.document_content:
            raise HTTPException(status_code=400, detail="Either document_path or content must be provided")

        # 1. Comprehensive document ingestion (preprocessing + vector storage)
        logger.info("Starting document ingestion...")
        ingestion_result = await store.ingest_single_document(body.document_path, body.document_content)

        if not ingestion_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Document ingestion failed: {ingestion_result['error']}"
            )

        logger.info(f"Document ingestion completed successfully")

        # Extract results from ingestion
        document_id = ingestion_result["document_id"]
        final_filename = ingestion_result["final_filename"]
        file_description = ingestion_result["description"]
        file_abstract = ingestion_result["abstract"]
        file_path = ingestion_result["file_path"]
        collection_type = ingestion_result["collection_type"]
        file_size = ingestion_result["file_size"]
       
        classification_mode = "automatic LLM classification"

        return {
            "message": f"Successfully ingested document using {classification_mode}",
            "document_id": document_id,
            "filename": final_filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_description": file_description,
            "file_abstract": file_abstract,
            "collection_type": collection_type,
            "classification_mode": classification_mode,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")


@router.post("/query")
async def query_documents(body: RAGQueryRequest):
    """
    查询文档
    """
    try:
        logger.info(f"Starting query for request_id: {body.request_id}, query: {body.query_text}")

        document_store = get_document_store()

        # 检查系统状态
        if not document_store.chroma_client.is_connected():
            logger.error("ChromaDB is not connected")
            raise HTTPException(status_code=503, detail="ChromaDB service is not available")

        if not document_store.retrievers:
            logger.warning("No retrievers available, returning empty results")
            return JSONResponse(content={
                "success": True,
                "results": [],
                "totalResults": 0,
                "message": "No documents available for search. Please ingest documents first.",
                "requestId": body.request_id
            })

        logger.info(f"Available collections: {list(document_store.retrievers.keys())}")

        # 执行查询
        results = document_store.search_documents(
            query_text=body.query_text,
            collection_types=body.collection_types,
            top_k=body.top_k,
            min_score=body.min_score
        )

        logger.info(f"Query completed, found {len(results)} results")

        return JSONResponse(content={
            "success": True,
            "results": results,
            "totalResults": len(results),
            "requestId": body.request_id
        })

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in query_documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")



@router.post("/delete")
async def delete_collection(body: RAGDeleteRequest):
    """
    删除集合
    """
    try:
        document_store = get_document_store()

        # 执行删除
        success = await document_store.reset_collection(collection_type=body.collection_type)

        if success:
            message = f"Successfully deleted collection: {body.collection_type}" if body.collection_type else "Successfully deleted all collections"
            return JSONResponse(content={
                "success": True,
                "message": message,
                "requestId": body.request_id
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to delete collection")

    except Exception as e:
        logger.error(f"Error in delete_collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-document")
async def delete_document(body: RAGDeleteDocumentRequest):
    """
    删除单个文档
    """
    try:
        document_store = get_document_store()

        # 执行删除
        success = await document_store.delete_document(document_id=body.document_id)

        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Successfully deleted document: {body.document_id}",
                "requestId": body.request_id
            })
        else:
            raise HTTPException(status_code=404, detail="Document not found or failed to delete")

    except Exception as e:
        logger.error(f"Error in delete_document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_rag_status():
    """
    获取RAG系统状态
    """
    try:
        document_store = get_document_store()

        # 获取状态信息
        is_ready = document_store.is_ready()
        available_collections = document_store.get_available_collections()
        collection_stats = document_store.get_collection_stats()

        return JSONResponse(content={
            "success": True,
            "isReady": is_ready,
            "availableCollections": available_collections,
            "collectionStats": collection_stats,
        })

    except Exception as e:
        logger.error(f"Error in get_rag_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/list")
async def list_documents(body: RAGListRequest):
    """
    获取已上传的文档列表
    """
    try:
        # 获取总数
        total_count = await RagDocumentOp.count_documents(
            filename_pattern=body.filename_pattern,
            collection_type=body.collection_type
        )

        # 获取分页文档列表
        documents = await RagDocumentOp.search_documents(
            filename_pattern=body.filename_pattern,
            collection_type=body.collection_type,
            limit=body.limit,
            offset=body.offset
        )

        # 转换为响应格式
        document_list = []
        for doc in documents:
            document_list.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "collection_type": doc.collection_type,
                "file_size": doc.file_size,
                "file_description": doc.file_description,
                "file_abstract": doc.file_abstract,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            })

        return JSONResponse(content={
            "success": True,
            "documents": document_list,
            "total": total_count,
            "requestId": body.request_id
        })

    except Exception as e:
        logger.error(f"Error in list_documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.post("/content")
async def get_document_content(body: RAGContentRequest):
    """
    获取文档的原始内容
    """
    try:
        # 根据文档ID查询文档信息
        document = await RagDocumentOp.get_by_id(body.document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {body.document_id} not found")

        content = ""

        # 如果有文件路径，尝试读取文件内容
        if document.file_path:
            try:
                import aiofiles
                import os

                # 检查文件是否存在
                if os.path.exists(document.file_path):
                    async with aiofiles.open(document.file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                else:
                    # 文件不存在，返回文档摘要或描述
                    content = document.file_abstract or document.file_description or "文件不存在，无法读取内容"
            except Exception as e:
                logger.warning(f"Failed to read file {document.file_path}: {e}")
                # 读取文件失败，返回文档摘要或描述
                content = document.file_abstract or document.file_description or f"无法读取文件内容: {str(e)}"
        else:
            # 没有文件路径，返回文档摘要或描述
            content = document.file_abstract or document.file_description or "无内容可显示"

        return JSONResponse(content={
            "success": True,
            "document_id": document.id,
            "filename": document.filename,
            "content": content,
            "file_size": len(content.encode('utf-8')),
            "requestId": body.request_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document_content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document content: {str(e)}")

@router.get("/health")
async def health_check():
    """
    快速健康检查端点，不需要请求体
    """
    try:
        document_store = get_document_store()

        # 检查 ChromaDB 连接
        chroma_connected = document_store.chroma_client.is_connected()

        # 检查基本状态
        has_retrievers = len(document_store.retrievers) > 0
        has_indexes = len(document_store.indexes) > 0

        status = {
            "status": "healthy" if chroma_connected else "unhealthy",
            "chromadb_connected": chroma_connected,
            "has_retrievers": has_retrievers,
            "has_indexes": has_indexes,
            "retriever_count": len(document_store.retrievers),
            "index_count": len(document_store.indexes),
            "available_collections": list(document_store.retrievers.keys()) if has_retrievers else []
        }

        return JSONResponse(content=status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "chromadb_connected": False,
                "has_retrievers": False,
                "has_indexes": False
            },
            status_code=500
        )



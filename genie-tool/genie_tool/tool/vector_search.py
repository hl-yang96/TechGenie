# -*- coding: utf-8 -*-
# =====================
# Vector Search Tool
# 
# Author: AI Assistant
# Date: 2025/7/29
# =====================
from loguru import logger
from typing import List, Optional, Dict, Any

from genie_tool.rag.document_store import get_document_store


def vector_search(
    query_text: str,
    collection_types: Optional[List[str]] = None,
    top_k: int = 5,
    min_score: float = 0.4
) -> Dict[str, Any]:
    """
    向量搜索工具 - 在文档集合中进行语义相似度搜索
    
    Args:
        query_text: 搜索查询文本
        collection_types: 要搜索的集合类型列表，为空则搜索所有集合
        top_k: 返回结果数量，默认5
        min_score: 最小相似度分数阈值，默认0.4
    
    Returns:
        包含搜索结果的字典:
        - success: 是否成功
        - results: 搜索结果列表
        - total_results: 结果总数
        - message: 状态消息
        - error: 错误信息（如果有）
    """
    try:
        logger.info(f"Vector search started: query='{query_text}', top_k={top_k}, min_score={min_score}")
        
        # 获取文档存储实例
        document_store = get_document_store()
        
        # 检查系统状态
        if not document_store.chroma_client.is_connected():
            error_msg = "ChromaDB service is not available"
            logger.error(error_msg)
            return {
                "success": False,
                "results": [],
                "total_results": 0,
                "error": error_msg
            }
        
        if not document_store.retrievers:
            warning_msg = "No documents available for search. Please ingest documents first."
            logger.warning(warning_msg)
            return {
                "success": True,
                "results": [],
                "total_results": 0,
                "message": warning_msg
            }
        
        # 记录可用集合
        available_collections = list(document_store.retrievers.keys())
        logger.info(f"Available collections: {available_collections}")
        
        # 执行搜索
        results = document_store.search_documents(
            query_text=query_text,
            collection_types=collection_types,
            top_k=top_k,
            min_score=min_score
        )
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_result = {
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "collection_type": result.get("collection_type", "unknown"),
                "source": result.get("source", "unknown"),
                "metadata": result.get("metadata", {}),
                "rank": result.get("overall_rank", result.get("rank", 0))
            }
            formatted_results.append(formatted_result)
        
        success_msg = f"Found {len(formatted_results)} documents matching query"
        logger.info(f"Vector search completed: {success_msg}")
        
        return {
            "success": True,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "message": success_msg,
            "query": query_text,
            "collections_searched": collection_types or available_collections,
            "min_score_used": min_score
        }
        
    except Exception as e:
        error_msg = f"Vector search failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "results": [],
            "total_results": 0,
            "error": error_msg
        }

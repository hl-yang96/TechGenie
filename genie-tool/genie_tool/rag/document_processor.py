"""
Document Processor for RAG System
Purpose: LLM-based document preprocessing including classification, cleaning, renaming, and metadata generation
"""

import json
from loguru import logger
import os
from typing import Dict, Any

from genie_tool.util.prompt_util import get_prompt
from genie_tool.util.llm_util import ask_llm
from .config import (
    COLLECTION_CONFIGS,
    COLLECTION_RESUMES, COLLECTION_PROJECTS_EXPERIENCE, COLLECTION_JOB_POSTINGS,
    MAX_METADATA_FIELD_LENGTH, MAX_SUMMARY_LENGTH, MAX_KEYWORDS_COUNT
)


def _truncate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate metadata fields to prevent chunk size issues."""
    truncated = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            truncated[key] = value[:MAX_METADATA_FIELD_LENGTH]
        elif isinstance(value, list):
            truncated[key] = value[:MAX_KEYWORDS_COUNT]
        else:
            truncated[key] = value
    return truncated


class DocumentProcessor:
    """
    LLM-based document processor for comprehensive document preprocessing.
    """

    def __init__(self):
        """Initialize the document processor."""
        pass

    async def process_document(self, document_content: str, filename: str = None) -> Dict[str, Any]:
        """
        Process document with LLM-based preprocessing.

        Args:
            document_content: Raw document text content
            filename: Original filename (optional)

        Returns:
            Dictionary containing all preprocessing results
        """
        try:
            # Get prompt from yaml
            prompt_template = get_prompt("rag")["document_preprocessing_prompt"]

            # Prepare the prompt
            prompt = prompt_template.format(
                document_content=document_content,
                filename=filename or "未知"
            )

            # Get preprocessing results from LLM
            model = os.getenv("DEFAULT_MODEL", "gpt-4.1")

            # Collect response from async generator
            response_raw = ""
            async for chunk in ask_llm(prompt, model=model, stream=False, only_content=True):
                if chunk:
                    response_raw += str(chunk)

            # Parse JSON response
            try:
                response_json = response_raw[response_raw.find('{'):response_raw.rfind('}')+1]
                preprocessing_result = json.loads(response_json)

                # Validate the preprocessing result
                if self._validate_preprocessing_result(preprocessing_result):
                    # Truncate metadata to prevent chunk size issues
                    if 'metadata' in preprocessing_result:
                        preprocessing_result['metadata'] = _truncate_metadata(preprocessing_result['metadata'])

                    logger.info(f"Document processed successfully, collection type: {preprocessing_result.get('collection_type')}")
                    return preprocessing_result
                else:
                    logger.warning("Invalid preprocessing result, using fallback")
                    return self._get_fallback_result(document_content, filename)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                return self._get_fallback_result(document_content, filename)

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return self._get_fallback_result(document_content, filename)

    def _validate_preprocessing_result(self, result: Dict[str, Any]) -> bool:
        """Validate preprocessing result structure."""
        required_fields = ["renamed_filename", "description", "abstract", "cleaned_content", "collection_type"]
        
        for field in required_fields:
            if field not in result or not result[field]:
                logger.warning(f"Missing or empty required field: {field}")
                return False
        
        # Validate collection type
        if result["collection_type"] not in COLLECTION_CONFIGS:
            logger.warning(f"Invalid collection type: {result['collection_type']}")
            return False
            
        return True

    def _get_fallback_result(self, document_content: str, filename: str = None) -> Dict[str, Any]:
        """Generate fallback result when LLM processing fails."""
        return {
            "renamed_filename": filename or "未知文档",
            "description": "文档处理失败，使用默认描述",
            "abstract": document_content[:100] + "..." if len(document_content) > 100 else document_content,
            "cleaned_content": document_content,
            "collection_type": COLLECTION_PROJECTS_EXPERIENCE,
            "metadata": {}
        }


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()

"""
RAG Configuration Constants
Purpose: Global configuration constants for RAG system based on user stories
"""

from typing import Dict, Any, List


# ============================================================================
# EMBEDDING AND VECTOR CONFIGURATION
# ============================================================================

# Embedding model configuration
EMBEDDING_MODEL_NAME = "gemini-embedding-001"
EMBEDDING_MODEL_NAME_CREW = "models/gemini-embedding-001"
EMBEDDING_BATCH_SIZE = 100 # Batch size for embedding operations efficiency

# Metadata length limits to avoid chunk size issues
MAX_METADATA_FIELD_LENGTH = 50  # Maximum characters for any single metadata field
MAX_SUMMARY_LENGTH = 100  # Maximum length for document summary
MAX_KEYWORDS_COUNT = 5  # Maximum number of keywords

# Global chunk size configurations for different document types
CHUNK_SIZE_RESUMES = 196  # Smaller chunks for precise resume matching
CHUNK_SIZE_PROJECTS = 512  # Medium chunks for project descriptions
CHUNK_SIZE_JOB_POSTINGS = 384  # Medium-small chunks for job requirements

# Chunk overlap configurations
CHUNK_OVERLAP_RESUMES = 30
CHUNK_OVERLAP_PROJECTS = 50
CHUNK_OVERLAP_JOB_POSTINGS = 30

# Retrieval configurations
SIMILARITY_TOP_K_DEFAULT = 10
SIMILARITY_TOP_K_RESUMES = 10
SIMILARITY_TOP_K_PROJECTS = 10
SIMILARITY_TOP_K_JOB_POSTINGS = 10

# ============================================================================
# COLLECTION DEFINITIONS (Based on User Stories)
# ============================================================================


# Phase 1: Core Job-Seeking Profile
COLLECTION_RESUMES = "resumes"
COLLECTION_PROJECTS_EXPERIENCE = "projects_experience"
COLLECTION_JOB_POSTINGS = "job_postings"

# Collection configurations based on user stories
COLLECTION_CONFIGS: Dict[str, Dict[str, Any]] = {
    # Phase 1 Collections
    str(COLLECTION_RESUMES): {
        "name": "resumes",
        "description": "存储用户所有版本的个人简历，可以用于职业发展相关的分析，匹配，推荐，面试准备等场景。",
        "metadata": {
            "type": "resume",
            "purpose": "job_matching",
            "phase": 1
        },
        "chunk_size": CHUNK_SIZE_RESUMES,
        "chunk_overlap": CHUNK_OVERLAP_RESUMES,
        "similarity_top_k": SIMILARITY_TOP_K_RESUMES,
        "required_metadata_fields": ["target_job", "language", "last_updated"],
        "optional_metadata_fields": ["version", "company_focus"]
    },
    
    str(COLLECTION_PROJECTS_EXPERIENCE): {
        "name": "projects_experience",
        "description": "存储用户所有项目和工作经验的详细材料，作为知识库用户分析用户的工作经验，学习路线，职业发展，查漏补缺等。",
        "metadata": {
            "type": "experience",
            "purpose": "resume_support",
            "phase": 1
        },
        "chunk_size": CHUNK_SIZE_PROJECTS,
        "chunk_overlap": CHUNK_OVERLAP_PROJECTS,
        "similarity_top_k": SIMILARITY_TOP_K_PROJECTS,
        "required_metadata_fields": ["project_name", "document_type", "is_technical"],
        "optional_metadata_fields": ["related_resume_version", "tech_stack", "duration"]
    },
    
    str(COLLECTION_JOB_POSTINGS): {
        "name": "job_postings",
        "description": "存储收集到的目标岗位JD。用于市场需求分析、技能差距识别和简历匹配。",
        "metadata": {
            "type": "job_posting",
            "purpose": "market_analysis",
            "phase": 1
        },
        "chunk_size": CHUNK_SIZE_JOB_POSTINGS,
        "chunk_overlap": CHUNK_OVERLAP_JOB_POSTINGS,
        "similarity_top_k": SIMILARITY_TOP_K_JOB_POSTINGS,
        "required_metadata_fields": ["company_name", "job_title", "source_url"],
        "optional_metadata_fields": ["salary_range", "location", "experience_level"]
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_collection_config(collection_type: str) -> Dict[str, Any]:
    """Get configuration for a specific collection type."""
    return COLLECTION_CONFIGS.get(collection_type, None)


def get_chunk_config(collection_type: str) -> Dict[str, int]:
    """Get chunk configuration for a specific collection type."""
    config = get_collection_config(collection_type)
    return {
        "chunk_size": config.get("chunk_size", 512),
        "chunk_overlap": config.get("chunk_overlap", 50)
    }


def get_retrieval_config(collection_type: str) -> Dict[str, int]:
    """Get retrieval configuration for a specific collection type."""
    config = get_collection_config(collection_type)
    return {
        "similarity_top_k": config.get("similarity_top_k", SIMILARITY_TOP_K_DEFAULT)
    }


def get_all_collection_types() -> List[str]:
    """Get all available collection types."""
    return list(COLLECTION_CONFIGS.keys())

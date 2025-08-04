"""
Document Store for TechCoach
Purpose: Document vectorization, storage and retrieval infrastructure for CrewAI agents
"""

import os,sys
from loguru import logger
from typing import Optional, List, Dict, Any
from pathlib import Path

# LlamaIndex imports for document processing and vector storage
from llama_index.core import VectorStoreIndex, StorageContext, Settings, SimpleDirectoryReader, Document
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.node_parser.text.utils import split_by_sep
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.readers.file.unstructured import UnstructuredReader


from .chroma_client import ChromaDBClient
from .config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_BATCH_SIZE,
    COLLECTION_CONFIGS,
    COLLECTION_PROJECTS_EXPERIENCE,
    get_collection_config,
    get_chunk_config,
    get_retrieval_config
)
from .document_processor import get_document_processor
from genie_tool.db.rag_documents_op import RagDocumentOp


class DocumentStore:
    """
    Document Storage and Retrieval Infrastructure for CrewAI Agents.

    This class provides core document management capabilities:
    - Document ingestion and vectorization with LLM-based classification
    - Semantic similarity search across multiple collections
    - Document metadata management with automatic enhancement
    - Vector database operations for job-seeking profile management

    Design Philosophy:
    - Focus on storage and retrieval
    - Provide rich context for agents
    - Support multiple specialized collections based on user stories
    """
    
    def __init__(self, chroma_host: Optional[str] = None, chroma_port: Optional[int] = None):
        """
        Initialize Document Store.

        Args:
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
        """
        self.chroma_client = ChromaDBClient(host=chroma_host, port=chroma_port)
        self.indexes: Dict[str, VectorStoreIndex] = {}  # Multiple indexes for different collections
        self.retrievers: Dict[str, Any] = {}  # Multiple retrievers for different collections
        self.document_processor = get_document_processor()
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name=EMBEDDING_MODEL_NAME,
            api_key=os.getenv("GEMINI_API_KEY"),
            embed_batch_size=EMBEDDING_BATCH_SIZE
        )
        logger.info("Document Store configured for embedding and chunking")
        self.is_initialized = False
        self.initialize()
        logger.info("Document Store initialized with ChromaDB client successfully")

    def initialize(self) -> bool:
        """
        Initialize document storage system with all collections.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Connect to ChromaDB
            if not self.chroma_client.connect():
                logger.error("Failed to connect to ChromaDB")
                return False

            # Initialize all collections based on user stories
            self._initialize_collections()

            # Rebuild retrievers for existing collections with data
            self._rebuild_all_retrievers()

            logger.info("Document Store initialized successfully with all collections")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Document Store: {e}")
            return False

    def _initialize_collections(self):
        """Initialize all document collections based on user stories."""
        for collection_type, config in COLLECTION_CONFIGS.items():
            try:
                self.chroma_client.get_or_create_collection(
                    name=config["name"],
                    metadata=config["metadata"]
                )
                logger.info(f"Initialized collection: {config['name']} ({collection_type})")

            except Exception as e:
                logger.warning(f"Failed to initialize collection for {collection_type}: {e}")

    def _rebuild_all_retrievers(self):
        """Rebuild retrievers for all collections that have data."""
        for collection_type in COLLECTION_CONFIGS.keys():
            try:
                self._rebuild_retriever_for_collection(collection_type)
            except Exception as e:
                logger.warning(f"Failed to rebuild retriever for {collection_type}: {e}")
                continue

    def _rebuild_retriever_for_collection(self, collection_type: str, force_rebuild: bool = False):
        """Rebuild retriever for a specific collection if it has data."""
        try:
            if collection_type in self.retrievers and not force_rebuild:
                logger.debug(f"Retriever for {collection_type} already exists")
                return

            config = COLLECTION_CONFIGS.get(collection_type)
            if not config:
                logger.warning(f"No config found for collection type: {collection_type}")
                return

            collection_name = config["name"]

            # Try to get existing collection
            try:
                collection = self.chroma_client.client.get_collection(name=collection_name)
                count = collection.count()

                if count > 0:
                    logger.info(f"Found {count} documents in collection {collection_type}, rebuilding retriever...")

                    # Create ChromaVectorStore and index
                    from llama_index.vector_stores.chroma import ChromaVectorStore
                    from llama_index.core import VectorStoreIndex

                    vector_store = ChromaVectorStore(chroma_collection=collection)
                    index = VectorStoreIndex.from_vector_store(vector_store)

                    self.indexes[collection_type] = index

                    # Create retriever with collection-specific configuration
                    retrieval_config = get_retrieval_config(collection_type)
                    self.retrievers[collection_type] = index.as_retriever(
                        similarity_top_k=retrieval_config["similarity_top_k"]
                    )

                    logger.info(f"Successfully rebuilt retriever for {collection_type} ({count} documents)")
                else:
                    logger.debug(f"Collection {collection_type} is empty, skipping retriever creation")

            except Exception as collection_error:
                logger.debug(f"Collection {collection_type} not found or inaccessible: {collection_error}")

        except Exception as e:
            logger.warning(f"Failed to rebuild retriever for {collection_type}: {e}")

    async def ingest_single_document(self, document_path: str = None, document_content: str = None) -> Dict[str, Any]:
        """
        Comprehensive document ingestion including preprocessing and vector storage.

        This function combines preprocessing and ingestion into a single operation:
        1. Extract content from file or use provided content
        2. LLM-based preprocessing (rename, description, abstract, cleaning, classification)
        3. Ingest into ChromaDB vector store
        4. Return complete ingestion results

        Args:
            document_path: Path to the document file (optional)
            document_content: Raw text content (optional)

        Returns:
            Dictionary containing ingestion results:
            - success: Boolean indicating success/failure
            - document_id: Generated document ID
            - collection_type: Determined collection type
            - renamed_filename: Generated meaningful filename
            - description: Brief description
            - abstract: Detailed summary
            - cleaned_content: Normalized text content

            - file_path: Path to saved processed file
            - file_size: Size of processed content
            - error: Error message if failed
        """
        from datetime import datetime
        import uuid

        document_id = str(uuid.uuid4())
        temp_file_path = None

        try:
            # ========== PREPROCESSING PHASE ==========
            # 0. Create temp directories if they don't exist
            temp_dir = Path("file_db_dir/temp/documents")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Handle different input scenarios
            if document_path and document_content:
                # Both path and content provided - save content to temp file with original extension
                original_path = Path(document_path)
                extension = original_path.suffix or '.txt'
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                temp_file_path = temp_dir / f"temp_doc_{timestamp}{extension}"

                # Check if content is base64 encoded (for binary files)
                text_extensions = ['.txt', '.md', '.html', '.json', '.xml', '.csv']
                if extension.lower() in text_extensions:
                    # Text file - save as UTF-8
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        f.write(document_content)
                else:
                    # Binary file - decode base64 and save as binary
                    try:
                        import base64
                        binary_content = base64.b64decode(document_content)
                        with open(temp_file_path, 'wb') as f:
                            f.write(binary_content)
                    except Exception as e:
                        logger.error(f"Failed to decode base64 content: {e}")
                        # Fallback to text mode
                        with open(temp_file_path, 'w', encoding='utf-8') as f:
                            f.write(document_content)

                document_path = str(temp_file_path)
                logger.info(f"Saved content to temporary file with original extension: {temp_file_path}")
            elif document_path is None and document_content is not None:
                # Only content provided - create temporary file with .txt extension
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                temp_file_path = temp_dir / f"temp_doc_{timestamp}.txt"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(document_content)
                document_path = str(temp_file_path)
                logger.info(f"Saved raw content to temporary file: {temp_file_path}")
            elif document_path is None:
                return {"success": False, "error": "Either document_path or document_content must be provided"}

            # 1. Use UnstructuredReader to extract structured data
            reader = UnstructuredReader()
            documents = reader.load_data(file=Path(document_path))
            logger.info(f"Finish extracting structured data from {document_path}")

            if not documents:
                return {"success": False, "error": f"No content could be extracted from {document_path}"}

            # Get the main document content
            main_document = documents[0]
            content = main_document.text
            original_filename = Path(document_path).name if document_path else "未知文档"

            logger.info(f"Extracted {len(content)} characters from document")

            limit=7000
            if len(content) >= 7000:
                logger.warning(f"Document content is very large ({len(content)} characters>{limit}), consider chunking")

            # 2. Send data content to LLM for comprehensive preprocessing
            preprocessing_result = await self.document_processor.process_document(content[0:limit], original_filename)

            # Extract all preprocessing results
            collection_type = preprocessing_result.get("collection_type", COLLECTION_PROJECTS_EXPERIENCE)
            renamed_filename = preprocessing_result.get("renamed_filename", original_filename)
            description = preprocessing_result.get("description", "")
            abstract = preprocessing_result.get("abstract", "")
            cleaned_content = preprocessing_result.get("cleaned_content", content)
            base_metadata = preprocessing_result.get("metadata", {})

            # Determine final filename and handle duplicates
            base_filename = renamed_filename
            if not base_filename.endswith('.txt'):
                base_filename += ".txt"

            # 3. Save the processed document to permanent location
            documents_dir = Path("file_db_dir/rag_files")
            documents_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename to handle duplicates
            final_filename = RagDocumentOp.generate_unique_filename(base_filename, str(documents_dir))
            permanent_file_path = documents_dir / final_filename

            # Save cleaned content to permanent file
            with open(permanent_file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            logger.info(f"Saved processed document to: {permanent_file_path}")

            # ========== INGESTION PHASE ==========
            # Create processed document with enhanced metadata using cleaned content
            document = Document(
                id_=final_filename,
                text=cleaned_content,
                metadata={
                    "document_id": document_id,
                    "file_name": final_filename,
                    "description": description,
                    "collection_type": collection_type,
                    **base_metadata
                }
            )

            # Get collection configuration
            config = get_collection_config(collection_type)
            if not config:
                return {
                    "success": False,
                    "error": f"Unknown collection type: {collection_type}"
                }

            # Configure chunking based on collection type
            chunk_config = get_chunk_config(collection_type)

            node_parser = SentenceSplitter(
                chunk_size=chunk_config["chunk_size"],
                chunk_overlap=chunk_config["chunk_overlap"],
                separator="，,。？！；\n",
                paragraph_separator="---"
            )

            node_parser_2 = SemanticSplitterNodeParser(
                buffer_size=1,
                breakpoint_percentile_threshold=70,
                embed_model= Settings.embed_model,
                sentence_splitter=split_by_sep("\n", keep_sep=False),
            )
            
            selected_parser = node_parser_2

            # Get or create ChromaDB collection
            chroma_collection = self.chroma_client.get_or_create_collection(
                name=config["name"],
                metadata=config["metadata"]
            )
            logger.info(f"Get collection {collection_type}, start to ingest")

            # Create vector store and storage context
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # Create or update index for this collection
            if collection_type in self.indexes:
                # Add document to existing index
                await self.indexes[collection_type].ainsert(document)
                index = self.indexes[collection_type]
                
            else:
                # Create new index with custom node parser
                index = VectorStoreIndex.from_documents(
                    [document],
                    storage_context=storage_context,
                    transformations=[selected_parser]
                )
                self.indexes[collection_type] = index

                # Create retriever with collection-specific configuration
                retrieval_config = get_retrieval_config(collection_type)
                self.retrievers[collection_type] = index.as_retriever(
                    similarity_top_k=retrieval_config["similarity_top_k"]
                )

            logger.info(f"Successfully ingested document into {collection_type}: {final_filename}")

            # ========== DATABASE STORAGE ==========
            # Save document information to database
            try:
                file_size = len(cleaned_content.encode('utf-8'))
                await RagDocumentOp.create_document(
                    filename=final_filename,
                    file_path=str(permanent_file_path),
                    collection_type=collection_type,
                    file_size=file_size,
                    file_description=description,
                    file_abstract=abstract,
                    document_id=document_id
                )
                logger.info(f"Saved document record to database: {document_id}")
            except Exception as db_error:
                logger.error(f"Failed to save document to database: {db_error}")
                # Continue execution even if database save fails

            # ========== RETURN RESULTS ==========
            return {
                "success": True,
                "document_id": document_id,
                "collection_type": collection_type,
                "description": description,
                "abstract": abstract,
                "cleaned_content": cleaned_content,
                "file_path": str(permanent_file_path),
                "file_size": len(cleaned_content.encode('utf-8')),
                "final_filename": final_filename
            }

        except Exception as e:
            logger.error(f"Failed to ingest single document: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }
        finally:
            # Clean up temporary file if it was created from raw content
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temporary file {temp_file_path}: {cleanup_error}")
    
    def search_documents(self,
                        query_text: str,
                        collection_types: Optional[List[str]] = None,
                        top_k: int = 15,
                        min_score: float = 0.4) -> List[Dict[str, Any]]:
        """
        Search documents across collections using semantic similarity.

        Args:
            query_text: Search query
            collection_types: List of collection types to search (None for all)
            top_k: Maximum number of results per collection
            min_score: Minimum similarity score threshold (default: 0.4)

        Returns:
            List of search results with metadata (filtered by min_score)
        """
        if not self.retrievers:
            logger.error("No retrievers available. Please ingest documents first.")
            return []

        # If no specific collections specified, search all available
        if collection_types is None:
            collection_types = list(self.retrievers.keys())

        try:
            all_results = []
            for collection_type in collection_types:
                if collection_type not in self.retrievers:
                    logger.warning(f"Collection {collection_type} not available")
                    continue

                # Get collection-specific top_k
                retrieval_config = get_retrieval_config(collection_type)
                collection_top_k = max(top_k, retrieval_config["similarity_top_k"])

                # Retrieve from this collection
                logger.info(f"Searching in collection {collection_type} with top_k={collection_top_k}")
                retriever = self.retrievers[collection_type]
                nodes = retriever.retrieve(query_text)
                logger.info(f"Found {len(nodes)} nodes in collection {collection_type}")

                # Process results with score filtering
                for i, node in enumerate(nodes[:collection_top_k]):
                    score = getattr(node, 'score', 0.0)

                    # Filter by minimum score threshold
                    if score < min_score:
                        logger.debug(f"Filtering out result with score {score} < {min_score}")
                        continue

                    # Filter by content length (discard if content is less than 5 characters)
                    if len(node.text) < 5:
                        logger.debug(f"Filtering out result with content length {len(node.text)} < 5")
                        continue

                    result = {
                        "rank": i + 1,
                        "content": node.text,
                        "score": score,
                        "metadata": node.metadata,
                        "source": node.metadata.get("source", "unknown"),
                        "node_id": node.node_id,
                        "collection_type": collection_type,
                        "collection_rank": i + 1
                    }
                    all_results.append(result)

            # Sort all results by score (descending)
            all_results.sort(key=lambda x: x["score"], reverse=True)

            # Re-rank and limit total results
            final_results = []
            for i, result in enumerate(all_results[:top_k * len(collection_types)]):
                result["overall_rank"] = i + 1
                final_results.append(result)

            logger.info(f"Retrieved {len(final_results)} documents from {len(collection_types)} collections (min_score: {min_score})")
            return final_results

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all document collections."""
        try:
            stats = {
                "total_collections": len(COLLECTION_CONFIGS),
                "active_collections": len(self.indexes),
                "collections": {}
            }

            logger.info(f"Getting collection stats. Total configs: {len(COLLECTION_CONFIGS)}, Active indexes: {len(self.indexes)}")

            for collection_type, config in COLLECTION_CONFIGS.items():
                try:
                    info = self.chroma_client.get_collection_info(config["name"])
                    count = info.get("count", 0)

                    logger.debug(f"Collection {collection_type} ({config['name']}): count={count}, has_index={collection_type in self.indexes}, has_retriever={collection_type in self.retrievers}")

                    collection_stats = {
                        "name": config["name"],
                        "description": config["description"],
                        "metadata": info["metadata"],
                        "count": count,  # 前端期望的字段名
                        "document_count": count,  # 保持兼容性
                        "has_index": collection_type in self.indexes,
                        "has_retriever": collection_type in self.retrievers,
                        "phase": config["metadata"].get("phase", 1),
                        "chunk_size": config["chunk_size"],
                        "similarity_top_k": config["similarity_top_k"]
                    }
                    stats["collections"][collection_type] = collection_stats
                except Exception as e:
                    logger.warning(f"Failed to get stats for collection {collection_type}: {e}")
                    stats["collections"][collection_type] = {
                        "name": config["name"],
                        "description": config["description"],
                        "count": 0,
                        "document_count": 0,
                        "has_index": collection_type in self.indexes,
                        "has_retriever": collection_type in self.retrievers,
                        "error": str(e)
                    }

            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    async def reset_collection(self, collection_type: Optional[str] = None) -> bool:
        """
        Reset document collection(s) (delete all data).

        Args:
            collection_type: Specific collection to reset, if None resets all

        Returns:
            True if reset successful, False otherwise
        """
        try:
            if collection_type:
                # Reset specific collection
                config = get_collection_config(collection_type)
                if not config:
                    logger.error(f"Unknown collection type: {collection_type}")
                    return False

                success = self.chroma_client.delete_collection(config["name"])

                # Clear local cache for this collection
                if collection_type in self.indexes:
                    del self.indexes[collection_type]
                if collection_type in self.retrievers:
                    del self.retrievers[collection_type]

                # Clear database records and local files for this collection
                try:
                    # Get documents before deleting to access file paths
                    documents = await RagDocumentOp.search_documents(collection_type=collection_type)

                    # Delete local files
                    deleted_files_count = 0
                    for doc in documents:
                        if doc.file_path and Path(doc.file_path).exists():
                            try:
                                Path(doc.file_path).unlink()
                                deleted_files_count += 1
                                logger.debug(f"Deleted local file: {doc.file_path}")
                            except Exception as file_error:
                                logger.warning(f"Failed to delete local file {doc.file_path}: {file_error}")

                    # Delete database records
                    deleted_count = await RagDocumentOp.delete_by_collection_type(collection_type)
                    logger.info(f"Deleted {deleted_count} database records and {deleted_files_count} local files for collection: {collection_type}")
                except Exception as db_error:
                    logger.error(f"Failed to delete database records/files for collection {collection_type}: {db_error}")

                # Recreate empty collection
                if success:
                    self.chroma_client.get_or_create_collection(
                        name=config["name"],
                        metadata=config["metadata"]
                    )

                logger.info(f"Reset collection: {config['name']} ({collection_type})")
                return success
            else:
                # Reset all collections
                success_count = 0
                for collection_type, config in COLLECTION_CONFIGS.items():
                    try:
                        if self.chroma_client.delete_collection(config["name"]):
                            success_count += 1
                            # Recreate empty collection
                            self.chroma_client.get_or_create_collection(
                                name=config["name"],
                                metadata=config["metadata"]
                            )
                    except Exception as e:
                        logger.error(f"Failed to reset collection {collection_type}: {e}")

                # Clear all local caches
                self.indexes.clear()
                self.retrievers.clear()

                # Clear all database records and local files
                try:
                    all_documents = await RagDocumentOp.get_all()
                    total_deleted = 0
                    deleted_files_count = 0

                    for doc in all_documents:
                        # Delete local file
                        if doc.file_path and Path(doc.file_path).exists():
                            try:
                                Path(doc.file_path).unlink()
                                deleted_files_count += 1
                                logger.debug(f"Deleted local file: {doc.file_path}")
                            except Exception as file_error:
                                logger.warning(f"Failed to delete local file {doc.file_path}: {file_error}")

                        # Delete database record
                        if await RagDocumentOp.delete_by_id(doc.id):
                            total_deleted += 1

                    logger.info(f"Deleted {total_deleted} database records and {deleted_files_count} local files for all collections")
                except Exception as db_error:
                    logger.error(f"Failed to delete all database records/files: {db_error}")

                logger.info(f"Reset {success_count}/{len(COLLECTION_CONFIGS)} collections")
                return success_count > 0

        except Exception as e:
            logger.error(f"Failed to reset collection(s): {e}")
            return False

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a single document from vector store, database, and local file system.

        Args:
            document_id: The document ID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Get document info before deletion
            document = await RagDocumentOp.get_by_id(document_id)
            if not document:
                logger.warning(f"Document not found: {document_id}")
                return False

            # Delete from vector store (ChromaDB) and update index/retriever
            collection_type = document.collection_type
            deleted_from_vector_store = False

            try:
                # Get collection config
                config = get_collection_config(collection_type)
                if config:
                    collection = self.chroma_client.get_or_create_collection(
                        name=config["name"],
                        metadata=config["metadata"]
                    )

                    # Delete documents by matching file_name in metadata
                    try:
                        # Query documents with matching file_name in metadata
                        results = collection.get(
                            where={"file_name": document.filename}
                        )

                        if results and results['ids']:
                            # Delete all matching documents from ChromaDB
                            collection.delete(ids=results['ids'])
                            logger.info(f"Deleted {len(results['ids'])} ChromaDB documents with file_name: {document.filename}")
                            deleted_from_vector_store = True
                        else:
                            logger.warning(f"No ChromaDB documents found with file_name: {document.filename}")
                    except Exception as chroma_error:
                        logger.warning(f"Failed to delete ChromaDB documents for {document.filename}: {chroma_error}")
            except Exception as vector_error:
                logger.error(f"Failed to delete from vector store: {vector_error}")

            # Update index and retriever if documents were deleted from vector store
            if deleted_from_vector_store and collection_type in self.indexes:
                try:
                    # Delete document from LlamaIndex index
                    index = self.indexes[collection_type]

                    # Try to delete by document ID (filename)
                    try:
                        index.delete_ref_doc(document.filename, delete_from_docstore=True)
                        logger.info(f"Deleted document from LlamaIndex index: {document.filename}")
                    except Exception as index_error:
                        logger.warning(f"Failed to delete from LlamaIndex index: {index_error}")
                        # If direct deletion fails, rebuild the retriever for this collection
                        logger.info(f"Rebuilding retriever for collection: {collection_type}")
                        self._rebuild_retriever_for_collection(collection_type, force_rebuild=True)

                except Exception as index_update_error:
                    logger.error(f"Failed to update index for collection {collection_type}: {index_update_error}")
                    # As a fallback, rebuild the retriever
                    try:
                        self._rebuild_retriever_for_collection(collection_type, force_rebuild=True)
                        logger.info(f"Rebuilt retriever for collection {collection_type} as fallback")
                    except Exception as rebuild_error:
                        logger.error(f"Failed to rebuild retriever for collection {collection_type}: {rebuild_error}")

            # Delete local file
            if document.file_path and Path(document.file_path).exists():
                try:
                    Path(document.file_path).unlink()
                    logger.info(f"Deleted local file: {document.file_path}")
                except Exception as file_error:
                    logger.warning(f"Failed to delete local file {document.file_path}: {file_error}")

            # Delete from database
            success = await RagDocumentOp.delete_by_id(document_id)
            if success:
                logger.info(f"Successfully deleted document: {document_id}")
            else:
                logger.error(f"Failed to delete document from database: {document_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    def is_ready(self) -> bool:
        """Check if document store is ready for CrewAI agents."""
        return (
            self.chroma_client.is_connected() and
            len(self.indexes) > 0 and
            len(self.retrievers) > 0
        )

    def get_available_collections(self) -> List[str]:
        """Get list of available collection types."""
        return list(self.retrievers.keys())

    def get_collection_info(self, collection_type: str) -> Dict[str, Any]:
        """Get detailed information about a specific collection."""
        config = get_collection_config(collection_type)
        if not config:
            return {"error": f"Unknown collection type: {collection_type}"}

        try:
            info = self.chroma_client.get_collection_info(config["name"])
            return {
                "collection_type": collection_type,
                "name": config["name"],
                "description": config["description"],
                "document_count": info.get("count", 0),
                "has_index": collection_type in self.indexes,
                "has_retriever": collection_type in self.retrievers,
                "config": config
            }
        except Exception as e:
            return {"error": str(e)}

global_document_store = DocumentStore()

def get_document_store() -> DocumentStore:
    """Get the global document store instance."""
    return global_document_store

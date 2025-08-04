"""
ChromaDB Client for TechCoach RAG System
Purpose: ChromaDB connection and collection management for document storage
"""

import os
from loguru import logger
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings


class ChromaDBClient:
    """
    ChromaDB client for managing vector storage and retrieval.
    
    This class handles:
    - Connection to ChromaDB server
    - Collection creation and management
    - Health checks and connection validation
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize ChromaDB client.

        Args:
            host: ChromaDB host (defaults to CHROMA_HOST env var or 'localhost')
            port: ChromaDB port (defaults to CHROMA_PORT env var or 8000)
        """
        self.host = host or os.getenv("CHROMA_HOST", "localhost")
        # Handle Docker service name in local development
        if self.host == "chroma":
            self.host = "localhost"
        self.port = port or int(os.getenv("CHROMA_PORT", "8000"))
        self.client: Optional[chromadb.HttpClient] = None
        self._collections: Dict[str, Any] = {}
        
    def connect(self) -> bool:
        """
        Establish connection to ChromaDB server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(allow_reset=True)
            )
            
            # Test connection with heartbeat
            self.client.heartbeat()
            logger.info(f"Successfully connected to ChromaDB at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            self.client = None
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to ChromaDB."""
        if not self.client:
            return False
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> Any:
        if not self.client:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")
        if not self.is_connected():
            raise RuntimeError("ChromaDB client is not connected. Call connect() first.")

        if name in self._collections.keys():
            return self._collections[name]
        
        try:
            # Try to get existing collection first
            logger.info(f"Start get existing collection: {name}")
            collection = self.client.get_collection(name=name)
            
        except Exception:
            logger.info(f"No existing, create new collection: {name}, metadata: {metadata}")
            # Create new collection if it doesn't exist
            try:
                collection = self.client.create_collection(
                    name=name,
                    metadata=metadata if metadata!=None else {}
                )
                logger.info(f"Finish created new collection: {name}")
            except Exception as e:
                logger.error(f"Failed to create collection {name}: {e}")
                raise RuntimeError(f"Failed to create collection {name}: {e}")
        
        self._collections[name] = collection
        return collection
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        if not self.client:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, name: str) -> bool:
        if not self.client:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")
        
        try:
            self.client.delete_collection(name=name)
            if name in self._collections:
                del self._collections[name]
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False
    
    def reset_database(self) -> bool:
        if not self.client:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")
        try:
            self.client.reset()
            self._collections.clear()
            logger.warning("ChromaDB database has been reset - all data deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False
    
    def get_collection_info(self, name: str) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")

        try:
            collection = self.client.get_collection(name=name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata or {}
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {name}: {e}")
            return {"name": name, "count": 0, "metadata": {}}

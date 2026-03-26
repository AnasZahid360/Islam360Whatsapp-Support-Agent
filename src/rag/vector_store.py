"""
Vector store management using native Pinecone SDK.

This module handles document embedding generation using HuggingFace 
and vector storage/retrieval using the native Pinecone SDK.
"""

import json
import os
import time
from typing import List, Optional, Dict, Any, Tuple
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from .huggingface_loader import HuggingFaceDatasetLoader


class VectorStoreManager:
    """
    Manages the Pinecone vector store using the native SDK.
    """
    
    def __init__(
        self,
        data_path: str = "data/.hf_cache/faqs.json",
        index_name: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector store manager.
        """
        self.data_path = data_path
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME") or "maktek-index"
        self.embedding_model_name = embedding_model
        
        # Initialize embeddings (keeping this LangChain component as it's stable)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.pc: Optional[Pinecone] = None
        self.index = None
    
    def _get_pc(self) -> Pinecone:
        """Lazy initialization of Pinecone client"""
        if self.pc is None:
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables.")
            self.pc = Pinecone(api_key=api_key)
        return self.pc

    def load_documents(self) -> List[Document]:
        """
        Load documents from Hugging Face dataset with fallback to local JSON.
        Prefers cached data for faster loading.
        """
        # Try loading from Hugging Face dataset
        loader = HuggingFaceDatasetLoader(
            use_cache=True,
            fallback_path=self.data_path
        )
        documents_data = loader.load(prefer_cache=True)
        
        if not documents_data:
            # If HF loading failed, try loading from local data_path
            if os.path.exists(self.data_path):
                print(f"Loading from local file: {self.data_path}")
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    documents_data = json.load(f)
            else:
                raise FileNotFoundError(
                    f"Could not load data from Hugging Face or local path {self.data_path}"
                )
        
        documents = []
        for idx, item in enumerate(documents_data):
            question = item.get("question", "")
            answer = item.get("answer", "")
            content = f"Question: {question}\n\nAnswer: {answer}"
            
            doc = Document(
                page_content=content,
                metadata={
                    "source": "huggingface_customer_support_faqs",
                    "question": question,
                    "answer": answer,
                    "doc_id": str(idx)
                }
            )
            documents.append(doc)
        
        print(f"✓ Loaded {len(documents)} documents")
        return documents

    def initialize_vector_store(self, force_reload: bool = False) -> Any:
        """Initialize connection to Pinecone and optionally upsert data"""
        pc = self._get_pc()
        
        # Check if index exists
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating new Pinecone index: {self.index_name}...")
            pc.create_index(
                name=self.index_name,
                dimension=384, # all-MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            # Wait for index to be ready
            while not pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            force_reload = True # New index needs data
        
        self.index = pc.Index(self.index_name)
        
        if force_reload:
            print(f"Upserting documents to {self.index_name}...")
            documents = self.load_documents()
            self.add_documents(documents)
            
        print(f"✓ Connected to Pinecone index: {self.index_name}")
        return self.index

    def add_documents(self, documents: List[Document]) -> None:
        """Upsert documents to Pinecone"""
        if self.index is None:
            self.initialize_vector_store()
            
        vectors = []
        for doc in documents:
            embedding = self.embeddings.embed_query(doc.page_content)
            vectors.append({
                "id": doc.metadata.get("doc_id", str(time.time())),
                "values": embedding,
                "metadata": {
                    "text": doc.page_content,
                    **doc.metadata
                }
            })
            
        # Standard upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i + batch_size])
            
        print(f"✓ Upserted {len(documents)} document vectors")

    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Query Pinecone and return LangChain-compatible results"""
        if self.index is None:
            self.initialize_vector_store()
            
        query_embedding = self.embeddings.embed_query(query)
        
        response = self.index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True
        )
        
        results = []
        for match in response.matches:
            metadata = match.metadata
            content = metadata.pop("text", "")
            doc = Document(page_content=content, metadata=metadata)
            results.append((doc, match.score))
            
        return results

    def get_vector_store(self) -> Any:
        """Backward compatibility with LangChain-style getter"""
        if self.index is None:
            self.initialize_vector_store()
        return self.index


# Singleton manager
_vector_store_manager: Optional[VectorStoreManager] = None

def get_vector_store_manager(
    data_path: str = "data/.hf_cache/faqs.json",
    index_name: Optional[str] = None
) -> VectorStoreManager:
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager(data_path, index_name)
    return _vector_store_manager

"""
Retriever implementation with relevance scoring and auto-escalation.

This module provides the retrieval logic that queries the vector store,
scores results, and determines if escalation is needed.
"""

from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from src.rag.vector_store import get_vector_store_manager


class RetrievalResult:
    """Container for retrieval results with metadata"""
    
    def __init__(
        self,
        documents: List[Document],
        scores: List[float],
        query: str,
        relevance_score: float,
        should_escalate: bool
    ):
        """
        Initialize retrieval result.
        
        Args:
            documents: Retrieved documents
            scores: Similarity scores for each document
            query: Original search query
            relevance_score: Average relevance score
            should_escalate: Whether to escalate based on quality
        """
        self.documents = documents
        self.scores = scores
        self.query = query
        self.relevance_score = relevance_score
        self.should_escalate = should_escalate
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convert to dictionary format for state storage.
        
        Returns:
            List of document dictionaries with scores
        """
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "question": doc.metadata.get("question", ""),
                "answer": doc.metadata.get("answer", "")
            }
            for doc, score in zip(self.documents, self.scores)
        ]


class Retriever:
    """
    Retriever with relevance scoring and auto-escalation logic.
    
    Queries the vector store, evaluates result quality, and determines
    whether the query should be escalated to human support.
    """
    
    def __init__(
        self,
        relevance_threshold: float = 0.7,
        max_docs: int = 5,
        escalation_threshold: float = 0.5
    ):
        """
        Initialize the retriever.
        
        Args:
            relevance_threshold: Minimum score for acceptable results
            max_docs: Maximum number of documents to retrieve
            escalation_threshold: Score below which to auto-escalate
        """
        self.relevance_threshold = relevance_threshold
        self.max_docs = max_docs
        self.escalation_threshold = escalation_threshold
        self.vector_store_manager = get_vector_store_manager()
    
    def retrieve(
        self,
        query: str,
        k: int = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            k: Number of documents to retrieve (overrides max_docs if provided)
        
        Returns:
            RetrievalResult with documents and metadata
        """
        num_docs = k if k is not None else self.max_docs
        
        # Perform similarity search
        results = self.vector_store_manager.similarity_search_with_score(
            query,
            k=num_docs
        )
        
        if not results:
            return RetrievalResult(
                documents=[],
                scores=[],
                query=query,
                relevance_score=0.0,
                should_escalate=True
            )
        
        # Extract documents and scores
        documents = [doc for doc, _ in results]
        
        # Pinecone returns similarity scores (0-1) where 1 is identical
        scores = [self._normalize_score(score) for _, score in results]
        
        # Calculate scores
        avg_score = sum(scores) / len(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        
        # Determine if escalation is needed
        # We use max_score because if ANY document is highly relevant, we shouldn't escalate
        should_escalate = max_score < self.escalation_threshold
        
        return RetrievalResult(
            documents=documents,
            scores=scores,
            query=query,
            relevance_score=max_score, # Report max_score as the relevance_score for state
            should_escalate=should_escalate
        )
    
    def _normalize_score(self, score: float) -> float:
        """
        Normalize Pinecone similarity score (0-1).
        
        Pinecone with cosine similarity returns values where 1 is most similar.
        Since it's already in the 0-1 range, we just ensure it's within bounds.
        
        Args:
            score: Pinecone similarity score
        
        Returns:
            Normalized similarity score (0-1)
        """
        # Pinecone scores are already similarity scores
        return max(0.0, min(1.0, score))
    
    def format_context(self, result: RetrievalResult) -> str:
        """
        Format retrieved documents as context for the generator.
        
        Args:
            result: RetrievalResult object
        
        Returns:
            Formatted context string
        """
        if not result.documents:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for idx, (doc, score) in enumerate(zip(result.documents, result.scores), 1):
            question = doc.metadata.get("question", "")
            answer = doc.metadata.get("answer", "")
            
            context_parts.append(
                f"[Document {idx}] (Relevance: {score:.2f})\n"
                f"Q: {question}\n"
                f"A: {answer}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_best_match(self, result: RetrievalResult) -> Tuple[Document, float]:
        """
        Get the best matching document from results.
        
        Args:
            result: RetrievalResult object
        
        Returns:
            Tuple of (best_document, best_score)
        """
        if not result.documents:
            return None, 0.0
        
        return result.documents[0], result.scores[0]

"""
Hugging Face Dataset Loader for Customer Support FAQs

This module loads the Customer_support_faqs_dataset from Hugging Face.
"""

import os
import json
from typing import List, Dict, Optional
from langchain_core.documents import Document


class HuggingFaceDatasetLoader:
    """
    Loads the Customer Support FAQs dataset from Hugging Face.
    """
    
    DATASET_ID = "MakTek/Customer_support_faqs_dataset"
    CACHE_DIR = "data/.hf_cache"
    
    def __init__(self, use_cache: bool = True, fallback_path: Optional[str] = None):
        """
        Initialize the loader.
        
        Args:
            use_cache: Whether to cache the dataset locally
            fallback_path: Path to local JSON file as fallback if HF fetch fails
        """
        self.use_cache = use_cache
        self.fallback_path = fallback_path
        self.cache_file = os.path.join(self.CACHE_DIR, "faqs.json")
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def load_from_huggingface(self) -> List[Dict[str, str]]:
        """
        Load dataset from Hugging Face using datasets library.
        
        Returns:
            List of dictionaries with 'question' and 'answer' keys
        """
        try:
            from datasets import load_dataset
            
            print(f"Loading dataset from Hugging Face: {self.DATASET_ID}...")
            dataset = load_dataset(self.DATASET_ID, split="train")
            
            # Convert to list of dicts
            data = []
            for item in dataset:
                data.append({
                    "question": item.get("question", ""),
                    "answer": item.get("answer", "")
                })
            
            # Cache locally if enabled
            if self.use_cache:
                self._save_cache(data)
                print(f"✓ Cached {len(data)} FAQs to {self.cache_file}")
            
            print(f"✓ Loaded {len(data)} FAQs from Hugging Face")
            return data
            
        except ImportError:
            print("Warning: 'datasets' library not found. Install with: pip install datasets")
            return self._load_fallback()
        except Exception as e:
            print(f"Error loading from Hugging Face: {e}")
            return self._load_fallback()
    
    def load_from_cache(self) -> Optional[List[Dict[str, str]]]:
        """Load cached dataset if available."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✓ Loaded {len(data)} FAQs from cache")
                return data
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
        return None
    
    def _save_cache(self, data: List[Dict[str, str]]) -> None:
        """Save dataset to local cache."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_fallback(self) -> List[Dict[str, str]]:
        """Load from fallback path or return empty list."""
        if self.fallback_path and os.path.exists(self.fallback_path):
            try:
                with open(self.fallback_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✓ Loaded {len(data)} FAQs from fallback: {self.fallback_path}")
                return data
            except Exception as e:
                print(f"Error loading fallback: {e}")
        
        print("Warning: No data available. Using empty dataset.")
        return []
    
    def load(self, prefer_cache: bool = True) -> List[Dict[str, str]]:
        """
        Load dataset with intelligent fallback strategy.
        
        Args:
            prefer_cache: If True, check cache first before HF
        
        Returns:
            List of FAQ dictionaries
        """
        # Try cache first if preferred
        if prefer_cache:
            cached = self.load_from_cache()
            if cached:
                return cached
        
        # Try Hugging Face
        data = self.load_from_huggingface()
        if data:
            return data
        
        # Fallback to local file
        return self._load_fallback()


def load_faqs_from_huggingface(
    use_cache: bool = True,
    prefer_cache: bool = True,
    fallback_path: Optional[str] = None
) -> List[Document]:
    """
    Convenience function to load FAQs and convert to LangChain Documents.
    
    Args:
        use_cache: Whether to cache the dataset
        prefer_cache: Whether to prefer cached data over re-downloading
        fallback_path: Path to local JSON file as fallback
    
    Returns:
        List of LangChain Document objects
    """
    loader = HuggingFaceDatasetLoader(use_cache, fallback_path)
    data = loader.load(prefer_cache=prefer_cache)
    
    documents = []
    for idx, item in enumerate(data):
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
    
    return documents

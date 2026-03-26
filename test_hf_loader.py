#!/usr/bin/env python3
"""
Test script to verify Hugging Face dataset loader works
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rag.huggingface_loader import HuggingFaceDatasetLoader, load_faqs_from_huggingface

def test_loader():
    """Test the HF dataset loader"""
    print("=" * 60)
    print("Testing Hugging Face Dataset Loader")
    print("=" * 60)
    
    # Test 1: Load with caching
    print("\n[Test 1] Loading from Hugging Face with cache...")
    loader = HuggingFaceDatasetLoader(use_cache=True, fallback_path="data/maktek_qa.json")
    data = loader.load(prefer_cache=False)  # First time, load from HF
    
    if data:
        print(f"✓ Successfully loaded {len(data)} FAQs")
        print(f"\nFirst FAQ:")
        print(f"  Q: {data[0].get('question', 'N/A')}")
        print(f"  A: {data[0].get('answer', 'N/A')[:100]}...")
        
        # Test 2: Load from cache
        print("\n[Test 2] Loading from cache...")
        data2 = loader.load(prefer_cache=True)
        if data2 and len(data2) == len(data):
            print(f"✓ Cache working! Loaded same {len(data2)} FAQs from cache")
        else:
            print(f"✗ Cache mismatch: got {len(data2)} items, expected {len(data)}")
    else:
        print("✗ Failed to load data")
        return False
    
    # Test 3: Convert to LangChain documents
    print("\n[Test 3] Converting to LangChain documents...")
    docs = load_faqs_from_huggingface(use_cache=True, prefer_cache=True, fallback_path="data/maktek_qa.json")
    if docs:
        print(f"✓ Converted to {len(docs)} documents")
        print(f"\nFirst document metadata:")
        print(f"  Source: {docs[0].metadata.get('source')}")
        print(f"  Doc ID: {docs[0].metadata.get('doc_id')}")
        return True
    else:
        print("✗ Failed to convert to documents")
        return False

if __name__ == "__main__":
    success = test_loader()
    sys.exit(0 if success else 1)

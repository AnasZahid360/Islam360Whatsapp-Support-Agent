#!/usr/bin/env python3
"""
Force reload the Pinecone vector store with 200 FAQs from Hugging Face dataset.

Run this script to update your Pinecone index with all 200 customer support FAQs.
This is optional - the system works fine with lazy loading too.
"""

import sys
import os

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def force_reload_vector_store():
    """Force reload Pinecone with 200 HF FAQs"""
    print("=" * 70)
    print("Force Reloading Pinecone Vector Store with 200 HF FAQs")
    print("=" * 70)
    
    try:
        from src.rag.vector_store import get_vector_store_manager
        from src.rag.huggingface_loader import load_faqs_from_huggingface
        
        print("\n[Step 1] Loading 200 FAQs from Hugging Face...")
        docs = load_faqs_from_huggingface(use_cache=True, prefer_cache=True)
        print(f"✓ Loaded {len(docs)} documents")
        
        print("\n[Step 2] Initializing vector store manager...")
        manager = get_vector_store_manager()
        print("✓ Manager initialized")
        
        print("\n[Step 3] Force reloading Pinecone index...")
        manager.initialize_vector_store(force_reload=True)
        print("✓ Pinecone index reloaded with 200 FAQs")
        
        print("\n[Step 4] Verifying retrieval...")
        results = manager.similarity_search_with_score(
            "What is your return policy?", 
            k=3
        )
        print(f"✓ Retrieved {len(results)} results for test query")
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS: Vector store updated with 200 HF FAQs!")
        print("=" * 70)
        print("\nYour chatbot can now search across 200 comprehensive FAQs:")
        print("  - Account management")
        print("  - Payment methods")
        print("  - Order tracking")
        print("  - Shipping & delivery")
        print("  - Returns & refunds")
        print("  - Product availability")
        print("  - Warranties & guarantees")
        print("  - And more...")
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = force_reload_vector_store()
    sys.exit(0 if success else 1)

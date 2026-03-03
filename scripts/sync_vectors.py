"""
Sync script to re-index the Pinecone vector store with the latest JSON data.
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rag.vector_store import get_vector_store_manager

def sync_data():
    load_dotenv()
    print("🔄 Synchronizing Pinecone with latest dataset...")
    
    manager = get_vector_store_manager()
    # Force reload will upsert all documents from JSON
    manager.initialize_vector_store(force_reload=True)
    
    print("✅ Synchronization complete!")

if __name__ == "__main__":
    sync_data()

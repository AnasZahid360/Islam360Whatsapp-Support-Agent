import os
from dotenv import load_dotenv
from src.rag.vector_store import get_vector_store_manager
from src.rag.retriever import Retriever

# Load environment variables
load_dotenv()

def verify_pinecone():
    print("--- Pinecone Verification ---")
    
    # Check environment variables
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not api_key or not index_name:
        print("❌ Error: PINECONE_API_KEY or PINECONE_INDEX_NAME not found in .env")
        return

    print(f"Index Name: {index_name}")
    
    try:
        # Initialize VectorStoreManager
        manager = get_vector_store_manager()
        
        # Initialize or Load Vector Store
        print("\n1. Initializing Vector Store...")
        # Force reload to ensure documents are upserted for this test
        vector_store = manager.initialize_vector_store(force_reload=True)
        
        # Initialize Retriever
        print("\n2. Testing Retriever...")
        retriever = Retriever()
        
        test_query = "What is the return policy for MakTek products?"
        print(f"Query: '{test_query}'")
        
        result = retriever.retrieve(test_query, k=3)
        
        print(f"\nResults (Relevance Score: {result.relevance_score:.2f}):")
        for i, (doc, score) in enumerate(zip(result.documents, result.scores), 1):
            print(f"[{i}] Score: {score:.4f}")
            print(f"    Q: {doc.metadata.get('question', 'N/A')}")
            print(f"    Content: {doc.page_content[:100]}...")
            
        if result.documents:
            print("\n✅ Verification SUCCESSFUL")
        else:
            print("\n⚠️ No documents retrieved. If this is a new index, make sure you have documents uploaded.")
            
    except Exception as e:
        print(f"\n❌ Verification FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_pinecone()

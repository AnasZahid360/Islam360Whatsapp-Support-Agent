"""
Verification script for 'damaged package' retrieval.
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rag.retriever import Retriever

def verify_damaged_package_retrieval():
    load_dotenv()
    print("🔍 Testing 'damaged package' retrieval...")
    
    retriever = Retriever(relevance_threshold=0.7, escalation_threshold=0.4)
    query = "i have received a damaged package what are your protocols"
    
    result = retriever.retrieve(query)
    
    print(f"\nQuery: {query}")
    print(f"Relevance Score: {result.relevance_score:.2f}")
    print(f"Should Escalate: {result.should_escalate}")
    
    if result.documents:
        print("\nTop Matching Document:")
        best_doc = result.documents[0]
        print(f"Question: {best_doc.metadata.get('question')}")
        print(f"Score: {result.scores[0]:.2f}")
    
    if result.relevance_score > 0.6 and not result.should_escalate:
        print("\n✅ SUCCESS: 'Damaged package' query now has high relevance!")
    else:
        print("\n❌ FAILED: 'Damaged package' query still has low relevance or triggers escalation")

if __name__ == "__main__":
    verify_damaged_package_retrieval()

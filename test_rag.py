from dotenv import load_dotenv
load_dotenv()

from src.rag.retriever import Retriever
import sys

r = Retriever()
result = r.retrieve("How can I return my order?")
print(f"Query: {result.query}")
print(f"Relevance Score: {result.relevance_score}")
print(f"Should Escalate: {result.should_escalate}")
if result.documents:
    print(f"Top Doc Q: {result.documents[0].metadata.get('question', '')}")

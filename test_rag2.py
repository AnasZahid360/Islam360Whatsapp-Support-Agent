from dotenv import load_dotenv
load_dotenv()
from src.rag.retriever import Retriever

r = Retriever(escalation_threshold=0.4)
for q in ["It was damaged during shipping. How can I return my order?", "How can I return my order?"]:
    result = r.retrieve(q)
    print(f"Q: '{q}' -> max_score: {result.relevance_score}, should_escalate: {result.should_escalate}")

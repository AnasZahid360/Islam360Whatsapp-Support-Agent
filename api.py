"""
FastAPI backend for the MakTek Multi-Agent RAG System.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import create_graph_with_store
from src.state import create_initial_state
from src.memory.memory_manager import get_memory_manager

# Load environment variables
load_dotenv()

app = FastAPI(title="MakTek Support API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph and memory manager
graph, memory_manager = create_graph_with_store()

class ChatRequest(BaseModel):
    message: str
    user_id: str
    thread_id: str
    config_overrides: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    sender: str = "assistant"
    thread_id: str
    user_id: str
    docs: Optional[List[Dict[str, Any]]] = None

def _serialize_message(msg: BaseMessage) -> Dict[str, Any]:
    return {
        "type": msg.type,
        "content": msg.content
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Expose the chatbot logic as an API endpoint.
    """
    try:
        # Configuration for the graph
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": request.user_id
            }
        }
        
        # Increment interaction count for user preferences
        await memory_manager.increment_interaction_count(request.user_id)
        
        # Create initial state or get existing state from checkpoint
        # LangGraph handles persistence automatically if thread_id is provided in config
        state = create_initial_state(request.user_id, request.thread_id, request.config_overrides)
        state["messages"] = [HumanMessage(content=request.message)]
        
        final_response = ""
        retrieved_docs = []
        
        # Execute the graph
        async for event in graph.astream(state, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    final_response = last_msg.content
                
                # Capture retrieved docs if available in state
                if "retrieved_docs" in event:
                    retrieved_docs = event["retrieved_docs"]

        if not final_response:
            raise HTTPException(status_code=500, detail="Failed to generate a response")

        return ChatResponse(
            response=final_response,
            thread_id=request.thread_id,
            user_id=request.user_id,
            docs=retrieved_docs
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

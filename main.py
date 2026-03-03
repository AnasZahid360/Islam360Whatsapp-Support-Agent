"""
Main application entry point for the MakTek Multi-Agent RAG System.

This script provides a CLI interface to interact with the system,
demonstrating thread management, memory persistence, and agent routing.
"""

import asyncio
import os
import sys
from datetime import datetime
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import create_graph_with_store
from src.state import create_initial_state
from src.rag.vector_store import get_vector_store_manager
from src.memory.memory_manager import get_memory_manager


# Load environment variables
load_dotenv()


async def initialize_system():
    """
    Initialize the RAG system components.
    
    Returns:
        Tuple of (graph, memory_manager)
    """
    print("🚀 Initializing MakTek Multi-Agent RAG System...")
    print()
    
    # Initialize vector store
    print("📚 Loading vector store...")
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    print()
    
    # Create graph
    print("🔧 Building agent graph...")
    graph, memory_manager = create_graph_with_store()
    print("✓ System initialized successfully!")
    print()
    
    return graph, memory_manager


async def run_conversation(graph, memory_manager, user_id: str, thread_id: str):
    """
    Run an interactive conversation session.
    
    Args:
        graph: Compiled LangGraph
        memory_manager: Memory manager instance
        user_id: Unique user identifier
        thread_id: Unique thread identifier
    """
    print(f"👤 User: {user_id}")
    print(f"🧵 Thread: {thread_id}")
    print()
    print("=" * 60)
    print("MakTek Customer Support - Type 'quit' to exit")
    print("=" * 60)
    print()
    
    # Create initial configuration
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id
        }
    }
    
    # Track interaction count
    await memory_manager.increment_interaction_count(user_id)
    
    # Track if this is the first turn to initialize state
    is_first_turn = True
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n👋 Goodbye! Have a great day!")
            break
        
        if is_first_turn:
            # Create full initial state with user message
            input_data = create_initial_state(user_id, thread_id)
            input_data["messages"] = [HumanMessage(content=user_input)]
            is_first_turn = False
        else:
            # Only send the new message for subsequent turns
            input_data = {"messages": [HumanMessage(content=user_input)]}
        
        print()
        print("🤖 Assistant: ", end="", flush=True)
        
        # Stream graph execution
        try:
            async for event in graph.astream(input_data, config, stream_mode="values"):
                # Check for final response
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if last_msg.type == "ai":
                        # Print the response
                        print(last_msg.content)
                        break
        
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            print("Please try again.")
        
        print()


async def run_single_query(
    graph,
    user_id: str,
    thread_id: str,
    query: str
):
    """
    Run a single query (non-interactive mode).
    
    Args:
        graph: Compiled LangGraph
        user_id: Unique user identifier
        thread_id: Unique thread identifier
        query: User query string
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id
        }
    }
    
    state = create_initial_state(user_id, thread_id)
    state["messages"] = [HumanMessage(content=query)]
    
    print(f"Query: {query}")
    print()
    
    async for event in graph.astream(state, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Response: {last_msg.content}")
                break


async def main():
    """Main entry point"""
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ ERROR: No API key found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        print()
        print("1. Copy .env.example to .env")
        print("2. Add your API key")
        print("3. Run this script again")
        return
    
    # Initialize system
    graph, memory_manager = await initialize_system()
    
    # Generate unique identifiers
    user_id = "user_" + datetime.now().strftime("%Y%m%d")
    thread_id = "thread_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run interactive conversation
    await run_conversation(graph, memory_manager, user_id, thread_id)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())

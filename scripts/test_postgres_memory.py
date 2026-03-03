"""
Verification script for PostgreSQL memory persistence.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.memory_manager import get_memory_manager
from src.graph import create_graph_with_store
from src.state import create_initial_state

async def test_postgres_persistence():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ Error: DATABASE_URL not found in .env file.")
        print("Please add DATABASE_URL=postgresql://user:password@localhost:5432/dbname to your .env")
        return

    print(f"🚀 Testing PostgreSQL persistence with URL: {db_url.split('@')[-1]}") # Hide credentials
    
    try:
        # Initialize graph
        graph, memory_manager = create_graph_with_store()
        
        user_id = "test_user_pg"
        thread_id = "test_thread_pg"
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        
        # 1. First turn - Save state
        print("\n--- Turn 1: Saving state ---")
        input_data = create_initial_state(user_id, thread_id)
        input_data["messages"] = [HumanMessage(content="Hello, my name is Alice.")]
        
        async for event in graph.astream(input_data, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    print(f"Assistant: {last_msg.content}")
        
        # 2. Verify state in DB
        print("\n--- Verifying persistence ---")
        checkpointer = memory_manager.get_checkpointer()
        current_state = await graph.aget_state(config)
        
        if current_state.values:
            print("✅ State successfully retrieved from PostgreSQL!")
            messages = current_state.values.get("messages", [])
            print(f"Messages in state: {len(messages)}")
        else:
            print("❌ Error: Could not retrieve state from PostgreSQL.")
            return

        # 3. Simulate second turn with only thread_id (relying on checkpointer)
        print("\n--- Turn 2: Testing memory across events ---")
        input_data_2 = {"messages": [HumanMessage(content="What is my name?")]}
        
        async for event in graph.astream(input_data_2, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    print(f"Assistant: {last_msg.content}")
                    if "Alice" in last_msg.content:
                        print("\n✅ SUCCESS: PostgreSQL memory successfully recalled context!")
                    else:
                        print("\n❌ FAILED: Bot did not remember names across turns.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_postgres_persistence())

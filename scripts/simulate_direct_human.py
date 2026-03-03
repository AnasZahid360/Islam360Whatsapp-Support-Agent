"""
Simulation script for direct human escalation.
"""

import asyncio
import os
import sys
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import create_graph_with_store
from src.state import create_initial_state

load_dotenv()

async def simulate_direct_escalation():
    print("🚀 Initializing system for direct escalation simulation...")
    graph, _ = create_graph_with_store()
    
    user_id = "direct_esc_user"
    thread_id = "thread_direct_esc"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    
    print("\n--- Turn 1: Explicit Human Request ---")
    user_input = "can i talk to a human"
    input_data = create_initial_state(user_id, thread_id)
    input_data["messages"] = [HumanMessage(content=user_input)]
    
    async for event in graph.astream(input_data, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Assistant: {last_msg.content}")
                
    print("\n--- Turn 2: Saying 'yes' ---")
    user_input = "yes please"
    input_data = {"messages": [HumanMessage(content=user_input)]}
    
    async for event in graph.astream(input_data, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                if "Ticket ID" in last_msg.content:
                    print(f"Assistant: {last_msg.content[:100]}...")
                    print("\n✅ SUCCESS: Direct escalation worked correctly!")
                    return

if __name__ == "__main__":
    asyncio.run(simulate_direct_escalation())

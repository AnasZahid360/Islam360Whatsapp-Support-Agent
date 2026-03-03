"""
Simulation script to verify escalation loop fix.
This script simulates a multi-turn conversation to ensure state persistence.
"""

import asyncio
import os
import sys
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import create_graph_with_store
from src.state import create_initial_state

load_dotenv()

async def verify_loop_fix():
    print("🚀 Initializing system for simulation...")
    graph, memory_manager = create_graph_with_store()
    
    user_id = "test_user"
    thread_id = "test_thread_loop"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    
    # 1. First turn: Trigger escalation proposal
    print("\n--- Turn 1: Triggering Escalation ---")
    # Using a query that we know has low relevance or triggered it before
    input_data = create_initial_state(user_id, thread_id)
    input_data["messages"] = [HumanMessage(content="i want to return my package")]
    
    async for event in graph.astream(input_data, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Assistant: {last_msg.content}")
    
    # Check state after turn 1
    state = await graph.aget_state(config)
    print(f"DEBUG: escalation_status after Turn 1: {state.values.get('escalation_status')}")
    
    if state.values.get('escalation_status') != "proposed":
        print("❌ FAILED: escalation_status should be 'proposed'")
        return

    # 2. Second turn: Respond with 'yes'
    print("\n--- Turn 2: Saying 'yes' ---")
    input_data = {"messages": [HumanMessage(content="yes please")]}
    
    async for event in graph.astream(input_data, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Assistant: {last_msg.content}")
    
    # Check state after turn 2
    state = await graph.aget_state(config)
    print(f"DEBUG: escalation_status after Turn 2: {state.values.get('escalation_status')}")
    
    if state.values.get('escalation_status') == "confirmed":
        print("\n✅ SUCCESS: Escalation loop fixed and ticket created!")
    else:
        print(f"\n❌ FAILED: escalation_status is {state.values.get('escalation_status')}, expected 'confirmed'")

if __name__ == "__main__":
    asyncio.run(verify_loop_fix())

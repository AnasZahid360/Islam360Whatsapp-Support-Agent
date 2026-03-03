"""
Example usage scenarios for the Multi-Agent RAG System.

This module demonstrates various use cases including:
- Basic RAG flow
- Escalation scenarios
- Memory persistence
- Hallucination detection
- Dynamic model switching
"""

import asyncio
import os
import sys
from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph import create_graph_with_store
from src.state import create_initial_state
from src.rag.vector_store import get_vector_store_manager
from src.memory.memory_manager import get_memory_manager
from dotenv import load_dotenv

load_dotenv()


async def example_1_basic_rag():
    """Example 1: Basic RAG flow with successful retrieval"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic RAG Flow")
    print("="*60 + "\n")
    
    # Initialize
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    graph, memory_manager = create_graph_with_store()
    
    # Query that should be answered from knowledge base
    query = "What are MakTek's business hours?"
    
    config = {"configurable": {"thread_id": "thread_001", "user_id": "user_001"}}
    state = create_initial_state("user_001", "thread_001")
    state["messages"] = [HumanMessage(content=query)]
    
    print(f"Query: {query}\n")
    
    async for event in graph.astream(state, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Response: {last_msg.content}\n")
                break


async def example_2_escalation():
    """Example 2: Query that triggers escalation"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Auto-Escalation")
    print("="*60 + "\n")
    
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    graph, memory_manager = create_graph_with_store()
    
    # Query that won't be in knowledge base
    query = "Can you help me debug my custom MakTek API integration code?"
    
    config = {"configurable": {"thread_id": "thread_002", "user_id": "user_002"}}
    state = create_initial_state("user_002", "thread_002")
    state["messages"] = [HumanMessage(content=query)]
    
    print(f"Query: {query}\n")
    
    async for event in graph.astream(state, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Response: {last_msg.content}\n")
                print("✓ Ticket should be created in data/tickets/\n")
                break


async def example_3_memory_persistence():
    """Example 3: Multiple queries in same thread"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Memory Persistence")
    print("="*60 + "\n")
    
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    graph, memory_manager = create_graph_with_store()
    
    thread_id = "thread_003"
    user_id = "user_003"
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    
    queries = [
        "How do I reset my password?",
        "How long is the reset link valid?",
        "What if I don't receive the email?"
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"Query {idx}: {query}\n")
        
        state = create_initial_state(user_id, thread_id)
        state["messages"] = [HumanMessage(content=query)]
        
        async for event in graph.astream(state, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    print(f"Response {idx}: {last_msg.content}\n")
                    break
        
        print("-" * 60 + "\n")


async def example_4_model_switching():
    """Example 4: Dynamic model selection"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Dynamic Model Switching")
    print("="*60 + "\n")
    
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    graph, memory_manager = create_graph_with_store()
    
    query = "What payment methods does MakTek accept?"
    
    # Scenario A: Switch to another Groq model (llama-3.1-8b-instant)
    print("Scenario A: Switching to a faster Groq model (Llama 3.1 8B)...\n")
    
    state_groq_fast = create_initial_state("user_004", "thread_004a")
    state_groq_fast["config"]["model_name"] = "llama-3.1-8b-instant"
    state_groq_fast["messages"] = [HumanMessage(content=query)]
    
    config_groq = {"configurable": {"thread_id": "thread_004a", "user_id": "user_004"}}
    
    async for event in graph.astream(state_groq_fast, config_groq, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Response (Groq Fast): {last_msg.content}\n")
                break
                
    print("-" * 30)
    
    # Scenario B: Switch to OpenAI (requires OPENAI_API_KEY)
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
        print("Scenario B: Switching to OpenAI GPT-4o-mini...\n")
        
        state_openai = create_initial_state("user_004", "thread_004b")
        state_openai["config"]["model_provider"] = "openai"
        state_openai["config"]["model_name"] = "gpt-4o-mini"
        state_openai["messages"] = [HumanMessage(content=query)]
        
        config_openai = {"configurable": {"thread_id": "thread_004b", "user_id": "user_004"}}
        
        async for event in graph.astream(state_openai, config_openai, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    print(f"Response (OpenAI): {last_msg.content}\n")
                    break
    else:
        print("Skipping OpenAI scenario (OPENAI_API_KEY not configured).")


async def example_5_user_preferences():
    """Example 5: Store and use user preferences"""
    print("\n" + "="*60)
    print("EXAMPLE 5: User Preferences")
    print("="*60 + "\n")
    
    vector_store_manager = get_vector_store_manager()
    vector_store_manager.initialize_vector_store()
    graph, memory_manager = create_graph_with_store()
    
    user_id = "user_005"
    
    # Store user preference
    await memory_manager.save_user_preference(
        user_id,
        "response_style",
        "concise"
    )
    
    print("✓ Stored user preference: response_style = 'concise'\n")
    
    # Query with preferences
    query = "Tell me about MakTek's warranty"
    
    config = {"configurable": {"thread_id": "thread_005", "user_id": user_id}}
    state = create_initial_state(user_id, "thread_005")
    state["messages"] = [HumanMessage(content=query)]
    
    print(f"Query: {query}\n")
    
    async for event in graph.astream(state, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai":
                print(f"Response: {last_msg.content}\n")
                break


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MakTek Multi-Agent RAG System - Examples")
    print("="*60)
    
    examples = [
        ("Basic RAG Flow", example_1_basic_rag),
        ("Auto-Escalation", example_2_escalation),
        ("Memory Persistence", example_3_memory_persistence),
        ("Model Switching", example_4_model_switching),
        ("User Preferences", example_5_user_preferences),
    ]
    
    print("\nAvailable examples:")
    for idx, (name, _) in enumerate(examples, 1):
        print(f"{idx}. {name}")
    
    print("\n0. Run all examples")
    print()
    
    choice = input("Select example to run (0-5): ").strip()
    
    if choice == "0":
        for name, func in examples:
            await func()
            input("\nPress Enter to continue to next example...")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        _, func = examples[int(choice) - 1]
        await func()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())

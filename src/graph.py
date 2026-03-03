"""
Main graph construction module.

This module assembles all agents, guardrails, and memory components
into a complete LangGraph StateGraph using the Command pattern.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import AgentState
from src.agents.supervisor import supervisor_node
from src.agents.retriever_agent import retriever_agent_node
from src.agents.generator_agent import generator_agent_node
from src.agents.escalator_agent import escalator_agent_node
from src.agents.greeting_agent import greeting_agent_node
from src.agents.summarizer import check_and_summarize
from src.guardrails.hallucination_check import hallucination_check_node
from src.guardrails.input_guardrail import input_guardrail_node
from src.memory.memory_manager import get_memory_manager


def create_graph():
    """
    Create and compile the Multi-Agent RAG StateGraph.
    
    Architecture:
    START → input_guardrail → supervisor → retriever_agent → generator_agent → 
    hallucination_check → supervisor → END
                    ↓
              escalator_agent → END
    
    Returns:
        Compiled LangGraph with checkpointing enabled
    """
    # Initialize graph
    graph_builder = StateGraph(AgentState)
    
    # Add all nodes
    graph_builder.add_node("input_guardrail", input_guardrail_node)
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("retriever_agent", retriever_agent_node)
    graph_builder.add_node("generator_agent", generator_agent_node)
    graph_builder.add_node("escalator_agent", escalator_agent_node)
    graph_builder.add_node("greeting_agent", greeting_agent_node)
    graph_builder.add_node("hallucination_check", hallucination_check_node)
    graph_builder.add_node("summarizer", check_and_summarize)
    
    # Set entry point
    graph_builder.add_edge(START, "input_guardrail")
    
    # The Command pattern handles all routing automatically
    # No need for explicit edges - the Command objects in each node
    # specify the next destination
    
    # Get memory manager for checkpointing
    memory_manager = get_memory_manager()
    checkpointer = memory_manager.get_checkpointer()
    
    # Compile graph with checkpointing
    graph = graph_builder.compile(
        checkpointer=checkpointer,
        # interrupt_before=["escalator_agent"]  # Optional: interrupt before escalation
    )
    
    return graph


def create_graph_with_store():
    """
    Create the graph with both checkpointer and store.
    
    This version includes long-term memory storage in addition
    to checkpointing.
    
    Returns:
        Tuple of (compiled_graph, memory_manager)
    """
    # Initialize graph
    graph_builder = StateGraph(AgentState)
    
    # Add all nodes
    graph_builder.add_node("input_guardrail", input_guardrail_node)
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("retriever_agent", retriever_agent_node)
    graph_builder.add_node("generator_agent", generator_agent_node)
    graph_builder.add_node("escalator_agent", escalator_agent_node)
    graph_builder.add_node("greeting_agent", greeting_agent_node)
    graph_builder.add_node("hallucination_check", hallucination_check_node)
    graph_builder.add_node("summarizer", check_and_summarize)
    
    # Set entry point
    graph_builder.add_edge(START, "input_guardrail")
    
    # Get memory manager
    memory_manager = get_memory_manager()
    checkpointer = memory_manager.get_checkpointer()
    store = memory_manager.get_store()
    
    # Compile graph with checkpointing and store
    graph = graph_builder.compile(
        checkpointer=checkpointer,
        store=store
    )
    
    return graph, memory_manager


# Export visualization helper
def visualize_graph(graph, output_path: str = "graph_visualization.png"):
    """
    Visualize the graph structure and save to file.
    
    Args:
        graph: Compiled LangGraph
        output_path: Path to save the visualization
    """
    try:
        from PIL import Image
        import io
        
        # Get the graph as PNG
        png_data = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        img = Image.open(io.BytesIO(png_data))
        img.save(output_path)
        
        print(f"✓ Graph visualization saved to {output_path}")
    except Exception as e:
        print(f"⚠ Could not generate visualization: {e}")
        print("To enable visualization, install: pip install pygraphviz pillow")

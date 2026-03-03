"""
Dynamic model configuration and initialization.

This module provides the get_model() function that dynamically initializes
LLM instances based on configuration, supporting both OpenAI and Anthropic.
"""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelProvider:
    """Constants for supported model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class ModelName:
    """Constants for supported model names"""
    # OpenAI models
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Anthropic models
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    
    # Groq models
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    LLAMA_3_1_8B = "llama-3.1-8b-instant"


def get_model(config: Dict[str, Any]) -> BaseChatModel:
    """
    Initialize and return an LLM based on the provided configuration.
    
    This function supports dynamic model switching between OpenAI, Anthropic,
    and Groq providers.
    """
    provider = config.get("model_provider", "groq").lower()
    model_name = config.get("model_name", "llama-3.3-70b-versatile")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 1000)
    
    if provider == ModelProvider.GROQ:
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    if provider == ModelProvider.OPENAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    elif provider == ModelProvider.ANTHROPIC:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
    
    else:
        raise ValueError(
            f"Unsupported model provider: {provider}. "
            f"Supported providers: {ModelProvider.OPENAI}, {ModelProvider.ANTHROPIC}"
        )


def get_fast_model() -> BaseChatModel:
    """
    Get a fast, cost-efficient model for simple tasks.
    """
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=ModelName.LLAMA_3_1_8B,
        temperature=0.3,
        max_tokens=500,
        api_key=os.getenv("GROQ_API_KEY")
    )


def get_powerful_model() -> BaseChatModel:
    """
    Get a powerful model for complex reasoning tasks.
    """
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=ModelName.LLAMA_3_3_70B,
        temperature=0.7,
        max_tokens=2000,
        api_key=os.getenv("GROQ_API_KEY")
    )


def validate_model_config(config: Dict[str, Any]) -> bool:
    """
    Validate that the model configuration is properly formatted
    and that the model belongs to the chosen provider.
    """
    required_keys = ["model_provider", "model_name"]
    
    for key in required_keys:
        if key not in config:
            return False
    
    provider = config["model_provider"].lower()
    model_name = config["model_name"].lower()
    
    if provider not in [ModelProvider.OPENAI, ModelProvider.ANTHROPIC, ModelProvider.GROQ]:
        return False
    
    # Provider-specific model name sanity check
    if provider == ModelProvider.GROQ:
        groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
        if not any(m in model_name for m in groq_models):
            print(f"⚠️ Warning: '{model_name}' might not be a valid Groq model name.")
            
    if provider == ModelProvider.OPENAI:
        if not (model_name.startswith("gpt-") or model_name.startswith("o1")):
            print(f"⚠️ Warning: '{model_name}' might not be a valid OpenAI model name.")
            
    return True

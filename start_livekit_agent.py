#!/usr/bin/env python3
"""
LiveKit Agent Worker startup script.

This script starts the LiveKit agent that handles real-time voice conversations.
The agent connects to a LiveKit server and processes incoming audio from users.

Usage:
    python start_livekit_agent.py
    
Environment variables required:
    - LIVEKIT_API_KEY: LiveKit API key
    - LIVEKIT_API_SECRET: LiveKit API secret  
    - LIVEKIT_API_URL: LiveKit server URL (ws://localhost:7880 or wss://example.com)
    - OPENAI_API_KEY: OpenAI API key for LLM
    - BACKEND_URL: Backend API URL (default: http://127.0.0.1:8000)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from voice.livekit_agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_env():
    """Validate required environment variables"""
    required_vars = [
        'LIVEKIT_API_KEY',
        'LIVEKIT_API_SECRET',
        'OPENAI_API_KEY',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set these variables in your .env file or environment")
        return False
    
    logger.info("✓ All required environment variables are set")
    return True


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    if len(sys.argv) == 1:
        sys.argv.append("start")
    
    logger.info("Starting MakTek LiveKit Voice Agent...")
    
    # Validate environment
    if not validate_env():
        sys.exit(1)
    
    # Display configuration
    logger.info(f"LiveKit URL: {os.getenv('LIVEKIT_API_URL', 'ws://localhost:7880')}")
    logger.info(f"Backend URL: {os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')}")
    logger.info("")
    logger.info("Agent is ready to accept connections...")
    logger.info("Users can join the room via the web interface or LiveKit SDK")
    
    try:
        # Run the agent
        run_agent()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Memory management for the Multi-Agent RAG System.

This module implements dual memory architecture:
1. Short-term: MemorySaver for thread-specific conversation persistence
2. Long-term: InMemoryStore for user preferences and patterns
"""

from typing import Dict, Any, Optional
import os
import logging
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.memory import InMemoryStore
from psycopg_pool import ConnectionPool
import psycopg


class MemoryManager:
    """
    Manages both short-term and long-term memory for the RAG system.
    
    Short-term memory: Thread-specific conversation history with checkpointing
    Long-term memory: User preferences, patterns, and persistent data
    """
    
    def __init__(self):
        """Initialize memory systems"""
        self.db_url = os.getenv("DATABASE_URL")
        # Support individual variables as fallback
        if not self.db_url:
            user = os.getenv("POSTGRESUSER")
            password = os.getenv("POSTGRESPASSWORD")
            host = os.getenv("POSTGRESHOST")
            port = os.getenv("POSTGRESPORT", "5432")
            dbname = os.getenv("POSTGRESDBNAME", "postgres")
            if all([user, password, host]):
                self.db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        
        self.pool = None
        self.checkpointer = None
        self.store = InMemoryStore()
        
    def _get_pool(self) -> ConnectionPool:
        """Lazy initialization of connection pool"""
        if self.pool is None:
            if not self.db_url:
                raise ValueError("DATABASE_URL or specific POSTGRES_* variables not found in environment.")
            # Use open=False to prevent immediate background connection attempts
            # Set min_size=0 so it doesn't try to maintain connections if we fail
            self.pool = ConnectionPool(
                conninfo=self.db_url, 
                max_size=10, 
                min_size=0,
                open=False,
                kwargs={"connect_timeout": 5}
            )
        return self.pool

    def get_checkpointer(self) -> Any:
        """
        Get the checkpointer for short-term memory.
        
        Attempts to use PostgreSQL if DATABASE_URL is present,
        otherwise falls back to MemorySaver (in-memory).
        
        Returns:
            PostgresSaver or MemorySaver instance
        """
        if self.checkpointer is not None:
            return self.checkpointer
            
        if not self.db_url:
            print("ℹ️ DATABASE_URL not found. Using in-memory checkpointer.")
            self.checkpointer = MemorySaver()
            return self.checkpointer

        # PHASE 1: Direct reachability check (NO POOL YET)
        # We do this to avoid starting background pool threads if the DB is unreachable.
        try:
            # Safety check for db_url format
            db_display = "database"
            db_url = self.db_url
            if isinstance(db_url, str) and "@" in db_url:
                db_display = db_url.split("@")[-1]
            print(f"Checking database connectivity to {db_display}...")
            # Using a very short timeout for the initial probe
            with psycopg.connect(self.db_url, connect_timeout=3) as conn:
                pass
            print("✅ Database is reachable.")
        except Exception as e:
            print(f"⚠️ Warning: Database unreachable ({e}).")
            print("🔄 Falling back to in-memory persistence (Short-term memory only).")
            self.checkpointer = MemorySaver()
            return self.checkpointer

        # PHASE 2: Initialize Pool and Saver if reachable
        try:
            pool = self._get_pool()
            pool.open()
            self.checkpointer = PostgresSaver(pool)
            self.checkpointer.setup()
            print("✅ Successfully connected to PostgreSQL for persistence.")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize PostgreSQL pool ({e}).")
            print("🔄 Falling back to in-memory persistence.")
            if self.pool:
                try:
                    self.pool.close()
                except:
                    pass
                self.pool = None
            self.checkpointer = MemorySaver()
            
        return self.checkpointer
    
    def get_store(self) -> InMemoryStore:
        """
        Get the store for long-term memory.
        
        Returns:
            InMemoryStore instance for user preferences
        """
        return self.store
    
    async def save_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any,
        namespace: tuple = ("user_preferences",)
    ) -> None:
        """
        Save a user preference to long-term storage.
        
        Args:
            user_id: Unique user identifier
            key: Preference key
            value: Preference value
            namespace: Storage namespace tuple
        """
        full_key = f"{user_id}:{key}"
        await self.store.aput(namespace, full_key, {"value": value})
    
    async def get_user_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None,
        namespace: tuple = ("user_preferences",)
    ) -> Any:
        """
        Retrieve a user preference from long-term storage.
        
        Args:
            user_id: Unique user identifier
            key: Preference key
            default: Default value if not found
            namespace: Storage namespace tuple
        
        Returns:
            User preference value or default
        """
        full_key = f"{user_id}:{key}"
        result = await self.store.aget(namespace, full_key)
        
        if result and "value" in result.value:
            return result.value["value"]
        return default
    
    async def get_all_user_preferences(
        self,
        user_id: str,
        namespace: tuple = ("user_preferences",)
    ) -> Dict[str, Any]:
        """
        Retrieve all preferences for a user.
        
        Args:
            user_id: Unique user identifier
            namespace: Storage namespace tuple
        
        Returns:
            Dictionary of all user preferences
        """
        items = await self.store.asearch(namespace)
        preferences = {}
        
        for item in items:
            if item.key.startswith(f"{user_id}:"):
                pref_key = item.key.split(":", 1)[1]
                if "value" in item.value:
                    preferences[pref_key] = item.value["value"]
        
        return preferences
    
    async def delete_user_preference(
        self,
        user_id: str,
        key: str,
        namespace: tuple = ("user_preferences",)
    ) -> None:
        """
        Delete a user preference.
        
        Args:
            user_id: Unique user identifier
            key: Preference key
            namespace: Storage namespace tuple
        """
        full_key = f"{user_id}:{key}"
        await self.store.adelete(namespace, full_key)
    
    async def increment_interaction_count(self, user_id: str) -> int:
        """
        Increment and return the user's interaction count.
        
        Args:
            user_id: Unique user identifier
        
        Returns:
            Updated interaction count
        """
        count = await self.get_user_preference(user_id, "interaction_count", 0)
        count += 1
        await self.save_user_preference(user_id, "interaction_count", count)
        return count
    
    async def save_user_pattern(
        self,
        user_id: str,
        pattern_type: str,
        pattern_data: Dict[str, Any]
    ) -> None:
        """
        Save a detected user pattern (e.g., preferred response style).
        
        Args:
            user_id: Unique user identifier
            pattern_type: Type of pattern (e.g., "response_style", "topics")
            pattern_data: Pattern metadata
        """
        namespace = ("user_patterns", pattern_type)
        await self.save_user_preference(user_id, pattern_type, pattern_data, namespace)
    
    async def get_user_pattern(
        self,
        user_id: str,
        pattern_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user pattern.
        
        Args:
            user_id: Unique user identifier
            pattern_type: Type of pattern
        
        Returns:
            Pattern data or None
        """
        namespace = ("user_patterns", pattern_type)
        return await self.get_user_preference(user_id, pattern_type, None, namespace)


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """
    Get or create the global memory manager instance.
    
    Returns:
        MemoryManager singleton
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


if __name__ == "__main__":
    print("\n" + "!" * 60)
    print("THIS IS A MODULE, NOT A STANDALONE SCRIPT.")
    print("Please run 'main.py' to start the chatbot.")
    print("!" * 60 + "\n")

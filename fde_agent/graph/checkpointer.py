"""
Persistence and State Checkpointing for FDE Multi-Agent System.
"""

from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer() -> BaseCheckpointSaver:
    """Return an in-memory checkpointer for stateful agent execution."""
    return MemorySaver()


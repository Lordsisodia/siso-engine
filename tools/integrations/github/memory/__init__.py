"""
Memory Integration Stub
========================

Stub for memory integration. Will be connected to the full memory system
when Phase 2 of the memory separation is implemented.
"""

from pathlib import Path
from typing import Union


class MemoryManager:
    """
    Stub for memory manager integration.

    TODO: Connect to full memory system when ready.
    """

    def __init__(self, memory_path: Union[str, Path]):
        """Initialize memory manager."""
        self.memory_path = Path(memory_path)

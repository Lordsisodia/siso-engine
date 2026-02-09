# BlackBox5 Core Agent Definitions
"""
Core agent implementations for BlackBox5.

This package contains the three primary agents:
- AnalystAgent (Mary): Research and analysis
- ArchitectAgent (Alex): System architecture and design
- DeveloperAgent (Amelia): Code implementation and testing
"""

from .AnalystAgent import AnalystAgent
from .ArchitectAgent import ArchitectAgent
from .DeveloperAgent import DeveloperAgent

__all__ = [
    "AnalystAgent",
    "ArchitectAgent",
    "DeveloperAgent",
]

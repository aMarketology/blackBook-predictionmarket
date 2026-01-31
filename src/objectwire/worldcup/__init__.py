"""
ObjectWire World Cup Module
===========================
FIFA World Cup 2026 journalism automation tools.

Components:
- cli.py: World Cup CLI commands
- cli_gemma.py: Gemma 2 integrated CLI
- config.py: World Cup configuration
- content_engine.py: AI content generation
- monitor.py: FIFA news feed monitoring
"""

from .config import WorldCupConfig
from .content_engine import WorldCupContentEngine
from .monitor import WorldCupMonitor

__all__ = [
    "WorldCupConfig",
    "WorldCupContentEngine", 
    "WorldCupMonitor"
]

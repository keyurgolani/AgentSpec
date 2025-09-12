"""
Core services module for AgentSpec.

Contains the main business logic components including instruction database,
spec generation, template management, context detection, and task management.
"""

from .context_detector import ContextDetector
from .instruction_database import InstructionDatabase

# from .spec_generator import SpecGenerator  # Not implemented yet
from .template_manager import TemplateManager

# from .task_context import TaskContextManager  # Not implemented yet

__all__ = [
    "InstructionDatabase",
    # "SpecGenerator",
    "TemplateManager",
    "ContextDetector",
    # "TaskContextManager"
]

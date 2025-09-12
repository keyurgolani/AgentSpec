"""
Configuration module for AgentSpec.

Contains default configuration files and configuration-related utilities.
"""

from pathlib import Path

# Get the directory containing this module
CONFIG_DIR = Path(__file__).parent


def get_config_path(filename: str) -> Path:
    """Get absolute path to a configuration file."""
    return CONFIG_DIR / filename


def get_default_config_path() -> Path:
    """Get path to default configuration file."""
    return CONFIG_DIR / "default.yaml"


def get_logging_config_path() -> Path:
    """Get path to logging configuration file."""
    return CONFIG_DIR / "logging.yaml"

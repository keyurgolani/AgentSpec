"""
Feature Flag System

This module provides a feature flag system for gradual migration from AgentSpec v1 to v2,
allowing controlled rollout of new features and backward compatibility management.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeatureFlagStatus(Enum):
    """Feature flag status enumeration"""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


@dataclass
class FeatureFlag:
    """Feature flag configuration"""

    name: str
    status: FeatureFlagStatus
    description: str
    default_value: bool = False
    deprecation_version: Optional[str] = None
    removal_version: Optional[str] = None
    replacement: Optional[str] = None
    migration_guide_url: Optional[str] = None


@dataclass
class FeatureFlagConfig:
    """Feature flag configuration container"""

    flags: Dict[str, FeatureFlag] = field(default_factory=dict)
    version: str = "2.0.0"
    migration_mode: bool = True
    show_deprecation_warnings: bool = True

    def add_flag(self, flag: FeatureFlag) -> None:
        """Add a feature flag to the configuration"""
        self.flags[flag.name] = flag

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name"""
        return self.flags.get(name)

    def is_enabled(self, name: str) -> bool:
        """Check if a feature flag is enabled"""
        flag = self.get_flag(name)
        if not flag:
            return False

        # Check environment variable override
        env_var = f"AGENTSPEC_FEATURE_{name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")

        return flag.status == FeatureFlagStatus.ENABLED or flag.default_value


class FeatureFlagManager:
    """Manages feature flags for AgentSpec migration"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize feature flag manager.

        Args:
            config_path: Optional path to feature flag configuration file
        """
        self.config_path = config_path
        self.config = FeatureFlagConfig()
        self._initialize_default_flags()

        if config_path and config_path.exists():
            self._load_config()

    def _initialize_default_flags(self) -> None:
        """Initialize default feature flags for AgentSpec migration"""
        default_flags = [
            FeatureFlag(
                name="legacy_cli_interface",
                status=FeatureFlagStatus.DEPRECATED,
                description="Legacy monolithic CLI interface (agentspec.py)",
                default_value=True,
                deprecation_version="2.0.0",
                removal_version="3.0.0",
                replacement="agentspec.cli.main",
                migration_guide_url=None,
            ),
            FeatureFlag(
                name="new_modular_system",
                status=FeatureFlagStatus.ENABLED,
                description="New modular AgentSpec system with enhanced features",
                default_value=True,
            ),
            FeatureFlag(
                name="enhanced_instruction_database",
                status=FeatureFlagStatus.ENABLED,
                description="Enhanced instruction database with versioning and validation",
                default_value=True,
            ),
            FeatureFlag(
                name="template_system",
                status=FeatureFlagStatus.ENABLED,
                description="Template system for project-specific specifications",
                default_value=True,
            ),
            FeatureFlag(
                name="smart_context_detection",
                status=FeatureFlagStatus.ENABLED,
                description="Smart project context detection and instruction suggestions",
                default_value=True,
            ),
            FeatureFlag(
                name="interactive_wizard_v2",
                status=FeatureFlagStatus.ENABLED,
                description="Enhanced interactive wizard with project detection",
                default_value=True,
            ),
            FeatureFlag(
                name="legacy_instruction_format",
                status=FeatureFlagStatus.DEPRECATED,
                description="Legacy instruction format support",
                default_value=True,
                deprecation_version="2.0.0",
                removal_version="3.0.0",
                replacement="enhanced_instruction_database",
            ),
            FeatureFlag(
                name="migration_warnings",
                status=FeatureFlagStatus.ENABLED,
                description="Show migration warnings for deprecated features",
                default_value=True,
            ),
            FeatureFlag(
                name="compatibility_mode",
                status=FeatureFlagStatus.ENABLED,
                description="Backward compatibility mode for v1 interface",
                default_value=True,
            ),
        ]

        for flag in default_flags:
            self.config.add_flag(flag)

    def _load_config(self) -> None:
        """Load feature flag configuration from file"""
        if self.config_path is None:
            return
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            # Update configuration
            if "version" in data:
                self.config.version = data["version"]
            if "migration_mode" in data:
                self.config.migration_mode = data["migration_mode"]
            if "show_deprecation_warnings" in data:
                self.config.show_deprecation_warnings = data[
                    "show_deprecation_warnings"
                ]

            # Update flags
            if "flags" in data:
                for flag_name, flag_data in data["flags"].items():
                    existing_flag = self.config.get_flag(flag_name)
                    if existing_flag:
                        # Update existing flag
                        if "status" in flag_data:
                            existing_flag.status = FeatureFlagStatus(
                                flag_data["status"]
                            )
                        if "default_value" in flag_data:
                            existing_flag.default_value = flag_data["default_value"]
                    else:
                        # Create new flag
                        new_flag = FeatureFlag(
                            name=flag_name,
                            status=FeatureFlagStatus(
                                flag_data.get("status", "disabled")
                            ),
                            description=flag_data.get("description", ""),
                            default_value=flag_data.get("default_value", False),
                            deprecation_version=flag_data.get("deprecation_version"),
                            removal_version=flag_data.get("removal_version"),
                            replacement=flag_data.get("replacement"),
                            migration_guide_url=flag_data.get("migration_guide_url"),
                        )
                        self.config.add_flag(new_flag)

            logger.info(f"Loaded feature flag configuration from {self.config_path}")

        except Exception as e:
            logger.warning(f"Failed to load feature flag configuration: {e}")

    def save_config(self, path: Optional[Path] = None) -> None:
        """
        Save feature flag configuration to file.

        Args:
            path: Optional path to save configuration (uses self.config_path if None)
        """
        save_path = path or self.config_path
        if not save_path:
            raise ValueError("No configuration path specified")

        try:
            # Prepare data for serialization
            data: Dict[str, Any] = {
                "version": self.config.version,
                "migration_mode": self.config.migration_mode,
                "show_deprecation_warnings": self.config.show_deprecation_warnings,
                "flags": {},
            }

            for flag_name, flag in self.config.flags.items():
                data["flags"][flag_name] = {
                    "status": flag.status.value,
                    "description": flag.description,
                    "default_value": flag.default_value,
                    "deprecation_version": flag.deprecation_version,
                    "removal_version": flag.removal_version,
                    "replacement": flag.replacement,
                    "migration_guide_url": flag.migration_guide_url,
                }

            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved feature flag configuration to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save feature flag configuration: {e}")
            raise

    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag

        Returns:
            True if the flag is enabled, False otherwise
        """
        return self.config.is_enabled(flag_name)

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag by name.

        Args:
            flag_name: Name of the feature flag

        Returns:
            FeatureFlag instance or None if not found
        """
        return self.config.get_flag(flag_name)

    def get_deprecated_flags(self) -> Dict[str, FeatureFlag]:
        """Get all deprecated feature flags"""
        return {
            name: flag
            for name, flag in self.config.flags.items()
            if flag.status == FeatureFlagStatus.DEPRECATED
        }

    def show_deprecation_warning(self, flag_name: str) -> None:
        """
        Show deprecation warning for a feature flag.

        Args:
            flag_name: Name of the deprecated feature flag
        """
        if not self.config.show_deprecation_warnings:
            return

        flag = self.get_flag(flag_name)
        if not flag or flag.status != FeatureFlagStatus.DEPRECATED:
            return

        import warnings

        message = f"Feature '{flag_name}' is deprecated"
        if flag.deprecation_version:
            message += f" since version {flag.deprecation_version}"
        if flag.removal_version:
            message += f" and will be removed in version {flag.removal_version}"
        if flag.replacement:
            message += f". Use '{flag.replacement}' instead"
        if flag.migration_guide_url:
            message += f". See migration guide: {flag.migration_guide_url}"

        warnings.warn(message, DeprecationWarning, stacklevel=3)

    def check_migration_status(self) -> Dict[str, Any]:
        """
        Check overall migration status.

        Returns:
            Dictionary with migration status information
        """
        deprecated_flags = self.get_deprecated_flags()
        enabled_deprecated = {
            name: flag
            for name, flag in deprecated_flags.items()
            if self.is_enabled(name)
        }

        return {
            "migration_mode": self.config.migration_mode,
            "total_flags": len(self.config.flags),
            "deprecated_flags": len(deprecated_flags),
            "enabled_deprecated_flags": len(enabled_deprecated),
            "migration_complete": len(enabled_deprecated) == 0,
            "deprecated_in_use": list(enabled_deprecated.keys()),
        }

    def generate_migration_report(self) -> str:
        """Generate a migration status report"""
        status = self.check_migration_status()

        report = []
        report.append("AgentSpec Migration Status Report")
        report.append("=" * 40)
        report.append(f"Version: {self.config.version}")
        report.append(
            f"Migration Mode: {'Enabled' if status['migration_mode'] else 'Disabled'}"
        )
        report.append(f"Total Feature Flags: {status['total_flags']}")
        report.append(f"Deprecated Flags: {status['deprecated_flags']}")
        report.append(f"Deprecated Flags in Use: {status['enabled_deprecated_flags']}")
        report.append(
            f"Migration Complete: {'Yes' if status['migration_complete'] else 'No'}"
        )

        if status["deprecated_in_use"]:
            report.append("\nDeprecated Features Still in Use:")
            for flag_name in status["deprecated_in_use"]:
                flag = self.get_flag(flag_name)
                if flag is not None:
                    report.append(f"  - {flag_name}: {flag.description}")
                    if flag.replacement:
                        report.append(f"    Replacement: {flag.replacement}")
                    if flag.migration_guide_url:
                        report.append(
                            f"    Migration Guide: {flag.migration_guide_url}"
                        )

        return "\n".join(report)


# Global feature flag manager instance
_feature_flag_manager: Optional[FeatureFlagManager] = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """Get the global feature flag manager instance"""
    global _feature_flag_manager
    if _feature_flag_manager is None:
        # Look for configuration file in standard locations
        config_paths = [
            Path.cwd() / ".agentspec" / "feature_flags.json",
            Path.home() / ".agentspec" / "feature_flags.json",
            Path("/etc/agentspec/feature_flags.json"),
        ]

        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break

        _feature_flag_manager = FeatureFlagManager(config_path)

    return _feature_flag_manager


def is_feature_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        flag_name: Name of the feature flag

    Returns:
        True if the flag is enabled, False otherwise
    """
    return get_feature_flag_manager().is_enabled(flag_name)


def show_deprecation_warning(flag_name: str) -> None:
    """
    Show deprecation warning for a feature flag.

    Args:
        flag_name: Name of the deprecated feature flag
    """
    get_feature_flag_manager().show_deprecation_warning(flag_name)

"""
Unit tests for utility modules.
"""

import logging
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from agentspec.utils.config import ConfigManager
from agentspec.utils.logging import setup_logging


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        manager = ConfigManager()

        assert manager.project_path == Path.cwd()
        assert manager._config is None
        assert not manager._loaded

    def test_init_with_custom_path(self, temp_dir):
        """Test initialization with custom path."""
        manager = ConfigManager(temp_dir)

        assert manager.project_path == temp_dir

    def test_load_config_default(self):
        """Test loading default configuration."""
        manager = ConfigManager()

        config = manager.load_config()

        assert isinstance(config, dict)
        assert "agentspec" in config
        assert "version" in config["agentspec"]
        assert "paths" in config["agentspec"]
        assert "behavior" in config["agentspec"]
        assert "logging" in config["agentspec"]

    def test_load_config_with_project_file(self, temp_dir):
        """Test loading config with project-specific file."""
        # Create project config file
        project_config = {
            "agentspec": {
                "paths": {
                    "instructions": "custom/instructions",
                    "output": "custom/output",
                },
                "behavior": {"auto_detect_project": False},
            }
        }

        config_file = temp_dir / ".agentspec.yaml"
        with open(config_file, "w") as f:
            import yaml

            yaml.dump(project_config, f)

        manager = ConfigManager(temp_dir)
        config = manager.load_config()

        # Should merge with defaults
        assert config["agentspec"]["paths"]["instructions"] == "custom/instructions"
        assert config["agentspec"]["behavior"]["auto_detect_project"] is False
        # Should still have default values
        assert "version" in config["agentspec"]

    def test_load_config_with_user_file(self, temp_dir):
        """Test loading config with user-specific file."""
        user_config = {
            "agentspec": {"logging": {"level": "DEBUG", "file": "custom.log"}}
        }

        # Mock user home directory
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_dir

            # Create user config file
            user_config_dir = temp_dir / ".agentspec"
            user_config_dir.mkdir()
            user_config_file = user_config_dir / "config.yaml"

            with open(user_config_file, "w") as f:
                import yaml

                yaml.dump(user_config, f)

            manager = ConfigManager()
            config = manager.load_config()

            # Should include user config
            assert config["agentspec"]["logging"]["level"] == "DEBUG"
            assert config["agentspec"]["logging"]["file"] == "custom.log"

    def test_load_config_priority_order(self, temp_dir):
        """Test configuration priority order."""
        # Create user config
        user_config = {
            "agentspec": {
                "behavior": {"auto_detect_project": False, "suggest_templates": False}
            }
        }

        # Create project config (should override user config)
        project_config = {
            "agentspec": {
                "behavior": {
                    "auto_detect_project": True  # This should override user config
                }
            }
        }

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_dir

            # Create user config
            user_config_dir = temp_dir / ".agentspec"
            user_config_dir.mkdir()
            with open(user_config_dir / "config.yaml", "w") as f:
                import yaml

                yaml.dump(user_config, f)

            # Create project config
            project_dir = temp_dir / "project"
            project_dir.mkdir()
            with open(project_dir / ".agentspec.yaml", "w") as f:
                import yaml

                yaml.dump(project_config, f)

            manager = ConfigManager(project_dir)
            config = manager.load_config()

            # Project config should override user config
            assert config["agentspec"]["behavior"]["auto_detect_project"] is True
            # User config should still apply where not overridden
            assert config["agentspec"]["behavior"]["suggest_templates"] is False

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading config with invalid YAML."""
        # Create invalid YAML file
        config_file = temp_dir / ".agentspec.yaml"
        config_file.write_text("invalid: yaml: content: [")

        manager = ConfigManager(temp_dir)

        # Should fall back to default config
        config = manager.load_config()

        assert isinstance(config, dict)
        assert "agentspec" in config

    def test_get_config_value(self, temp_dir):
        """Test getting specific config values."""
        project_config = {
            "agentspec": {"paths": {"instructions": "custom/instructions"}}
        }

        config_file = temp_dir / ".agentspec.yaml"
        with open(config_file, "w") as f:
            import yaml

            yaml.dump(project_config, f)

        manager = ConfigManager(temp_dir)
        manager.load_config()

        # Test getting nested value
        instructions_path = manager.get_config_value("agentspec.paths.instructions")
        assert instructions_path == "custom/instructions"

        # Test getting non-existent value with default
        non_existent = manager.get_config_value(
            "agentspec.nonexistent", "default_value"
        )
        assert non_existent == "default_value"

        # Test getting non-existent value without default
        non_existent = manager.get_config_value("agentspec.nonexistent")
        assert non_existent is None

    def test_set_config_value(self, temp_dir):
        """Test setting config values."""
        manager = ConfigManager(temp_dir)
        manager.load_config()

        # Set a new value
        manager.set_config_value("agentspec.custom.setting", "test_value")

        # Verify it was set
        value = manager.get_config_value("agentspec.custom.setting")
        assert value == "test_value"

    def test_save_config(self, temp_dir):
        """Test saving configuration to file."""
        manager = ConfigManager(temp_dir)
        config = manager.load_config()

        # Modify config
        config["agentspec"]["custom"] = {"test": "value"}

        # Save config
        config_file = temp_dir / ".agentspec.yaml"
        manager.save_config(str(config_file))

        # Verify file was created and contains correct data
        assert config_file.exists()

        with open(config_file) as f:
            import yaml

            saved_config = yaml.safe_load(f)

        assert saved_config["agentspec"]["custom"]["test"] == "value"

    def test_reload_config(self, temp_dir):
        """Test reloading configuration."""
        config_file = temp_dir / ".agentspec.yaml"

        # Create initial config
        initial_config = {"agentspec": {"custom": {"value": "initial"}}}

        with open(config_file, "w") as f:
            import yaml

            yaml.dump(initial_config, f)

        manager = ConfigManager(temp_dir)
        config1 = manager.load_config()

        assert config1["agentspec"]["custom"]["value"] == "initial"

        # Modify config file
        updated_config = {"agentspec": {"custom": {"value": "updated"}}}

        with open(config_file, "w") as f:
            import yaml

            yaml.dump(updated_config, f)

        # Reload config
        manager.reload()
        config2 = manager.load_config()

        assert config2["agentspec"]["custom"]["value"] == "updated"

    def test_merge_configs(self):
        """Test configuration merging."""
        manager = ConfigManager()

        base_config = {
            "agentspec": {
                "version": "1.0.0",
                "paths": {
                    "instructions": "default/instructions",
                    "templates": "default/templates",
                },
                "behavior": {"auto_detect_project": True, "suggest_templates": True},
            }
        }

        override_config = {
            "agentspec": {
                "paths": {"instructions": "custom/instructions"},
                "behavior": {"auto_detect_project": False},
                "custom": {"setting": "value"},
            }
        }

        merged = manager._merge_configs(base_config, override_config)

        # Should preserve base values not overridden
        assert merged["agentspec"]["version"] == "1.0.0"
        assert merged["agentspec"]["paths"]["templates"] == "default/templates"
        assert merged["agentspec"]["behavior"]["suggest_templates"] is True

        # Should override with new values
        assert merged["agentspec"]["paths"]["instructions"] == "custom/instructions"
        assert merged["agentspec"]["behavior"]["auto_detect_project"] is False

        # Should add new values
        assert merged["agentspec"]["custom"]["setting"] == "value"


class TestLoggingSetup:
    """Test cases for logging setup utilities."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()

            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args[1]
            assert call_args["level"] == logging.INFO

    def test_setup_logging_with_level(self):
        """Test logging setup with specific level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(log_level="DEBUG")

            call_args = mock_basic_config.call_args[1]
            assert call_args["level"] == logging.DEBUG

    def test_setup_logging_with_file(self, temp_dir):
        """Test logging setup with file output."""
        log_file = temp_dir / "test.log"

        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(log_file=str(log_file))

            call_args = mock_basic_config.call_args[1]
            assert "filename" in call_args
            assert call_args["filename"] == str(log_file)

    def test_setup_logging_structured(self):
        """Test structured logging setup."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(structured=True)

            call_args = mock_basic_config.call_args[1]
            # Should use JSON formatter for structured logging
            assert "format" in call_args

    def test_setup_logging_no_console(self):
        """Test logging setup without console output."""
        with patch("logging.basicConfig") as mock_basic_config:
            with patch("logging.StreamHandler") as mock_stream_handler:
                setup_logging(console_output=False)

                # Should not add console handler
                mock_stream_handler.assert_not_called()

    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(log_level="INVALID")

            # Should fall back to INFO level
            call_args = mock_basic_config.call_args[1]
            assert call_args["level"] == logging.INFO

    def test_setup_logging_with_handlers(self):
        """Test logging setup with custom handlers."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            setup_logging(log_level="DEBUG", structured=True, console_output=True)

            # Should configure root logger
            mock_get_logger.assert_called()

    def test_setup_logging_file_creation(self, temp_dir):
        """Test that log file directory is created."""
        log_file = temp_dir / "logs" / "test.log"

        # Directory doesn't exist initially
        assert not log_file.parent.exists()

        with patch("logging.basicConfig"):
            setup_logging(log_file=str(log_file))

        # Directory should be created
        assert log_file.parent.exists()

    def test_setup_logging_rotation(self, temp_dir):
        """Test logging setup with file rotation."""
        log_file = temp_dir / "test.log"

        with patch("logging.handlers.RotatingFileHandler") as mock_rotating:
            setup_logging(log_file=str(log_file), max_bytes=1024 * 1024, backup_count=5)

            mock_rotating.assert_called_once()
            call_args = mock_rotating.call_args
            assert call_args[0][0] == str(log_file)

    def test_get_logger_with_context(self):
        """Test getting logger with context information."""
        from agentspec.utils.logging import get_logger_with_context

        logger = get_logger_with_context(
            "test_module", {"task_id": "123", "user": "test"}
        )

        assert logger.name == "test_module"
        # Context should be available in logger
        assert hasattr(logger, "_context") or logger.extra

    def test_log_performance(self):
        """Test performance logging utilities."""
        from agentspec.utils.logging import log_performance

        with patch("time.time", side_effect=[1.0, 2.5]):  # 1.5 second duration
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                @log_performance("test_operation")
                def test_function():
                    return "result"

                result = test_function()

                assert result == "result"
                mock_logger.info.assert_called()
                # Should log performance information
                call_args = mock_logger.info.call_args[0][0]
                assert "test_operation" in call_args
                assert "1.5" in call_args  # Duration


class TestFeatureFlags:
    """Test cases for feature flags utility."""

    def test_feature_flag_enabled(self):
        """Test checking if feature flag is enabled."""
        from agentspec.utils.feature_flags import is_feature_enabled

        # Mock config with feature flags
        with patch("agentspec.utils.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.get_config_value.return_value = True
            mock_config_manager.return_value = mock_manager

            result = is_feature_enabled("test_feature")

            assert result is True
            mock_manager.get_config_value.assert_called_with(
                "agentspec.feature_flags.test_feature", False
            )

    def test_feature_flag_disabled(self):
        """Test checking disabled feature flag."""
        from agentspec.utils.feature_flags import is_feature_enabled

        with patch("agentspec.utils.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.get_config_value.return_value = False
            mock_config_manager.return_value = mock_manager

            result = is_feature_enabled("test_feature")

            assert result is False

    def test_feature_flag_default(self):
        """Test feature flag with default value."""
        from agentspec.utils.feature_flags import is_feature_enabled

        with patch("agentspec.utils.config.ConfigManager") as mock_config_manager:
            mock_manager = Mock()
            mock_manager.get_config_value.return_value = None  # Not configured
            mock_config_manager.return_value = mock_manager

            result = is_feature_enabled("test_feature", default=True)

            assert result is True

    def test_feature_flag_decorator(self):
        """Test feature flag decorator."""
        from agentspec.utils.feature_flags import feature_flag

        with patch(
            "agentspec.utils.feature_flags.is_feature_enabled", return_value=True
        ):

            @feature_flag("test_feature")
            def test_function():
                return "enabled"

            result = test_function()
            assert result == "enabled"

        with patch(
            "agentspec.utils.feature_flags.is_feature_enabled", return_value=False
        ):

            @feature_flag("test_feature")
            def test_function():
                return "enabled"

            result = test_function()
            assert result is None  # Should return None when disabled

    def test_feature_flag_decorator_with_fallback(self):
        """Test feature flag decorator with fallback function."""
        from agentspec.utils.feature_flags import feature_flag

        def fallback_function():
            return "fallback"

        with patch(
            "agentspec.utils.feature_flags.is_feature_enabled", return_value=False
        ):

            @feature_flag("test_feature", fallback=fallback_function)
            def test_function():
                return "enabled"

            result = test_function()
            assert result == "fallback"


class TestUtilityHelpers:
    """Test cases for utility helper functions."""

    def test_ensure_directory_exists(self, temp_dir):
        """Test directory creation utility."""
        from agentspec.utils.file_utils import ensure_directory_exists

        test_dir = temp_dir / "nested" / "directory"
        assert not test_dir.exists()

        ensure_directory_exists(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_safe_file_write(self, temp_dir):
        """Test safe file writing utility."""
        from agentspec.utils.file_utils import safe_file_write

        test_file = temp_dir / "test.txt"
        content = "Test content"

        safe_file_write(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_safe_file_write_backup(self, temp_dir):
        """Test safe file writing with backup."""
        from agentspec.utils.file_utils import safe_file_write

        test_file = temp_dir / "test.txt"

        # Create initial file
        test_file.write_text("Original content")

        # Write new content with backup
        safe_file_write(test_file, "New content", backup=True)

        assert test_file.read_text() == "New content"

        # Backup should exist
        backup_file = temp_dir / "test.txt.bak"
        assert backup_file.exists()
        assert backup_file.read_text() == "Original content"

    def test_validate_file_path(self, temp_dir):
        """Test file path validation utility."""
        from agentspec.utils.file_utils import validate_file_path

        # Valid existing file
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        result = validate_file_path(test_file)
        assert result is True

        # Non-existent file
        result = validate_file_path(temp_dir / "nonexistent.txt")
        assert result is False

        # Directory instead of file
        result = validate_file_path(temp_dir)
        assert result is False

    def test_get_file_hash(self, temp_dir):
        """Test file hash calculation utility."""
        from agentspec.utils.file_utils import get_file_hash

        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content for hashing")

        hash1 = get_file_hash(test_file)
        hash2 = get_file_hash(test_file)

        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length

        # Different content should produce different hash
        test_file.write_text("Different content")
        hash3 = get_file_hash(test_file)

        assert hash1 != hash3

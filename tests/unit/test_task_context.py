"""
Unit tests for TaskContextManager class.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agentspec.core.task_context import (
    TaskContext,
    TaskContextManager,
    TaskDefinition,
    TaskDependency,
    TaskGraph,
    TaskMetadata,
    TaskPriority,
    TaskStatus,
    ValidationResult,
)
from tests.conftest import assert_validation_result


class TestTaskContextManager:
    """Test cases for TaskContextManager class."""

    def test_init_with_default_paths(self):
        """Test initialization with default paths."""
        manager = TaskContextManager()

        assert manager.contexts_path is not None
        assert manager.schema_path is not None
        assert manager._contexts == {}
        assert not manager._loaded
        assert manager.contexts_path.exists()  # Should create directory

    def test_init_with_custom_paths(self, temp_dir):
        """Test initialization with custom paths."""
        contexts_path = temp_dir / "contexts"
        schema_path = temp_dir / "schema.json"

        manager = TaskContextManager(
            contexts_path=contexts_path, schema_path=schema_path
        )

        assert manager.contexts_path == contexts_path
        assert manager.schema_path == schema_path
        assert contexts_path.exists()  # Should create directory

    def test_create_task_context(self, task_context_manager):
        """Test creating a new task context."""
        task_def = TaskDefinition(
            title="Test Task",
            description="A test task for unit testing",
            category="testing",
            priority=TaskPriority.HIGH,
            estimated_duration=60,
            tags=["test", "unit"],
        )

        context = task_context_manager.create_task_context(task_def)

        assert isinstance(context, TaskContext)
        assert context.title == "Test Task"
        assert context.description == "A test task for unit testing"
        assert context.status == TaskStatus.PENDING
        assert context.metadata.category == "testing"
        assert context.metadata.priority == TaskPriority.HIGH
        assert context.metadata.estimated_duration == 60
        assert context.metadata.tags == ["test", "unit"]
        assert context.id in task_context_manager._contexts

    def test_create_task_context_invalid(self, task_context_manager):
        """Test creating invalid task context."""
        task_def = TaskDefinition(
            title="",  # Empty title should be invalid
            description="A test task",
            category="testing",
        )

        with pytest.raises(ValueError, match="Invalid task context"):
            task_context_manager.create_task_context(task_def)

    def test_load_task_context_success(self, task_context_manager, sample_task_context):
        """Test loading existing task context."""
        # First save a context
        task_context_manager._save_task_context(sample_task_context)

        # Clear loaded contexts
        task_context_manager._contexts.clear()

        # Load the context
        loaded_context = task_context_manager.load_task_context(sample_task_context.id)

        assert loaded_context is not None
        assert loaded_context.id == sample_task_context.id
        assert loaded_context.title == sample_task_context.title
        assert loaded_context.description == sample_task_context.description

    def test_load_task_context_not_found(self, task_context_manager):
        """Test loading nonexistent task context."""
        context = task_context_manager.load_task_context("nonexistent_id")

        assert context is None

    def test_load_task_context_from_cache(
        self, task_context_manager, sample_task_context
    ):
        """Test loading task context from cache."""
        # Add to cache
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        loaded_context = task_context_manager.load_task_context(sample_task_context.id)

        assert loaded_context == sample_task_context

    def test_update_task_context(self, task_context_manager, sample_task_context):
        """Test updating existing task context."""
        # First create the context
        task_context_manager._contexts[sample_task_context.id] = sample_task_context
        original_updated_at = sample_task_context.metadata.updated_at

        # Update the context
        sample_task_context.title = "Updated Title"
        task_context_manager.update_task_context(sample_task_context)

        # Check that updated_at was changed
        assert sample_task_context.metadata.updated_at > original_updated_at

        # Verify the context file was saved
        context_file = (
            task_context_manager.contexts_path / f"{sample_task_context.id}.json"
        )
        assert context_file.exists()

    def test_update_task_context_invalid(self, task_context_manager):
        """Test updating invalid task context."""
        invalid_context = TaskContext(
            id="", title="Test", description="Test"  # Empty ID should be invalid
        )

        with pytest.raises(ValueError, match="Invalid task context"):
            task_context_manager.update_task_context(invalid_context)

    def test_validate_task_context_valid(
        self, task_context_manager, sample_task_context
    ):
        """Test validation of valid task context."""
        result = task_context_manager.validate_task_context(sample_task_context)

        assert_validation_result(result, should_be_valid=True)

    def test_validate_task_context_empty_id(self, task_context_manager):
        """Test validation of task context with empty ID."""
        context = TaskContext(id="", title="Test", description="Test")

        result = task_context_manager.validate_task_context(context)

        assert_validation_result(result, should_be_valid=False, expected_errors=1)
        assert "ID cannot be empty" in result.errors[0]

    def test_validate_task_context_empty_title(self, task_context_manager):
        """Test validation of task context with empty title."""
        context = TaskContext(id="test_id", title="", description="Test")

        result = task_context_manager.validate_task_context(context)

        assert_validation_result(result, should_be_valid=False, expected_errors=1)
        assert "title cannot be empty" in result.errors[0]

    def test_validate_task_context_self_dependency(self, task_context_manager):
        """Test validation of task context with self-dependency."""
        context = TaskContext(
            id="test_id",
            title="Test",
            description="Test",
            dependencies=[TaskDependency(task_id="test_id", dependency_type="blocks")],
        )

        result = task_context_manager.validate_task_context(context)

        assert_validation_result(result, should_be_valid=False, expected_errors=1)
        assert "cannot depend on itself" in result.errors[0]

    def test_validate_task_context_negative_duration(self, task_context_manager):
        """Test validation of task context with negative duration."""
        context = TaskContext(
            id="test_id",
            title="Test",
            description="Test",
            metadata=TaskMetadata(category="test", estimated_duration=-10),
        )

        result = task_context_manager.validate_task_context(context)

        assert_validation_result(result, should_be_valid=False, expected_errors=1)
        assert "cannot be negative" in result.errors[0]

    def test_get_task_dependencies(self, task_context_manager, sample_task_context):
        """Test getting task dependencies."""
        # Add dependencies
        dep1 = TaskDependency(task_id="dep1", dependency_type="blocks")
        dep2 = TaskDependency(task_id="dep2", dependency_type="requires")
        sample_task_context.dependencies = [dep1, dep2]

        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        dependencies = task_context_manager.get_task_dependencies(
            sample_task_context.id
        )

        assert len(dependencies) == 2
        assert dependencies[0].task_id == "dep1"
        assert dependencies[1].task_id == "dep2"

    def test_get_task_dependencies_not_found(self, task_context_manager):
        """Test getting dependencies for nonexistent task."""
        dependencies = task_context_manager.get_task_dependencies("nonexistent")

        assert len(dependencies) == 0

    def test_add_task_dependency(self, task_context_manager, sample_task_context):
        """Test adding task dependency."""
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        dependency = TaskDependency(
            task_id="other_task",
            dependency_type="blocks",
            description="Test dependency",
        )

        task_context_manager.add_task_dependency(sample_task_context.id, dependency)

        assert len(sample_task_context.dependencies) == 1
        assert sample_task_context.dependencies[0].task_id == "other_task"

    def test_add_task_dependency_self_reference(
        self, task_context_manager, sample_task_context
    ):
        """Test adding self-referencing dependency."""
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        dependency = TaskDependency(
            task_id=sample_task_context.id, dependency_type="blocks"
        )

        with pytest.raises(ValueError, match="cannot depend on itself"):
            task_context_manager.add_task_dependency(sample_task_context.id, dependency)

    def test_add_task_dependency_duplicate(
        self, task_context_manager, sample_task_context
    ):
        """Test adding duplicate dependency."""
        # Add initial dependency
        existing_dep = TaskDependency(task_id="other_task", dependency_type="blocks")
        sample_task_context.dependencies = [existing_dep]
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        # Try to add same dependency
        duplicate_dep = TaskDependency(task_id="other_task", dependency_type="requires")

        task_context_manager.add_task_dependency(sample_task_context.id, duplicate_dep)

        # Should still have only one dependency
        assert len(sample_task_context.dependencies) == 1

    def test_remove_task_dependency(self, task_context_manager, sample_task_context):
        """Test removing task dependency."""
        # Add dependency first
        dependency = TaskDependency(task_id="other_task", dependency_type="blocks")
        sample_task_context.dependencies = [dependency]
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        # Remove dependency
        task_context_manager.remove_task_dependency(
            sample_task_context.id, "other_task"
        )

        assert len(sample_task_context.dependencies) == 0

    def test_remove_task_dependency_not_found(
        self, task_context_manager, sample_task_context
    ):
        """Test removing nonexistent dependency."""
        task_context_manager._contexts[sample_task_context.id] = sample_task_context

        # Should not raise error
        task_context_manager.remove_task_dependency(
            sample_task_context.id, "nonexistent"
        )

        assert len(sample_task_context.dependencies) == 0

    def test_get_task_order_no_dependencies(self, task_context_manager):
        """Test task ordering with no dependencies."""
        # Create tasks without dependencies
        task1 = TaskContext(id="task1", title="Task 1", description="First task")
        task2 = TaskContext(id="task2", title="Task 2", description="Second task")

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        ordered_ids = task_context_manager.get_task_order(["task1", "task2"])

        assert len(ordered_ids) == 2
        assert "task1" in ordered_ids
        assert "task2" in ordered_ids

    def test_get_task_order_with_dependencies(self, task_context_manager):
        """Test task ordering with dependencies."""
        # Create tasks with dependencies
        task1 = TaskContext(id="task1", title="Task 1", description="First task")
        task2 = TaskContext(
            id="task2",
            title="Task 2",
            description="Second task",
            dependencies=[
                TaskDependency(
                    task_id="task1", dependency_type="blocks", is_hard_dependency=True
                )
            ],
        )

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        ordered_ids = task_context_manager.get_task_order(["task1", "task2"])

        assert len(ordered_ids) == 2
        assert ordered_ids.index("task1") < ordered_ids.index("task2")

    def test_visualize_task_graph(self, task_context_manager):
        """Test task graph visualization."""
        # Create tasks with dependencies
        task1 = TaskContext(id="task1", title="Task 1", description="First task")
        task2 = TaskContext(
            id="task2",
            title="Task 2",
            description="Second task",
            dependencies=[TaskDependency(task_id="task1", dependency_type="blocks")],
        )

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        graph = task_context_manager.visualize_task_graph(["task1", "task2"])

        assert isinstance(graph, TaskGraph)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.edges[0] == ("task1", "task2", "blocks")

    def test_has_dependency_cycle_no_cycle(self, task_context_manager):
        """Test cycle detection with no cycles."""
        task1 = TaskContext(id="task1", title="Task 1", description="First task")
        task2 = TaskContext(
            id="task2",
            title="Task 2",
            description="Second task",
            dependencies=[TaskDependency(task_id="task1", dependency_type="blocks")],
        )

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        has_cycle = task_context_manager._has_dependency_cycle("task1")

        assert has_cycle is False

    def test_has_dependency_cycle_with_cycle(self, task_context_manager):
        """Test cycle detection with cycles."""
        task1 = TaskContext(
            id="task1",
            title="Task 1",
            description="First task",
            dependencies=[TaskDependency(task_id="task2", dependency_type="blocks")],
        )
        task2 = TaskContext(
            id="task2",
            title="Task 2",
            description="Second task",
            dependencies=[TaskDependency(task_id="task1", dependency_type="blocks")],
        )

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        has_cycle = task_context_manager._has_dependency_cycle("task1")

        assert has_cycle is True

    def test_search_task_contexts(self, task_context_manager):
        """Test searching task contexts."""
        # Create test contexts
        task1 = TaskContext(
            id="task1",
            title="Frontend Development",
            description="Build React components",
            metadata=TaskMetadata(category="development", tags=["frontend", "react"]),
        )
        task2 = TaskContext(
            id="task2",
            title="Backend API",
            description="Create REST API endpoints",
            metadata=TaskMetadata(category="development", tags=["backend", "api"]),
        )

        task_context_manager._contexts["task1"] = task1
        task_context_manager._contexts["task2"] = task2

        # Search by query
        results = task_context_manager.search_task_contexts(query="React")

        assert len(results) == 1
        assert results[0].id == "task1"

    def test_task_context_to_dict(self, task_context_manager, sample_task_context):
        """Test converting task context to dictionary."""
        context_dict = task_context_manager._task_context_to_dict(sample_task_context)

        assert isinstance(context_dict, dict)
        assert context_dict["id"] == sample_task_context.id
        assert context_dict["title"] == sample_task_context.title
        assert context_dict["description"] == sample_task_context.description
        assert context_dict["status"] == sample_task_context.status.value
        assert "metadata" in context_dict
        assert (
            context_dict["metadata"]["category"]
            == sample_task_context.metadata.category
        )

    def test_parse_task_context(self, task_context_manager):
        """Test parsing task context from dictionary."""
        context_data = {
            "id": "test_task",
            "title": "Test Task",
            "description": "A test task",
            "status": "pending",
            "metadata": {
                "category": "testing",
                "priority": "high",
                "estimated_duration": 60,
                "tags": ["test"],
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
            },
            "dependencies": [
                {
                    "task_id": "other_task",
                    "dependency_type": "blocks",
                    "is_hard_dependency": True,
                }
            ],
            "sub_tasks": [],
            "parent_task": None,
            "template_id": None,
            "context_data": {},
        }

        context = task_context_manager._parse_task_context(context_data)

        assert isinstance(context, TaskContext)
        assert context.id == "test_task"
        assert context.title == "Test Task"
        assert context.status == TaskStatus.PENDING
        assert context.metadata.category == "testing"
        assert context.metadata.priority == TaskPriority.HIGH
        assert len(context.dependencies) == 1
        assert context.dependencies[0].task_id == "other_task"


class TestTaskStatus:
    """Test cases for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTaskPriority:
    """Test cases for TaskPriority enum."""

    def test_task_priority_values(self):
        """Test TaskPriority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"


class TestTaskDependency:
    """Test cases for TaskDependency dataclass."""

    def test_dependency_creation(self):
        """Test creating a TaskDependency instance."""
        dependency = TaskDependency(
            task_id="other_task",
            dependency_type="blocks",
            description="Task must complete before this one",
            is_hard_dependency=True,
        )

        assert dependency.task_id == "other_task"
        assert dependency.dependency_type == "blocks"
        assert dependency.description == "Task must complete before this one"
        assert dependency.is_hard_dependency is True


class TestTaskMetadata:
    """Test cases for TaskMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating TaskMetadata instance."""
        metadata = TaskMetadata(
            category="development",
            priority=TaskPriority.HIGH,
            estimated_duration=120,
            tags=["frontend", "react"],
            assignee="developer@example.com",
            notes=["Initial implementation", "Needs review"],
        )

        assert metadata.category == "development"
        assert metadata.priority == TaskPriority.HIGH
        assert metadata.estimated_duration == 120
        assert metadata.tags == ["frontend", "react"]
        assert metadata.assignee == "developer@example.com"
        assert len(metadata.notes) == 2


class TestTaskDefinition:
    """Test cases for TaskDefinition dataclass."""

    def test_definition_creation(self):
        """Test creating TaskDefinition instance."""
        definition = TaskDefinition(
            title="Implement feature",
            description="Add new feature to the application",
            category="development",
            priority=TaskPriority.MEDIUM,
            estimated_duration=180,
            tags=["feature", "backend"],
        )

        assert definition.title == "Implement feature"
        assert definition.description == "Add new feature to the application"
        assert definition.category == "development"
        assert definition.priority == TaskPriority.MEDIUM
        assert definition.estimated_duration == 180
        assert definition.tags == ["feature", "backend"]


class TestTaskGraph:
    """Test cases for TaskGraph dataclass."""

    def test_graph_creation(self, sample_task_context):
        """Test creating TaskGraph instance."""
        nodes = {"task1": sample_task_context}
        edges = [("task1", "task2", "blocks")]
        cycles = [["task1", "task2", "task1"]]

        graph = TaskGraph(nodes=nodes, edges=edges, cycles=cycles)

        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1
        assert len(graph.cycles) == 1
        assert graph.edges[0] == ("task1", "task2", "blocks")

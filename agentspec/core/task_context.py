"""
Task Context Management

This module provides the TaskContextManager class for managing enhanced task contexts
with structured metadata, dependency tracking, and template support.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import jsonschema
    from jsonschema import ValidationError as JsonSchemaValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None  # type: ignore
    JsonSchemaValidationError = Exception  # type: ignore
    HAS_JSONSCHEMA = False

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks"""

    task_id: str
    dependency_type: str  # blocks, requires, suggests, conflicts_with
    description: Optional[str] = None
    is_hard_dependency: bool = True  # Hard vs soft dependency


@dataclass
class TaskMetadata:
    """Structured metadata for a task context"""

    category: str
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = None  # in minutes
    actual_duration: Optional[int] = None  # in minutes
    tags: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Basic task definition for creating task contexts"""

    title: str
    description: str
    category: str
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


@dataclass
class TaskContext:
    """Enhanced task context with structured metadata and dependencies"""

    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: TaskMetadata = field(
        default_factory=lambda: TaskMetadata(category="general")
    )
    dependencies: List[TaskDependency] = field(default_factory=list)
    sub_tasks: List[str] = field(default_factory=list)  # IDs of sub-tasks
    parent_task: Optional[str] = None  # ID of parent task
    template_id: Optional[str] = None  # Template used to create this context
    context_data: Dict[str, Any] = field(
        default_factory=dict
    )  # Additional context data

    def __post_init__(self) -> None:
        """Initialize timestamps if not set"""
        if not self.metadata.created_at:
            self.metadata.created_at = datetime.now()
        self.metadata.updated_at = datetime.now()


@dataclass
class TaskGraph:
    """Represents a task dependency graph"""

    nodes: Dict[str, TaskContext]
    edges: List[Tuple[str, str, str]]  # (from_task, to_task, dependency_type)
    cycles: List[List[str]] = field(default_factory=list)  # Detected cycles


@dataclass
class ValidationResult:
    """Result of task context validation"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


class TaskContextManager:
    """
    Manages enhanced task contexts with structured metadata and dependencies.

    This class provides functionality to:
    - Create and manage task contexts with rich metadata
    - Track task dependencies and relationships
    - Validate task context data
    - Support task context templates and inheritance
    - Provide search and filtering capabilities
    """

    def __init__(
        self,
        contexts_path: Optional[Path] = None,
        schema_path: Optional[Path] = None,
    ):
        """
        Initialize the task context manager.

        Args:
            contexts_path: Path to the task contexts directory
            schema_path: Path to the task context schema file
        """
        self.contexts_path = contexts_path or Path.cwd() / "task_contexts"
        self.schema_path = (
            schema_path
            or Path(__file__).parent.parent
            / "data"
            / "schemas"
            / "task_context_schema.json"
        )

        self._contexts: Dict[str, TaskContext] = {}
        self._schema: Optional[Dict] = None

        # Template support attributes (for compatibility with enhanced functions)
        self.template_manager: Optional[Any] = None
        self.__original_init__: Optional[Any] = None
        self._loaded = False

        # Ensure contexts directory exists
        self.contexts_path.mkdir(parents=True, exist_ok=True)

        # Load schema
        self._load_schema()

    def _load_schema(self) -> None:
        """Load the JSON schema for task context validation"""
        try:
            if self.schema_path.exists():
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    self._schema = json.load(f)
                logger.debug(f"Loaded task context schema from {self.schema_path}")
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
                # Create a basic schema if none exists
                self._create_default_schema()
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            self._schema = None

    def _create_default_schema(self) -> None:
        """Create a default schema for task contexts"""
        default_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Task Context Schema",
            "description": "Schema for validating AgentSpec task contexts",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the task context",
                },
                "title": {
                    "type": "string",
                    "description": "Task title",
                    "minLength": 1,
                },
                "description": {
                    "type": "string",
                    "description": "Task description",
                    "minLength": 1,
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "pending",
                        "in_progress",
                        "completed",
                        "blocked",
                        "cancelled",
                    ],
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                        "estimated_duration": {"type": ["integer", "null"]},
                        "actual_duration": {"type": ["integer", "null"]},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "assignee": {"type": ["string", "null"]},
                        "created_by": {"type": ["string", "null"]},
                        "created_at": {
                            "type": ["string", "null"],
                            "format": "date-time",
                        },
                        "updated_at": {
                            "type": ["string", "null"],
                            "format": "date-time",
                        },
                        "due_date": {
                            "type": ["string", "null"],
                            "format": "date-time",
                        },
                        "completion_date": {
                            "type": ["string", "null"],
                            "format": "date-time",
                        },
                        "notes": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "custom_fields": {"type": "object"},
                    },
                    "required": ["category"],
                },
                "dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "dependency_type": {"type": "string"},
                            "description": {"type": ["string", "null"]},
                            "is_hard_dependency": {"type": "boolean"},
                        },
                        "required": ["task_id", "dependency_type"],
                    },
                },
                "sub_tasks": {"type": "array", "items": {"type": "string"}},
                "parent_task": {"type": ["string", "null"]},
                "template_id": {"type": ["string", "null"]},
                "context_data": {"type": "object"},
            },
            "required": ["id", "title", "description", "status", "metadata"],
            "additionalProperties": False,
        }

        # Save the default schema
        try:
            self.schema_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schema_path, "w", encoding="utf-8") as f:
                json.dump(default_schema, f, indent=2)
            self._schema = default_schema
            logger.info(f"Created default task context schema at {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to create default schema: {e}")

    def create_task_context(self, task: TaskDefinition) -> TaskContext:
        """
        Create a new task context from a task definition.

        Args:
            task: TaskDefinition containing basic task information

        Returns:
            Created TaskContext

        Raises:
            ValueError: If task definition is invalid
        """
        # Generate unique ID
        task_id = str(uuid.uuid4())

        # Create metadata from task definition
        metadata = TaskMetadata(
            category=task.category,
            priority=task.priority,
            estimated_duration=task.estimated_duration,
            tags=task.tags.copy(),
            assignee=task.assignee,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        if task.due_date:
            metadata.due_date = task.due_date

        # Create task context
        context = TaskContext(
            id=task_id,
            title=task.title,
            description=task.description,
            status=TaskStatus.PENDING,
            metadata=metadata,
        )

        # Validate the context
        validation_result = self.validate_task_context(context)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid task context: {validation_result.errors}")

        # Save the context
        self._save_task_context(context)

        # Add to loaded contexts
        self._contexts[task_id] = context

        logger.info(f"Created task context {task_id}: {task.title}")
        return context

    def load_task_context(self, task_id: str) -> Optional[TaskContext]:
        """
        Load a task context by ID.

        Args:
            task_id: ID of the task context to load

        Returns:
            TaskContext if found, None otherwise
        """
        # Check if already loaded
        if task_id in self._contexts:
            return self._contexts[task_id]

        # Try to load from file
        context_file = self.contexts_path / f"{task_id}.json"
        if not context_file.exists():
            logger.warning(f"Task context file not found: {context_file}")
            return None

        try:
            with open(context_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            context = self._parse_task_context(data)

            # Validate the loaded context
            validation_result = self.validate_task_context(context)
            if not validation_result.is_valid:
                logger.error(
                    f"Invalid task context {task_id}: {validation_result.errors}"
                )
                return None

            # Add to loaded contexts
            self._contexts[task_id] = context

            logger.debug(f"Loaded task context {task_id}")
            return context

        except Exception as e:
            logger.error(f"Failed to load task context {task_id}: {e}")
            return None

    def update_task_context(self, context: TaskContext) -> None:
        """
        Update an existing task context.

        Args:
            context: TaskContext to update

        Raises:
            ValueError: If context is invalid
        """
        # Update timestamp
        context.metadata.updated_at = datetime.now()

        # Validate the context
        validation_result = self.validate_task_context(context)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid task context: {validation_result.errors}")

        # Save the context
        self._save_task_context(context)

        # Update in loaded contexts
        self._contexts[context.id] = context

        logger.debug(f"Updated task context {context.id}")

    def _save_task_context(self, context: TaskContext) -> None:
        """Save task context to file"""
        context_file = self.contexts_path / f"{context.id}.json"

        try:
            # Convert to dictionary for JSON serialization
            context_dict = self._task_context_to_dict(context)

            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(context_dict, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save task context {context.id}: {e}")
            raise

    def _parse_task_context(self, data: Dict) -> TaskContext:
        """Parse task context data from JSON into TaskContext object"""
        # Parse metadata
        metadata_data = data.get("metadata", {})

        # Parse datetime fields
        created_at = None
        updated_at = None
        due_date = None
        completion_date = None

        if metadata_data.get("created_at"):
            created_at = datetime.fromisoformat(
                metadata_data["created_at"].replace("Z", "+00:00")
            )
        if metadata_data.get("updated_at"):
            updated_at = datetime.fromisoformat(
                metadata_data["updated_at"].replace("Z", "+00:00")
            )
        if metadata_data.get("due_date"):
            due_date = datetime.fromisoformat(
                metadata_data["due_date"].replace("Z", "+00:00")
            )
        if metadata_data.get("completion_date"):
            completion_date = datetime.fromisoformat(
                metadata_data["completion_date"].replace("Z", "+00:00")
            )

        metadata = TaskMetadata(
            category=metadata_data.get("category", "general"),
            priority=TaskPriority(metadata_data.get("priority", "medium")),
            estimated_duration=metadata_data.get("estimated_duration"),
            actual_duration=metadata_data.get("actual_duration"),
            tags=metadata_data.get("tags", []),
            assignee=metadata_data.get("assignee"),
            created_by=metadata_data.get("created_by"),
            created_at=created_at,
            updated_at=updated_at,
            due_date=due_date,
            completion_date=completion_date,
            notes=metadata_data.get("notes", []),
            custom_fields=metadata_data.get("custom_fields", {}),
        )

        # Parse dependencies
        dependencies = []
        for dep_data in data.get("dependencies", []):
            dependencies.append(
                TaskDependency(
                    task_id=dep_data["task_id"],
                    dependency_type=dep_data["dependency_type"],
                    description=dep_data.get("description"),
                    is_hard_dependency=dep_data.get("is_hard_dependency", True),
                )
            )

        return TaskContext(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TaskStatus(data.get("status", "pending")),
            metadata=metadata,
            dependencies=dependencies,
            sub_tasks=data.get("sub_tasks", []),
            parent_task=data.get("parent_task"),
            template_id=data.get("template_id"),
            context_data=data.get("context_data", {}),
        )

    def _task_context_to_dict(self, context: TaskContext) -> Dict:
        """Convert TaskContext object to dictionary for JSON serialization"""
        # Convert metadata
        metadata_dict = {
            "category": context.metadata.category,
            "priority": context.metadata.priority.value,
            "estimated_duration": context.metadata.estimated_duration,
            "actual_duration": context.metadata.actual_duration,
            "tags": context.metadata.tags,
            "assignee": context.metadata.assignee,
            "created_by": context.metadata.created_by,
            "notes": context.metadata.notes,
            "custom_fields": context.metadata.custom_fields,
        }

        # Add datetime fields if they exist
        if context.metadata.created_at:
            metadata_dict["created_at"] = context.metadata.created_at.isoformat()
        if context.metadata.updated_at:
            metadata_dict["updated_at"] = context.metadata.updated_at.isoformat()
        if context.metadata.due_date:
            metadata_dict["due_date"] = context.metadata.due_date.isoformat()
        if context.metadata.completion_date:
            metadata_dict["completion_date"] = (
                context.metadata.completion_date.isoformat()
            )

        # Convert dependencies
        dependencies_list = []
        for dep in context.dependencies:
            dep_dict = {
                "task_id": dep.task_id,
                "dependency_type": dep.dependency_type,
                "is_hard_dependency": dep.is_hard_dependency,
            }
            if dep.description:
                dep_dict["description"] = dep.description
            dependencies_list.append(dep_dict)

        return {
            "id": context.id,
            "title": context.title,
            "description": context.description,
            "status": context.status.value,
            "metadata": metadata_dict,
            "dependencies": dependencies_list,
            "sub_tasks": context.sub_tasks,
            "parent_task": context.parent_task,
            "template_id": context.template_id,
            "context_data": context.context_data,
        }

    def validate_task_context(self, context: TaskContext) -> ValidationResult:
        """
        Validate a task context against the schema and business rules.

        Args:
            context: TaskContext to validate

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        # Convert context to dict for schema validation
        context_dict = self._task_context_to_dict(context)

        # Schema validation
        if self._schema and HAS_JSONSCHEMA:
            try:
                jsonschema.validate(context_dict, self._schema)
            except JsonSchemaValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")
        elif self._schema and not HAS_JSONSCHEMA:
            warnings.append("jsonschema not available, skipping schema validation")

        # Business rule validation
        if not context.id:
            errors.append("Task context ID cannot be empty")

        if not context.title or not context.title.strip():
            errors.append("Task title cannot be empty")

        if not context.description or not context.description.strip():
            errors.append("Task description cannot be empty")

        if not context.metadata.category:
            errors.append("Task category cannot be empty")

        # Validate dependencies
        for dep in context.dependencies:
            if not dep.task_id:
                errors.append("Dependency task ID cannot be empty")
            if not dep.dependency_type:
                errors.append("Dependency type cannot be empty")
            if dep.task_id == context.id:
                errors.append("Task cannot depend on itsel")

        # Validate sub-tasks
        if context.id in context.sub_tasks:
            errors.append("Task cannot be its own sub-task")

        # Validate parent task
        if context.parent_task == context.id:
            errors.append("Task cannot be its own parent")

        # Duration validation
        if (
            context.metadata.estimated_duration is not None
            and context.metadata.estimated_duration < 0
        ):
            errors.append("Estimated duration cannot be negative")

        if (
            context.metadata.actual_duration is not None
            and context.metadata.actual_duration < 0
        ):
            errors.append("Actual duration cannot be negative")

        # Date validation
        if (
            context.metadata.due_date
            and context.metadata.created_at
            and context.metadata.due_date < context.metadata.created_at
        ):
            warnings.append("Due date is before creation date")

        if (
            context.metadata.completion_date
            and context.metadata.created_at
            and context.metadata.completion_date < context.metadata.created_at
        ):
            errors.append("Completion date cannot be before creation date")

        # Status validation
        if (
            context.status == TaskStatus.COMPLETED
            and not context.metadata.completion_date
        ):
            warnings.append("Completed task should have completion date")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_task_dependencies(self, task_id: str) -> List[TaskDependency]:
        """
        Get all dependencies for a specific task.

        Args:
            task_id: ID of the task to get dependencies for

        Returns:
            List of TaskDependency objects
        """
        context = self.load_task_context(task_id)
        if not context:
            return []

        return context.dependencies.copy()

    def add_task_dependency(self, task_id: str, dependency: TaskDependency) -> None:
        """
        Add a dependency to a task.

        Args:
            task_id: ID of the task to add dependency to
            dependency: TaskDependency to add

        Raises:
            ValueError: If task not found or dependency creates a cycle
        """
        context = self.load_task_context(task_id)
        if not context:
            raise ValueError(f"Task context not found: {task_id}")

        # Check for self-dependency
        if dependency.task_id == task_id:
            raise ValueError("Task cannot depend on itsel")

        # Check if dependency already exists
        existing_deps = [dep.task_id for dep in context.dependencies]
        if dependency.task_id in existing_deps:
            logger.warning(
                f"Dependency already exists: {task_id} -> {dependency.task_id}"
            )
            return

        # Add dependency
        context.dependencies.append(dependency)

        # Check for cycles
        if self._has_dependency_cycle(task_id):
            # Remove the dependency that created the cycle
            context.dependencies.pop()
            raise ValueError(
                f"Adding dependency would create a cycle: {task_id} -> {dependency.task_id}"
            )

        # Update the context
        self.update_task_context(context)

        logger.info(
            f"Added dependency: {task_id} -> {dependency.task_id} ({dependency.dependency_type})"
        )

    def remove_task_dependency(self, task_id: str, dependency_task_id: str) -> None:
        """
        Remove a dependency from a task.

        Args:
            task_id: ID of the task to remove dependency from
            dependency_task_id: ID of the dependency task to remove
        """
        context = self.load_task_context(task_id)
        if not context:
            logger.warning(f"Task context not found: {task_id}")
            return

        # Find and remove the dependency
        original_count = len(context.dependencies)
        context.dependencies = [
            dep for dep in context.dependencies if dep.task_id != dependency_task_id
        ]

        if len(context.dependencies) < original_count:
            self.update_task_context(context)
            logger.info(f"Removed dependency: {task_id} -> {dependency_task_id}")
        else:
            logger.warning(f"Dependency not found: {task_id} -> {dependency_task_id}")

    def _has_dependency_cycle(
        self, start_task_id: str, visited: Optional[Set[str]] = None
    ) -> bool:
        """
        Check if adding a dependency would create a cycle.

        Args:
            start_task_id: ID of the task to start checking from
            visited: Set of already visited task IDs

        Returns:
            True if a cycle is detected, False otherwise
        """
        if visited is None:
            visited = set()

        if start_task_id in visited:
            return True

        visited.add(start_task_id)

        context = self.load_task_context(start_task_id)
        if not context:
            return False

        # Check all dependencies
        for dependency in context.dependencies:
            if self._has_dependency_cycle(dependency.task_id, visited.copy()):
                return True

        return False

    def get_task_order(self, task_ids: List[str]) -> List[str]:
        """
        Get tasks ordered by their dependencies (topological sort).

        Args:
            task_ids: List of task IDs to order

        Returns:
            List of task IDs in dependency order
        """
        # Build dependency graph
        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}

        # Initialize
        for task_id in task_ids:
            graph[task_id] = []
            in_degree[task_id] = 0

        # Build edges
        for task_id in task_ids:
            context = self.load_task_context(task_id)
            if context:
                for dep in context.dependencies:
                    if dep.task_id in task_ids and dep.is_hard_dependency:
                        graph[dep.task_id].append(task_id)
                        in_degree[task_id] += 1

        # Topological sort using Kahn's algorithm
        queue = [task_id for task_id in task_ids if in_degree[task_id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(task_ids):
            logger.warning("Dependency cycle detected in task ordering")
            # Return original order if cycle detected
            return task_ids

        return result

    def visualize_task_graph(self, task_ids: List[str]) -> TaskGraph:
        """
        Create a visualization of task dependencies.

        Args:
            task_ids: List of task IDs to include in the graph

        Returns:
            TaskGraph object with nodes, edges, and cycle information
        """
        nodes = {}
        edges = []

        # Load all task contexts
        for task_id in task_ids:
            context = self.load_task_context(task_id)
            if context:
                nodes[task_id] = context

                # Add edges for dependencies
                for dep in context.dependencies:
                    if dep.task_id in task_ids:
                        edges.append((dep.task_id, task_id, dep.dependency_type))

        # Detect cycles
        cycles = self._detect_cycles(task_ids)

        return TaskGraph(nodes=nodes, edges=edges, cycles=cycles)

    def _detect_cycles(self, task_ids: List[str]) -> List[List[str]]:
        """
        Detect all cycles in the task dependency graph.

        Args:
            task_ids: List of task IDs to check

        Returns:
            List of cycles, where each cycle is a list of task IDs
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(task_id: str, path: List[str]) -> None:
            if task_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(task_id)
                cycle = path[cycle_start:] + [task_id]
                cycles.append(cycle)
                return

            if task_id in visited:
                return

            visited.add(task_id)
            rec_stack.add(task_id)

            context = self.load_task_context(task_id)
            if context:
                for dep in context.dependencies:
                    if dep.task_id in task_ids and dep.is_hard_dependency:
                        dfs(dep.task_id, path + [task_id])

            rec_stack.remove(task_id)

        for task_id in task_ids:
            if task_id not in visited:
                dfs(task_id, [])

        return cycles

    def search_task_contexts(
        self,
        query: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        due_before: Optional[datetime] = None,
    ) -> List[TaskContext]:
        """
        Search and filter task contexts based on various criteria.

        Args:
            query: Text search in title and description
            status: Filter by task status
            category: Filter by category
            priority: Filter by priority
            assignee: Filter by assignee
            tags: Filter by tags (task must have all specified tags)
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            due_after: Filter by due date (after)
            due_before: Filter by due date (before)

        Returns:
            List of matching TaskContext objects
        """
        # Load all contexts if not already loaded
        self._load_all_contexts()

        results = []

        for context in self._contexts.values():
            # Text search
            if query:
                query_lower = query.lower()
                if (
                    query_lower not in context.title.lower()
                    and query_lower not in context.description.lower()
                ):
                    continue

            # Status filter
            if status and context.status != status:
                continue

            # Category filter
            if category and context.metadata.category != category:
                continue

            # Priority filter
            if priority and context.metadata.priority != priority:
                continue

            # Assignee filter
            if assignee and context.metadata.assignee != assignee:
                continue

            # Tags filter (must have all specified tags)
            if tags:
                context_tags = set(context.metadata.tags)
                required_tags = set(tags)
                if not required_tags.issubset(context_tags):
                    continue

            # Date filters
            if created_after and context.metadata.created_at:
                if context.metadata.created_at < created_after:
                    continue

            if created_before and context.metadata.created_at:
                if context.metadata.created_at > created_before:
                    continue

            if due_after and context.metadata.due_date:
                if context.metadata.due_date < due_after:
                    continue

            if due_before and context.metadata.due_date:
                if context.metadata.due_date > due_before:
                    continue

            results.append(context)

        return results

    def _load_all_contexts(self) -> None:
        """Load all task contexts from files"""
        if self._loaded:
            return

        # Find all JSON files in the contexts directory
        json_files = list(self.contexts_path.glob("*.json"))

        for json_file in json_files:
            try:
                task_id = json_file.stem
                if task_id not in self._contexts:
                    self.load_task_context(task_id)
            except Exception as e:
                logger.error(f"Failed to load task context from {json_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._contexts)} task contexts")

    def get_all_categories(self) -> Set[str]:
        """
        Get all unique categories from loaded task contexts.

        Returns:
            Set of category names
        """
        self._load_all_contexts()
        return {context.metadata.category for context in self._contexts.values()}

    def get_all_assignees(self) -> Set[str]:
        """
        Get all unique assignees from loaded task contexts.

        Returns:
            Set of assignee names
        """
        self._load_all_contexts()
        assignees = set()
        for context in self._contexts.values():
            if context.metadata.assignee:
                assignees.add(context.metadata.assignee)
        return assignees

    def get_all_tags(self) -> Set[str]:
        """
        Get all unique tags from loaded task contexts.

        Returns:
            Set of tag names
        """
        self._load_all_contexts()
        tags = set()
        for context in self._contexts.values():
            tags.update(context.metadata.tags)
        return tags

    def delete_task_context(self, task_id: str) -> bool:
        """
        Delete a task context.

        Args:
            task_id: ID of the task context to delete

        Returns:
            True if deleted successfully, False if not found
        """
        # Remove from memory
        if task_id in self._contexts:
            del self._contexts[task_id]

        # Remove file
        context_file = self.contexts_path / f"{task_id}.json"
        if context_file.exists():
            try:
                context_file.unlink()
                logger.info(f"Deleted task context {task_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete task context file {task_id}: {e}")
                return False

        return False

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about task contexts.

        Returns:
            Dictionary with various statistics
        """
        self._load_all_contexts()

        total_tasks = len(self._contexts)
        if total_tasks == 0:
            return {"total_tasks": 0}

        # Status distribution
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = 0

        # Priority distribution
        priority_counts = {}
        for priority in TaskPriority:
            priority_counts[priority.value] = 0

        # Category distribution
        category_counts: Dict[str, int] = {}

        # Duration statistics
        estimated_durations = []
        actual_durations = []

        for context in self._contexts.values():
            # Status
            status_counts[context.status.value] += 1

            # Priority
            priority_counts[context.metadata.priority.value] += 1

            # Category
            category = context.metadata.category
            category_counts[category] = category_counts.get(category, 0) + 1

            # Durations
            if context.metadata.estimated_duration:
                estimated_durations.append(context.metadata.estimated_duration)
            if context.metadata.actual_duration:
                actual_durations.append(context.metadata.actual_duration)

        stats = {
            "total_tasks": total_tasks,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "category_distribution": category_counts,
            "total_categories": len(category_counts),
            "total_assignees": len(self.get_all_assignees()),
            "total_tags": len(self.get_all_tags()),
        }

        # Duration statistics
        if estimated_durations:
            stats["estimated_duration"] = {
                "min": min(estimated_durations),
                "max": max(estimated_durations),
                "avg": sum(estimated_durations) / len(estimated_durations),
                "total": sum(estimated_durations),
            }

        if actual_durations:
            stats["actual_duration"] = {
                "min": min(actual_durations),
                "max": max(actual_durations),
                "avg": sum(actual_durations) / len(actual_durations),
                "total": sum(actual_durations),
            }

        return stats

    def reload(self) -> None:
        """Reload all task contexts from files"""
        self._loaded = False
        self._contexts.clear()
        self._load_all_contexts()

    def export_task_graph_dot(
        self, task_ids: List[str], include_status: bool = True
    ) -> str:
        """
        Export task dependency graph in DOT format for graphviz visualization.

        Args:
            task_ids: List of task IDs to include in the graph
            include_status: Whether to include status information in node labels

        Returns:
            DOT format string for graphviz
        """
        graph = self.visualize_task_graph(task_ids)

        dot_lines = ["digraph TaskDependencies {"]
        dot_lines.append("  rankdir=TB;")
        dot_lines.append("  node [shape=box, style=rounded];")

        # Add nodes
        for task_id, context in graph.nodes.items():
            label = context.title.replace('"', '\\"')

            if include_status:
                label += f"\\n[{context.status.value}]"
                if context.metadata.priority != TaskPriority.MEDIUM:
                    label += f"\\n{context.metadata.priority.value} priority"

            # Color based on status
            color = {
                TaskStatus.PENDING: "lightblue",
                TaskStatus.IN_PROGRESS: "yellow",
                TaskStatus.COMPLETED: "lightgreen",
                TaskStatus.BLOCKED: "orange",
                TaskStatus.CANCELLED: "lightgray",
            }.get(context.status, "white")

            dot_lines.append(
                f'  "{task_id}" [label="{label}", fillcolor="{color}", style="filled,rounded"];'
            )

        # Add edges
        for from_task, to_task, dep_type in graph.edges:
            style = "solid" if dep_type in ["blocks", "requires"] else "dashed"
            color = (
                "red"
                if dep_type == "blocks"
                else "blue" if dep_type == "requires" else "gray"
            )

            dot_lines.append(
                f'  "{from_task}" -> "{to_task}" [label="{dep_type}", style="{style}", color="{color}"];'
            )

        # Highlight cycles
        for cycle in graph.cycles:
            if len(cycle) > 1:
                for i in range(len(cycle) - 1):
                    dot_lines.append(
                        f'  "{cycle[i]}" -> "{cycle[i+1]}" [color="red", penwidth=3];'
                    )

        dot_lines.append("}")

        return "\n".join(dot_lines)

    def get_task_progress_summary(
        self, task_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of task progress for visualization.

        Args:
            task_ids: Optional list of task IDs to include. If None, includes all tasks.

        Returns:
            Dictionary with progress summary information
        """
        if task_ids is None:
            self._load_all_contexts()
            contexts = list(self._contexts.values())
        else:
            contexts = [
                ctx
                for tid in task_ids
                if (ctx := self.load_task_context(tid)) is not None
            ]

        if not contexts:
            return {"total_tasks": 0}

        total_tasks = len(contexts)
        completed_tasks = sum(
            1 for ctx in contexts if ctx.status == TaskStatus.COMPLETED
        )
        in_progress_tasks = sum(
            1 for ctx in contexts if ctx.status == TaskStatus.IN_PROGRESS
        )
        blocked_tasks = sum(1 for ctx in contexts if ctx.status == TaskStatus.BLOCKED)

        # Calculate estimated vs actual time
        total_estimated = sum(ctx.metadata.estimated_duration or 0 for ctx in contexts)
        total_actual = sum(
            ctx.metadata.actual_duration or 0
            for ctx in contexts
            if ctx.metadata.actual_duration
        )

        # Progress by category
        category_progress: Dict[str, Dict[str, Any]] = {}
        for ctx in contexts:
            category = ctx.metadata.category
            if category not in category_progress:
                category_progress[category] = {"total": 0, "completed": 0}

            category_progress[category]["total"] += 1
            if ctx.status == TaskStatus.COMPLETED:
                category_progress[category]["completed"] += 1

        # Calculate completion percentage for each category
        for category_data in category_progress.values():
            category_data["completion_rate"] = (
                category_data["completed"] / category_data["total"] * 100
                if category_data["total"] > 0
                else 0
            )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "blocked_tasks": blocked_tasks,
            "completion_rate": (
                completed_tasks / total_tasks * 100 if total_tasks > 0 else 0
            ),
            "total_estimated_time": total_estimated,
            "total_actual_time": total_actual,
            "time_variance": (
                total_actual - total_estimated if total_estimated > 0 else 0
            ),
            "category_progress": category_progress,
            "status_distribution": {
                "pending": sum(
                    1 for ctx in contexts if ctx.status == TaskStatus.PENDING
                ),
                "in_progress": in_progress_tasks,
                "completed": completed_tasks,
                "blocked": blocked_tasks,
                "cancelled": sum(
                    1 for ctx in contexts if ctx.status == TaskStatus.CANCELLED
                ),
            },
        }


@dataclass
class TaskContextTemplate:
    """Template for creating task contexts"""

    id: str
    name: str
    description: str
    category: str
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    default_dependencies: List[str] = field(default_factory=list)  # Template IDs
    context_data_template: Dict[str, Any] = field(default_factory=dict)
    inheritance: Optional[str] = None  # Parent template ID
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskContextTemplateManager:
    """Manages task context templates"""

    def __init__(self, templates_path: Optional[Path] = None):
        """
        Initialize the template manager.

        Args:
            templates_path: Path to the task context templates directory
        """
        self.templates_path = (
            templates_path
            or Path(__file__).parent.parent / "data" / "templates" / "task_contexts"
        )
        self._templates: Dict[str, TaskContextTemplate] = {}
        self._loaded = False

        # Ensure templates directory exists
        self.templates_path.mkdir(parents=True, exist_ok=True)

        # Create default templates if none exist
        self._create_default_templates()

    def _create_default_templates(self) -> None:
        """Create default task context templates"""
        default_templates = [
            TaskContextTemplate(
                id="development_task",
                name="Development Task",
                description="Template for general development tasks",
                category="development",
                priority=TaskPriority.MEDIUM,
                estimated_duration=120,  # 2 hours
                tags=["development", "coding"],
                context_data_template={
                    "files_to_modify": [],
                    "testing_required": True,
                    "documentation_required": False,
                },
            ),
            TaskContextTemplate(
                id="bug_fix",
                name="Bug Fix",
                description="Template for bug fixing tasks",
                category="maintenance",
                priority=TaskPriority.HIGH,
                estimated_duration=60,  # 1 hour
                tags=["bug", "fix", "maintenance"],
                context_data_template={
                    "bug_report_id": "",
                    "reproduction_steps": [],
                    "affected_components": [],
                    "testing_required": True,
                },
            ),
            TaskContextTemplate(
                id="feature_implementation",
                name="Feature Implementation",
                description="Template for implementing new features",
                category="feature",
                priority=TaskPriority.MEDIUM,
                estimated_duration=240,  # 4 hours
                tags=["feature", "implementation", "development"],
                context_data_template={
                    "requirements": [],
                    "design_document": "",
                    "testing_strategy": "",
                    "documentation_required": True,
                },
            ),
            TaskContextTemplate(
                id="testing_task",
                name="Testing Task",
                description="Template for testing tasks",
                category="testing",
                priority=TaskPriority.MEDIUM,
                estimated_duration=90,  # 1.5 hours
                tags=["testing", "qa", "validation"],
                context_data_template={
                    "test_type": "unit",  # unit, integration, e2e
                    "coverage_target": 80,
                    "test_cases": [],
                    "automation_required": True,
                },
            ),
            TaskContextTemplate(
                id="documentation_task",
                name="Documentation Task",
                description="Template for documentation tasks",
                category="documentation",
                priority=TaskPriority.LOW,
                estimated_duration=60,  # 1 hour
                tags=["documentation", "writing"],
                context_data_template={
                    "document_type": "user_guide",  # user_guide, api_docs, technical_spec
                    "target_audience": "developers",
                    "format": "markdown",
                    "review_required": True,
                },
            ),
        ]

        for template in default_templates:
            template_file = self.templates_path / f"{template.id}.json"
            if not template_file.exists():
                self._save_template(template)

    def load_templates(self) -> Dict[str, TaskContextTemplate]:
        """
        Load all task context templates from files.

        Returns:
            Dictionary mapping template IDs to TaskContextTemplate objects
        """
        if self._loaded:
            return self._templates

        self._templates.clear()

        # Find all JSON files in the templates directory
        json_files = list(self.templates_path.glob("*.json"))

        for json_file in json_files:
            try:
                self._load_template_file(json_file)
            except Exception as e:
                logger.error(f"Failed to load template file {json_file}: {e}")

        # Resolve template inheritance
        self._resolve_template_inheritance()

        self._loaded = True
        logger.info(f"Loaded {len(self._templates)} task context templates")

        return self._templates

    def _load_template_file(self, file_path: Path) -> None:
        """Load template from a single JSON file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        template = self._parse_template(data)
        self._templates[template.id] = template

    def _parse_template(self, data: Dict) -> TaskContextTemplate:
        """Parse template data from JSON into TaskContextTemplate object"""
        return TaskContextTemplate(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            priority=TaskPriority(data.get("priority", "medium")),
            estimated_duration=data.get("estimated_duration"),
            tags=data.get("tags", []),
            default_dependencies=data.get("default_dependencies", []),
            context_data_template=data.get("context_data_template", {}),
            inheritance=data.get("inheritance"),
            metadata=data.get("metadata", {}),
        )

    def _resolve_template_inheritance(self) -> None:
        """Resolve template inheritance relationships"""
        for template in self._templates.values():
            if template.inheritance:
                self._apply_template_inheritance(template)

    def _apply_template_inheritance(self, template: TaskContextTemplate) -> None:
        """Apply inheritance from parent template"""
        if not template.inheritance:
            return

        parent_template = self._templates.get(template.inheritance)
        if not parent_template:
            logger.warning(f"Parent template not found: {template.inheritance}")
            return

        # Recursively apply parent's inheritance first
        if parent_template.inheritance:
            self._apply_template_inheritance(parent_template)

        # Merge properties from parent (child overrides parent)
        if not template.estimated_duration and parent_template.estimated_duration:
            template.estimated_duration = parent_template.estimated_duration

        # Merge tags
        parent_tags = set(parent_template.tags)
        child_tags = set(template.tags)
        template.tags = list(parent_tags.union(child_tags))

        # Merge default dependencies
        parent_deps = set(parent_template.default_dependencies)
        child_deps = set(template.default_dependencies)
        template.default_dependencies = list(parent_deps.union(child_deps))

        # Merge context data template
        merged_context_data = parent_template.context_data_template.copy()
        merged_context_data.update(template.context_data_template)
        template.context_data_template = merged_context_data

        # Merge metadata
        merged_metadata = parent_template.metadata.copy()
        merged_metadata.update(template.metadata)
        template.metadata = merged_metadata

    def get_template(self, template_id: str) -> Optional[TaskContextTemplate]:
        """
        Get a specific template by ID.

        Args:
            template_id: ID of the template

        Returns:
            TaskContextTemplate if found, None otherwise
        """
        if not self._loaded:
            self.load_templates()

        return self._templates.get(template_id)

    def create_template(self, template: TaskContextTemplate) -> str:
        """
        Create a new task context template.

        Args:
            template: TaskContextTemplate to create

        Returns:
            Template ID

        Raises:
            ValueError: If template ID already exists
        """
        if template.id in self._templates:
            raise ValueError(f"Template with ID {template.id} already exists")

        # Save to file
        self._save_template(template)

        # Add to loaded templates
        self._templates[template.id] = template

        logger.info(f"Created task context template {template.id}")
        return template.id

    def _save_template(self, template: TaskContextTemplate) -> None:
        """Save template to file"""
        template_file = self.templates_path / f"{template.id}.json"

        template_dict = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "priority": template.priority.value,
            "estimated_duration": template.estimated_duration,
            "tags": template.tags,
            "default_dependencies": template.default_dependencies,
            "context_data_template": template.context_data_template,
            "inheritance": template.inheritance,
            "metadata": template.metadata,
        }

        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=2)

    def get_templates_by_category(self, category: str) -> List[TaskContextTemplate]:
        """
        Get all templates for a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of templates in the category
        """
        if not self._loaded:
            self.load_templates()

        return [
            template
            for template in self._templates.values()
            if template.category == category
        ]

    def create_task_from_template(
        self,
        template_id: str,
        title: str,
        description: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None,
    ) -> TaskDefinition:
        """
        Create a TaskDefinition from a template.

        Args:
            template_id: ID of the template to use
            title: Title for the new task
            description: Optional description override
            customizations: Optional customizations to apply

        Returns:
            TaskDefinition ready for creating a TaskContext

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Use template description if none provided
        if description is None:
            description = template.description

        # Apply customizations
        priority = template.priority
        estimated_duration = template.estimated_duration
        tags = template.tags.copy()

        if customizations:
            if "priority" in customizations:
                priority = TaskPriority(customizations["priority"])
            if "estimated_duration" in customizations:
                estimated_duration = customizations["estimated_duration"]
            if "additional_tags" in customizations:
                tags.extend(customizations["additional_tags"])

        return TaskDefinition(
            title=title,
            description=description,
            category=template.category,
            priority=priority,
            estimated_duration=estimated_duration,
            tags=tags,
        )


# Add template support to TaskContextManager
# NOTE: These functions are disabled for MyPy compatibility
# def _add_template_support_to_manager() -> None:
#     """Add template support methods to TaskContextManager"""

#     def __init_with_templates__(
#         self: "TaskContextManager",
#         contexts_path: Optional[Path] = None,
#         schema_path: Optional[Path] = None,
#         templates_path: Optional[Path] = None,
#     ) -> None:
#         """Enhanced init with template support"""
#         # Call original init
#         self.__original_init__(contexts_path, schema_path)

#         # Add template manager
#         self.template_manager = TaskContextTemplateManager(templates_path)

#     def create_task_from_template(
#         self: "TaskContextManager",
#         template_id: str,
#         title: str,
#         description: Optional[str] = None,
#         customizations: Optional[Dict[str, Any]] = None,
#     ) -> TaskContext:
#         """
#         Create a task context from a template.

#         Args:
#             template_id: ID of the template to use
#             title: Title for the new task
#             description: Optional description override
#             customizations: Optional customizations to apply

#         Returns:
#             Created TaskContext
#         """
#         # Get task definition from template
#         task_def = self.template_manager.create_task_from_template(
#             template_id, title, description, customizations
#         )

#         # Create task context
#         context = self.create_task_context(task_def)

#         # Set template ID
#         context.template_id = template_id

#         # Apply template context data
#         template = self.template_manager.get_template(template_id)
#         if template and template.context_data_template:
#             context.context_data.update(template.context_data_template)

#         # Apply customizations to context data
#         if customizations and "context_data" in customizations:
#             context.context_data.update(customizations["context_data"])

#         # Update the context
#         self.update_task_context(context)

#         return context

#     def get_available_templates(self: "TaskContextManager") -> Dict[str, TaskContextTemplate]:
#         """Get all available task context templates"""
#         return self.template_manager.load_templates()

#     def get_templates_by_category(
#         self: "TaskContextManager", category: str
#     ) -> List[TaskContextTemplate]:
#         """Get templates by category"""
#         return self.template_manager.get_templates_by_category(category)

# Store original init and replace with enhanced version
# Note: Dynamic attribute assignment disabled for MyPy compatibility
# TaskContextManager.__original_init__ = TaskContextManager.__init__  # type: ignore
# TaskContextManager.__init__ = __init_with_templates__  # type: ignore
# TaskContextManager.create_task_from_template = create_task_from_template  # type: ignore
# TaskContextManager.get_available_templates = get_available_templates  # type: ignore
# TaskContextManager.get_templates_by_category = get_templates_by_category  # type: ignore


# Apply template support
# _add_template_support_to_manager()  # Disabled for MyPy compatibility

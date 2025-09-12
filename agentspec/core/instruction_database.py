"""
Instruction Database Management

This module provides the InstructionDatabase class for loading, validating,
and querying AgentSpec instructions from modular JSON files.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

try:
    import jsonschema
    from jsonschema import ValidationError as JsonSchemaValidationError

    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None  # type: ignore
    JsonSchemaValidationError = Exception  # type: ignore
    HAS_JSONSCHEMA = False

if TYPE_CHECKING:
    from .context_detector import ProjectContext

logger = logging.getLogger(__name__)


@dataclass
class Condition:
    """Represents a condition for instruction applicability"""

    type: str  # project_type, technology, file_exists, dependency_exists
    value: str
    operator: str  # equals, contains, matches, not_equals


@dataclass
class Parameter:
    """Represents a parameter for instruction customization"""

    name: str
    type: str  # string, number, boolean, array
    default: Any = None
    description: str = ""
    required: bool = False


@dataclass
class LanguageVariant:
    """Represents a language-specific variant of instruction content"""

    language: str  # ISO 639-1 language code (e.g., 'en', 'es', 'fr')
    content: str
    parameters: Optional[List[Parameter]] = None


@dataclass
class InstructionMetadata:
    """Metadata for an instruction"""

    category: str
    priority: int = 5
    author: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deprecated: bool = False
    replacement: Optional[str] = None
    default_language: str = "en"


@dataclass
class Instruction:
    """Represents a single AgentSpec instruction"""

    id: str
    version: str
    tags: List[str]
    content: str
    conditions: Optional[List[Condition]] = None
    parameters: Optional[List[Parameter]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[InstructionMetadata] = None
    language_variants: Optional[Dict[str, LanguageVariant]] = None


@dataclass
class ValidationResult:
    """Result of instruction validation"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class Conflict:
    """Represents a conflict between instructions"""

    instruction1_id: str
    instruction2_id: str
    conflict_type: str
    description: str
    severity: str = "medium"  # low, medium, high


@dataclass
class VersionInfo:
    """Represents semantic version information"""

    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version_str: str) -> "VersionInfo":
        """Parse version string into VersionInfo"""
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        try:
            return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
        except ValueError:
            raise ValueError(f"Invalid version format: {version_str}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) <= (
            other.major,
            other.minor,
            other.patch,
        )

    def __gt__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) > (
            other.major,
            other.minor,
            other.patch,
        )

    def __ge__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) >= (
            other.major,
            other.minor,
            other.patch,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (
            other.major,
            other.minor,
            other.patch,
        )

    def is_compatible(self, other: "VersionInfo") -> bool:
        """Check if versions are compatible (same major version)"""
        return self.major == other.major


class InstructionDatabase:
    """
    Manages instruction loading, validation, and querying from modular JSON files.

    This class provides functionality to:
    - Load instructions from category-based JSON files
    - Validate instruction format and content
    - Query instructions by tags
    - Detect conflicts between instructions
    - Evaluate conditional instructions based on project context
    """

    def __init__(
        self,
        instructions_path: Optional[Path] = None,
        schema_path: Optional[Path] = None,
    ):
        """
        Initialize the instruction database.

        Args:
            instructions_path: Path to the instructions directory
            schema_path: Path to the instruction schema file
        """
        self.instructions_path = (
            instructions_path or Path(__file__).parent.parent / "data" / "instructions"
        )
        self.schema_path = (
            schema_path
            or Path(__file__).parent.parent
            / "data"
            / "schemas"
            / "instruction_schema.json"
        )

        self._instructions: Dict[str, Instruction] = {}
        self._schema: Optional[Dict] = None
        self._loaded = False

        # Load schema
        self._load_schema()

    def _load_schema(self) -> None:
        """Load the JSON schema for instruction validation"""
        try:
            if self.schema_path.exists():
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    self._schema = json.load(f)
                logger.debug(f"Loaded instruction schema from {self.schema_path}")
            else:
                logger.warning(f"Schema file not found: {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            self._schema = None

    def load_instructions(self) -> Dict[str, Instruction]:
        """
        Load all instructions from JSON files in the instructions directory.

        Returns:
            Dictionary mapping instruction IDs to Instruction objects

        Raises:
            FileNotFoundError: If instructions directory doesn't exist
            ValueError: If instruction files contain invalid data
        """
        if self._loaded:
            return self._instructions

        if not self.instructions_path.exists():
            raise FileNotFoundError(
                f"Instructions directory not found: {self.instructions_path}"
            )

        self._instructions.clear()

        # Find all JSON files in the instructions directory
        json_files = list(self.instructions_path.glob("*.json"))

        if not json_files:
            logger.warning(f"No instruction files found in {self.instructions_path}")
            return self._instructions

        # Log the AI-enhanced instruction files being loaded
        ai_files = [f for f in json_files if "ai-" in f.name]
        if ai_files:
            logger.info(
                f"Loading {len(ai_files)} AI-enhanced instruction files: {[f.name for f in ai_files]}"
            )

        for json_file in json_files:
            try:
                self._load_instruction_file(json_file)
            except Exception as e:
                logger.error(f"Failed to load instruction file {json_file}: {e}")
                # Continue loading other files

        self._loaded = True
        logger.info(
            f"Loaded {len(self._instructions)} instructions from {len(json_files)} files"
        )

        return self._instructions

    def _load_instruction_file(self, file_path: Path) -> None:
        """Load instructions from a single JSON file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "instructions" not in data:
            raise ValueError(
                f"Invalid instruction file format: missing 'instructions' key in {file_path}"
            )

        for instruction_data in data["instructions"]:
            try:
                instruction = self._parse_instruction(instruction_data)

                # Validate instruction
                validation_result = self.validate_instruction(instruction)
                if not validation_result.is_valid:
                    logger.error(
                        f"Invalid instruction {instruction.id}: {validation_result.errors}"
                    )
                    continue

                # Check for duplicate IDs
                if instruction.id in self._instructions:
                    logger.warning(
                        f"Duplicate instruction ID: {instruction.id} (overwriting)"
                    )

                self._instructions[instruction.id] = instruction

            except Exception as e:
                logger.error(f"Failed to parse instruction in {file_path}: {e}")

    def _parse_instruction(self, data: Dict) -> Instruction:
        """Parse instruction data from JSON into Instruction object"""
        # Parse conditions
        conditions = None
        if "conditions" in data and data["conditions"]:
            conditions = [
                Condition(
                    type=cond["type"],
                    value=cond["value"],
                    operator=cond["operator"],
                )
                for cond in data["conditions"]
            ]

        # Parse parameters
        parameters = None
        if "parameters" in data and data["parameters"]:
            parameters = [
                Parameter(
                    name=param["name"],
                    type=param["type"],
                    default=param.get("default"),
                    description=param.get("description", ""),
                    required=param.get("required", False),
                )
                for param in data["parameters"]
            ]

        # Parse language variants
        language_variants = None
        if "language_variants" in data and data["language_variants"]:
            language_variants = {}
            for lang_code, variant_data in data["language_variants"].items():
                # Parse variant parameters if present
                variant_parameters = None
                if "parameters" in variant_data and variant_data["parameters"]:
                    variant_parameters = [
                        Parameter(
                            name=param["name"],
                            type=param["type"],
                            default=param.get("default"),
                            description=param.get("description", ""),
                            required=param.get("required", False),
                        )
                        for param in variant_data["parameters"]
                    ]

                language_variants[lang_code] = LanguageVariant(
                    language=lang_code,
                    content=variant_data["content"],
                    parameters=variant_parameters,
                )

        # Parse metadata
        metadata = None
        if "metadata" in data:
            meta_data = data["metadata"]
            created_at = None
            updated_at = None

            if "created_at" in meta_data:
                created_at = datetime.fromisoformat(
                    meta_data["created_at"].replace("Z", "+00:00")
                )
            if "updated_at" in meta_data:
                updated_at = datetime.fromisoformat(
                    meta_data["updated_at"].replace("Z", "+00:00")
                )

            metadata = InstructionMetadata(
                category=meta_data["category"],
                priority=meta_data.get("priority", 5),
                author=meta_data.get("author", ""),
                created_at=created_at,
                updated_at=updated_at,
                deprecated=meta_data.get("deprecated", False),
                replacement=meta_data.get("replacement"),
                default_language=meta_data.get("default_language", "en"),
            )

        return Instruction(
            id=data["id"],
            version=data["version"],
            tags=data["tags"],
            content=data["content"],
            conditions=conditions,
            parameters=parameters,
            dependencies=data.get("dependencies"),
            metadata=metadata,
            language_variants=language_variants,
        )

    def get_by_tags(self, tags: List[str]) -> List[Instruction]:
        """
        Get instructions that match any of the specified tags.

        Args:
            tags: List of tags to filter by

        Returns:
            List of matching instructions
        """
        if not self._loaded:
            self.load_instructions()

        if not tags:
            return list(self._instructions.values())

        matching_instructions = []
        tag_set = set(tag.lower() for tag in tags)

        for instruction in self._instructions.values():
            instruction_tags = set(tag.lower() for tag in instruction.tags)
            if tag_set.intersection(instruction_tags):
                matching_instructions.append(instruction)

        # Sort by priority (higher priority first)
        matching_instructions.sort(
            key=lambda inst: inst.metadata.priority if inst.metadata else 5,
            reverse=True,
        )

        return matching_instructions

    def validate_instruction(self, instruction: Instruction) -> ValidationResult:
        """
        Validate an instruction against the schema and business rules.

        Args:
            instruction: Instruction to validate

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        # Convert instruction to dict for schema validation
        instruction_dict: Dict[str, Any] = {
            "id": instruction.id,
            "version": instruction.version,
            "tags": instruction.tags,
            "content": instruction.content,
        }

        if instruction.conditions:
            instruction_dict["conditions"] = [
                {
                    "type": cond.type,
                    "value": cond.value,
                    "operator": cond.operator,
                }
                for cond in instruction.conditions
            ]

        if instruction.parameters:
            instruction_dict["parameters"] = [
                {
                    "name": param.name,
                    "type": param.type,
                    "default": param.default,
                    "description": param.description,
                    "required": param.required,
                }
                for param in instruction.parameters
            ]

        if instruction.dependencies:
            instruction_dict["dependencies"] = instruction.dependencies

        if instruction.metadata:
            metadata_dict: Dict[str, Any] = {
                "category": instruction.metadata.category,
                "priority": instruction.metadata.priority,
                "author": instruction.metadata.author,
                "deprecated": instruction.metadata.deprecated,
            }

            if instruction.metadata.created_at:
                metadata_dict["created_at"] = (
                    instruction.metadata.created_at.isoformat()
                )
            if instruction.metadata.updated_at:
                metadata_dict["updated_at"] = (
                    instruction.metadata.updated_at.isoformat()
                )
            if instruction.metadata.replacement:
                metadata_dict["replacement"] = instruction.metadata.replacement

            instruction_dict["metadata"] = metadata_dict

        # Schema validation
        if self._schema and HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instruction_dict, self._schema)
            except JsonSchemaValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")
        elif self._schema and not HAS_JSONSCHEMA:
            warnings.append("jsonschema not available, skipping schema validation")

        # Business rule validation
        if not instruction.id:
            errors.append("Instruction ID cannot be empty")

        if not instruction.content or len(instruction.content.strip()) < 10:
            errors.append("Instruction content must be at least 10 characters")

        if not instruction.tags:
            errors.append("Instruction must have at least one tag")

        # Version format validation
        try:
            version_parts = instruction.version.split(".")
            if len(version_parts) != 3 or not all(
                part.isdigit() for part in version_parts
            ):
                errors.append("Version must be in semantic versioning format (x.y.z)")
        except Exception:
            errors.append("Invalid version format")

        # Deprecation warnings
        if instruction.metadata and instruction.metadata.deprecated:
            warnings.append(f"Instruction {instruction.id} is deprecated")
            if not instruction.metadata.replacement:
                warnings.append(
                    f"Deprecated instruction {instruction.id} has no replacement specified"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_instruction_metadata(
        self, instruction_id: str
    ) -> Optional[InstructionMetadata]:
        """
        Get metadata for a specific instruction.

        Args:
            instruction_id: ID of the instruction

        Returns:
            InstructionMetadata if found, None otherwise
        """
        if not self._loaded:
            self.load_instructions()

        instruction = self._instructions.get(instruction_id)
        return instruction.metadata if instruction else None

    def get_instruction(self, instruction_id: str) -> Optional[Instruction]:
        """
        Get a specific instruction by ID.

        Args:
            instruction_id: ID of the instruction

        Returns:
            Instruction if found, None otherwise
        """
        if not self._loaded:
            self.load_instructions()

        return self._instructions.get(instruction_id)

    def get_all_tags(self) -> Set[str]:
        """
        Get all unique tags from all instructions.

        Returns:
            Set of all tags
        """
        if not self._loaded:
            self.load_instructions()

        tags = set()
        for instruction in self._instructions.values():
            tags.update(instruction.tags)

        return tags

    def get_instructions_by_category(self, category: str) -> List[Instruction]:
        """
        Get all instructions in a specific category.

        Args:
            category: Category name

        Returns:
            List of instructions in the category
        """
        if not self._loaded:
            self.load_instructions()

        return [
            instruction
            for instruction in self._instructions.values()
            if instruction.metadata and instruction.metadata.category == category
        ]

    def reload(self) -> None:
        """Reload all instructions from files"""
        self._loaded = False
        self._instructions.clear()
        self.load_instructions()

    def detect_conflicts(
        self, instructions: Optional[List[Instruction]] = None
    ) -> List[Conflict]:
        """
        Detect conflicts between instructions.

        Args:
            instructions: List of instructions to check for conflicts.
                         If None, checks all loaded instructions.

        Returns:
            List of detected conflicts
        """
        if instructions is None:
            if not self._loaded:
                self.load_instructions()
            instructions = list(self._instructions.values())

        conflicts = []

        # Check for various types of conflicts
        conflicts.extend(self._detect_tag_conflicts(instructions))
        conflicts.extend(self._detect_content_conflicts(instructions))
        conflicts.extend(self._detect_dependency_conflicts(instructions))
        conflicts.extend(self._detect_version_conflicts(instructions))

        return conflicts

    def _detect_tag_conflicts(self, instructions: List[Instruction]) -> List[Conflict]:
        """Detect instructions with conflicting tag combinations"""
        conflicts = []

        # Group instructions by similar tag sets
        tag_groups: Dict[Tuple[str, ...], List[Instruction]] = {}
        for instruction in instructions:
            tag_signature = tuple(sorted(instruction.tags))
            if tag_signature not in tag_groups:
                tag_groups[tag_signature] = []
            tag_groups[tag_signature].append(instruction)

        # Check for duplicate tag signatures
        for tag_signature, group_instructions in tag_groups.items():
            if len(group_instructions) > 1:
                for i in range(len(group_instructions)):
                    for j in range(i + 1, len(group_instructions)):
                        inst1, inst2 = (
                            group_instructions[i],
                            group_instructions[j],
                        )
                        conflicts.append(
                            Conflict(
                                instruction1_id=inst1.id,
                                instruction2_id=inst2.id,
                                conflict_type="duplicate_tags",
                                description=f"Instructions have identical tag sets: {', '.join(tag_signature)}",
                                severity="medium",
                            )
                        )

        return conflicts

    def _detect_content_conflicts(
        self, instructions: List[Instruction]
    ) -> List[Conflict]:
        """Detect instructions with conflicting content"""
        conflicts = []

        # Look for contradictory instructions
        contradictory_patterns = [
            (r"never\s+use", r"always\s+use", "contradictory_usage"),
            (r"avoid\s+", r"implement\s+", "contradictory_implementation"),
            (r"disable\s+", r"enable\s+", "contradictory_configuration"),
        ]

        for i, inst1 in enumerate(instructions):
            for j, inst2 in enumerate(instructions[i + 1 :], i + 1):
                # Skip if instructions don't share any tags
                if not set(inst1.tags).intersection(set(inst2.tags)):
                    continue

                content1_lower = inst1.content.lower()
                content2_lower = inst2.content.lower()

                for (
                    pattern1,
                    pattern2,
                    conflict_type,
                ) in contradictory_patterns:
                    if (
                        re.search(pattern1, content1_lower)
                        and re.search(pattern2, content2_lower)
                    ) or (
                        re.search(pattern2, content1_lower)
                        and re.search(pattern1, content2_lower)
                    ):
                        conflicts.append(
                            Conflict(
                                instruction1_id=inst1.id,
                                instruction2_id=inst2.id,
                                conflict_type=conflict_type,
                                description="Instructions contain contradictory guidance",
                                severity="high",
                            )
                        )

        return conflicts

    def _detect_dependency_conflicts(
        self, instructions: List[Instruction]
    ) -> List[Conflict]:
        """Detect circular dependencies and missing dependencies"""
        conflicts = []

        # Build dependency graph
        instruction_ids = {inst.id for inst in instructions}
        dependency_graph = {}

        for instruction in instructions:
            dependency_graph[instruction.id] = instruction.dependencies or []

        # Check for missing dependencies
        for instruction in instructions:
            if instruction.dependencies:
                for dep_id in instruction.dependencies:
                    if dep_id not in instruction_ids:
                        conflicts.append(
                            Conflict(
                                instruction1_id=instruction.id,
                                instruction2_id=dep_id,
                                conflict_type="missing_dependency",
                                description=f"Instruction {instruction.id} depends on missing instruction {dep_id}",
                                severity="high",
                            )
                        )

        # Check for circular dependencies
        def has_circular_dependency(
            start_id: str, current_id: str, visited: Set[str], path: List[str]
        ) -> bool:
            if current_id in visited:
                if current_id == start_id:
                    return True
                return False

            visited.add(current_id)
            path.append(current_id)

            for dep_id in dependency_graph.get(current_id, []):
                if dep_id in instruction_ids:
                    if has_circular_dependency(
                        start_id, dep_id, visited.copy(), path.copy()
                    ):
                        return True

            return False

        for instruction_id in instruction_ids:
            if has_circular_dependency(instruction_id, instruction_id, set(), []):
                # Find the actual cycle
                visited = set()
                path: List[str] = []

                def find_cycle(current_id: str) -> Optional[List[str]]:
                    if current_id in visited:
                        cycle_start = path.index(current_id)
                        return path[cycle_start:] + [current_id]

                    visited.add(current_id)
                    path.append(current_id)

                    for dep_id in dependency_graph.get(current_id, []):
                        if dep_id in instruction_ids:
                            cycle = find_cycle(dep_id)
                            if cycle:
                                return cycle

                    path.pop()
                    return None

                cycle = find_cycle(instruction_id)
                if cycle and len(cycle) > 1:
                    conflicts.append(
                        Conflict(
                            instruction1_id=cycle[0],
                            instruction2_id=cycle[1],
                            conflict_type="circular_dependency",
                            description=f"Circular dependency detected: {' -> '.join(cycle)}",
                            severity="high",
                        )
                    )

        return conflicts

    def _detect_version_conflicts(
        self, instructions: List[Instruction]
    ) -> List[Conflict]:
        """Detect version compatibility issues"""
        conflicts = []

        # Group instructions by ID (different versions of same instruction)
        version_groups: Dict[str, List[Instruction]] = {}
        for instruction in instructions:
            base_id = instruction.id
            if base_id not in version_groups:
                version_groups[base_id] = []
            version_groups[base_id].append(instruction)

        # Check for version conflicts within groups
        for base_id, group_instructions in version_groups.items():
            if len(group_instructions) > 1:
                # Sort by version
                try:
                    sorted_instructions = sorted(
                        group_instructions,
                        key=lambda inst: VersionInfo.from_string(inst.version),
                    )

                    # Check for major version incompatibilities
                    versions = [
                        VersionInfo.from_string(inst.version)
                        for inst in sorted_instructions
                    ]
                    for i in range(len(versions)):
                        for j in range(i + 1, len(versions)):
                            if not versions[i].is_compatible(versions[j]):
                                conflicts.append(
                                    Conflict(
                                        instruction1_id=sorted_instructions[i].id,
                                        instruction2_id=sorted_instructions[j].id,
                                        conflict_type="version_incompatibility",
                                        description=f"Major version incompatibility: {versions[i]} vs {versions[j]}",
                                        severity="medium",
                                    )
                                )

                except ValueError as e:
                    # Invalid version format
                    conflicts.append(
                        Conflict(
                            instruction1_id=group_instructions[0].id,
                            instruction2_id=(
                                group_instructions[1].id
                                if len(group_instructions) > 1
                                else ""
                            ),
                            conflict_type="invalid_version",
                            description=f"Invalid version format in instruction group {base_id}: {e}",
                            severity="medium",
                        )
                    )

        return conflicts

    def resolve_dependencies(self, instruction_ids: List[str]) -> List[str]:
        """
        Resolve instruction dependencies and return ordered list.

        Args:
            instruction_ids: List of instruction IDs to resolve

        Returns:
            Ordered list of instruction IDs with dependencies resolved

        Raises:
            ValueError: If circular dependencies are detected
        """
        if not self._loaded:
            self.load_instructions()

        # Build dependency graph for requested instructions
        dependency_graph: Dict[str, List[str]] = {}
        all_required_ids = set(instruction_ids)

        # Collect all dependencies recursively
        def collect_dependencies(inst_id: str) -> None:
            if inst_id in dependency_graph:
                return

            instruction = self._instructions.get(inst_id)
            if not instruction:
                dependency_graph[inst_id] = []
                return

            deps = instruction.dependencies or []
            dependency_graph[inst_id] = deps

            for dep_id in deps:
                all_required_ids.add(dep_id)
                collect_dependencies(dep_id)

        for inst_id in instruction_ids:
            collect_dependencies(inst_id)

        # Topological sort
        visited = set()
        temp_visited = set()
        result = []

        def visit(inst_id: str) -> None:
            if inst_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {inst_id}")

            if inst_id in visited:
                return

            temp_visited.add(inst_id)

            for dep_id in dependency_graph.get(inst_id, []):
                visit(dep_id)

            temp_visited.remove(inst_id)
            visited.add(inst_id)
            result.append(inst_id)

        for inst_id in all_required_ids:
            if inst_id not in visited:
                visit(inst_id)

        return result

    def is_backward_compatible(self, old_version: str, new_version: str) -> bool:
        """
        Check if new version is backward compatible with old version.

        Args:
            old_version: Old version string
            new_version: New version string

        Returns:
            True if backward compatible, False otherwise
        """
        try:
            old_ver = VersionInfo.from_string(old_version)
            new_ver = VersionInfo.from_string(new_version)

            # Backward compatible if:
            # 1. Same major version and new version >= old version
            # 2. Or new major version > old major version (with migration path)
            return (old_ver.major == new_ver.major and new_ver >= old_ver) or (
                new_ver.major > old_ver.major
            )

        except ValueError:
            return False

    def evaluate_conditions(
        self, instruction: Instruction, context: "ProjectContext"
    ) -> bool:
        """
        Evaluate instruction conditions against project context.

        Args:
            instruction: Instruction with conditions to evaluate
            context: Project context to evaluate against

        Returns:
            True if all conditions are met, False otherwise
        """
        if not instruction.conditions:
            return True  # No conditions means always applicable

        for condition in instruction.conditions:
            if not self._evaluate_single_condition(condition, context):
                return False

        return True

    def _evaluate_single_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """
        Evaluate a single condition against project context.

        Args:
            condition: Condition to evaluate
            context: Project context

        Returns:
            True if condition is met, False otherwise
        """
        try:
            if condition.type == "project_type":
                return self._evaluate_project_type_condition(condition, context)
            elif condition.type == "technology":
                return self._evaluate_technology_condition(condition, context)
            elif condition.type == "file_exists":
                return self._evaluate_file_exists_condition(condition, context)
            elif condition.type == "dependency_exists":
                return self._evaluate_dependency_condition(condition, context)
            elif condition.type == "language":
                return self._evaluate_language_condition(condition, context)
            elif condition.type == "framework":
                return self._evaluate_framework_condition(condition, context)
            else:
                logger.warning(f"Unknown condition type: {condition.type}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.type}: {e}")
            return False

    def _evaluate_project_type_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate project type condition"""
        project_type_value = (
            context.project_type.value
            if hasattr(context.project_type, "value")
            else str(context.project_type)
        )

        if condition.operator == "equals":
            return project_type_value == condition.value
        elif condition.operator == "not_equals":
            return project_type_value != condition.value
        elif condition.operator == "contains":
            return condition.value in project_type_value
        else:
            return False

    def _evaluate_technology_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate technology stack condition"""
        tech_stack = context.technology_stack

        # Check in various technology categories
        all_technologies = []

        # Add languages
        if hasattr(tech_stack, "languages"):
            all_technologies.extend(
                [
                    lang.value if hasattr(lang, "value") else str(lang)
                    for lang in tech_stack.languages
                ]
            )

        # Add frameworks
        if hasattr(tech_stack, "frameworks"):
            all_technologies.extend([fw.name for fw in tech_stack.frameworks])

        # Add databases
        if hasattr(tech_stack, "databases"):
            all_technologies.extend(tech_stack.databases)

        # Add tools
        if hasattr(tech_stack, "tools"):
            all_technologies.extend(tech_stack.tools)

        # Add platforms
        if hasattr(tech_stack, "platforms"):
            all_technologies.extend(tech_stack.platforms)

        if condition.operator == "equals":
            return condition.value in all_technologies
        elif condition.operator == "not_equals":
            return condition.value not in all_technologies
        elif condition.operator == "contains":
            return any(condition.value in tech for tech in all_technologies)
        elif condition.operator == "matches":
            pattern = re.compile(condition.value, re.IGNORECASE)
            return any(pattern.search(tech) for tech in all_technologies)
        else:
            return False

    def _evaluate_file_exists_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate file existence condition"""
        project_path = Path(context.project_path)

        if condition.operator == "equals":
            # Check exact file path
            return (project_path / condition.value).exists()
        elif condition.operator == "contains":
            # Check if any file contains the pattern in its path
            pattern = condition.value
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.relpath(os.path.join(root, file), project_path)
                    if pattern in file_path:
                        return True
            return False
        elif condition.operator == "matches":
            # Check if any file matches the regex pattern
            regex_pattern = re.compile(condition.value)
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = os.path.relpath(os.path.join(root, file), project_path)
                    if regex_pattern.search(file_path):
                        return True
            return False
        else:
            return False

    def _evaluate_dependency_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate dependency condition"""
        dependencies = context.dependencies if hasattr(context, "dependencies") else []
        dependency_names = [dep.name for dep in dependencies]

        if condition.operator == "equals":
            return condition.value in dependency_names
        elif condition.operator == "not_equals":
            return condition.value not in dependency_names
        elif condition.operator == "contains":
            return any(condition.value in dep_name for dep_name in dependency_names)
        elif condition.operator == "matches":
            pattern = re.compile(condition.value, re.IGNORECASE)
            return any(pattern.search(dep_name) for dep_name in dependency_names)
        else:
            return False

    def _evaluate_language_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate programming language condition"""
        languages = (
            context.technology_stack.languages
            if hasattr(context.technology_stack, "languages")
            else []
        )
        language_names = [
            lang.value if hasattr(lang, "value") else str(lang) for lang in languages
        ]

        if condition.operator == "equals":
            return condition.value in language_names
        elif condition.operator == "not_equals":
            return condition.value not in language_names
        elif condition.operator == "contains":
            return any(condition.value in lang for lang in language_names)
        else:
            return False

    def _evaluate_framework_condition(
        self, condition: Condition, context: "ProjectContext"
    ) -> bool:
        """Evaluate framework condition"""
        frameworks = (
            context.technology_stack.frameworks
            if hasattr(context.technology_stack, "frameworks")
            else []
        )
        framework_names = [fw.name for fw in frameworks]

        if condition.operator == "equals":
            return condition.value in framework_names
        elif condition.operator == "not_equals":
            return condition.value not in framework_names
        elif condition.operator == "contains":
            return any(condition.value in fw_name for fw_name in framework_names)
        elif condition.operator == "matches":
            pattern = re.compile(condition.value, re.IGNORECASE)
            return any(pattern.search(fw_name) for fw_name in framework_names)
        else:
            return False

    def filter_instructions_by_conditions(
        self, instructions: List[Instruction], context: "ProjectContext"
    ) -> List[Instruction]:
        """
        Filter instructions based on their conditions and project context.

        Args:
            instructions: List of instructions to filter
            context: Project context to evaluate conditions against

        Returns:
            List of instructions that meet their conditions
        """
        filtered_instructions = []

        for instruction in instructions:
            if self.evaluate_conditions(instruction, context):
                filtered_instructions.append(instruction)
            else:
                logger.debug(
                    f"Instruction {instruction.id} filtered out due to unmet conditions"
                )

        return filtered_instructions

    def get_by_tags_with_conditions(
        self, tags: List[str], context: "ProjectContext"
    ) -> List[Instruction]:
        """
        Get instructions that match tags and satisfy their conditions.

        Args:
            tags: List of tags to filter by
            context: Project context for condition evaluation

        Returns:
            List of matching instructions that satisfy their conditions
        """
        # First get instructions by tags
        tag_matched_instructions = self.get_by_tags(tags)

        # Then filter by conditions
        return self.filter_instructions_by_conditions(tag_matched_instructions, context)

    def validate_condition(self, condition: Condition) -> ValidationResult:
        """
        Validate a condition for correctness.

        Args:
            condition: Condition to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []

        # Validate condition type
        valid_types = [
            "project_type",
            "technology",
            "file_exists",
            "dependency_exists",
            "language",
            "framework",
        ]
        if condition.type not in valid_types:
            errors.append(
                f"Invalid condition type: {condition.type}. Must be one of: {', '.join(valid_types)}"
            )

        # Validate operator
        valid_operators = ["equals", "not_equals", "contains", "matches"]
        if condition.operator not in valid_operators:
            errors.append(
                f"Invalid operator: {condition.operator}. Must be one of: {', '.join(valid_operators)}"
            )

        # Validate value
        if not condition.value or not isinstance(condition.value, str):
            errors.append("Condition value must be a non-empty string")

        # Validate regex patterns for 'matches' operator
        if condition.operator == "matches":
            try:
                re.compile(condition.value)
            except re.error as e:
                errors.append(f"Invalid regex pattern in condition value: {e}")

        # Type-specific validations
        if condition.type == "project_type":
            # Could validate against known project types
            pass
        elif condition.type == "file_exists":
            # Validate file path format
            if ".." in condition.value or condition.value.startswith("/"):
                warnings.append("File path should be relative to project root")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def test_condition_evaluation(
        self, condition: Condition, test_contexts: List["ProjectContext"]
    ) -> Dict[str, bool]:
        """
        Test condition evaluation against multiple project contexts.

        Args:
            condition: Condition to test
            test_contexts: List of project contexts to test against

        Returns:
            Dictionary mapping context descriptions to evaluation results
        """
        results = {}

        for i, context in enumerate(test_contexts):
            context_desc = (
                f"Context {i+1}: {getattr(context, 'project_type', 'unknown')}"
            )
            try:
                result = self._evaluate_single_condition(condition, context)
                results[context_desc] = result
            except Exception as e:
                logger.error(f"Error testing condition against {context_desc}: {e}")
                results[context_desc] = False

        return results

    def substitute_parameters(
        self, instruction: Instruction, parameter_values: Dict[str, Any]
    ) -> str:
        """
        Substitute parameters in instruction content with provided values.

        Args:
            instruction: Instruction with parameters to substitute
            parameter_values: Dictionary of parameter names to values

        Returns:
            Instruction content with parameters substituted
        """
        content = instruction.content

        if not instruction.parameters:
            return content

        # Create a mapping of parameter names to their processed values
        substitution_map = {}

        for parameter in instruction.parameters:
            param_name = parameter.name

            # Get value from provided values or use default
            if param_name in parameter_values:
                value = parameter_values[param_name]
            elif parameter.default is not None:
                value = parameter.default
            elif parameter.required:
                raise ValueError(f"Required parameter '{param_name}' not provided")
            else:
                continue  # Skip optional parameters without values

            # Validate and convert value based on parameter type
            processed_value = self._process_parameter_value(parameter, value)
            substitution_map[param_name] = processed_value

        # Perform substitution using various patterns
        substituted_content = self._perform_parameter_substitution(
            content, substitution_map
        )

        return substituted_content

    def _process_parameter_value(self, parameter: Parameter, value: Any) -> str:
        """
        Process and validate parameter value based on its type.

        Args:
            parameter: Parameter definition
            value: Raw parameter value

        Returns:
            Processed value as string
        """
        if parameter.type == "string":
            return str(value)
        elif parameter.type == "number":
            try:
                # Try to preserve integer vs float distinction
                if isinstance(value, (int, float)):
                    return str(value)
                else:
                    # Try to parse as number
                    if "." in str(value):
                        return str(float(value))
                    else:
                        return str(int(value))
            except (ValueError, TypeError):
                raise ValueError(
                    f"Parameter '{parameter.name}' must be a number, got: {value}"
                )
        elif parameter.type == "boolean":
            if isinstance(value, bool):
                return str(value).lower()
            elif isinstance(value, str):
                if value.lower() in ["true", "1", "yes", "on"]:
                    return "true"
                elif value.lower() in ["false", "0", "no", "of"]:
                    return "false"
                else:
                    raise ValueError(
                        f"Parameter '{parameter.name}' must be a boolean, got: {value}"
                    )
            else:
                return str(bool(value)).lower()
        elif parameter.type == "array":
            if isinstance(value, list):
                return ", ".join(str(item) for item in value)
            elif isinstance(value, str):
                # Assume comma-separated values
                return value
            else:
                raise ValueError(
                    f"Parameter '{parameter.name}' must be an array, got: {value}"
                )
        else:
            # Unknown type, treat as string
            return str(value)

    def _perform_parameter_substitution(
        self, content: str, substitution_map: Dict[str, str]
    ) -> str:
        """
        Perform parameter substitution in content using various patterns.

        Args:
            content: Original content
            substitution_map: Map of parameter names to values

        Returns:
            Content with parameters substituted
        """
        result = content

        for param_name, param_value in substitution_map.items():
            # Support multiple substitution patterns:
            # {{param_name}} - double braces
            # ${param_name} - shell-style
            # {param_name} - single braces
            patterns = [
                (f"{{{{{param_name}}}}}", param_value),  # {{param_name}}
                (f"${{{param_name}}}", param_value),  # ${param_name}
                (f"{{{param_name}}}", param_value),  # {param_name}
            ]

            for pattern, replacement in patterns:
                result = result.replace(pattern, replacement)

        return result

    def validate_parameter_values(
        self, instruction: Instruction, parameter_values: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate parameter values against instruction parameter definitions.

        Args:
            instruction: Instruction with parameter definitions
            parameter_values: Dictionary of parameter values to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not instruction.parameters:
            if parameter_values:
                warnings.append(
                    "Parameter values provided but instruction has no parameters"
                )
            return ValidationResult(is_valid=True, errors=errors, warnings=warnings)

        # Check required parameters
        required_params = {p.name for p in instruction.parameters if p.required}
        provided_params = set(parameter_values.keys())

        missing_required = required_params - provided_params
        if missing_required:
            errors.extend(
                [
                    f"Required parameter '{param}' not provided"
                    for param in missing_required
                ]
            )

        # Check for unknown parameters
        valid_params = {p.name for p in instruction.parameters}
        unknown_params = provided_params - valid_params
        if unknown_params:
            warnings.extend(
                [f"Unknown parameter '{param}' provided" for param in unknown_params]
            )

        # Validate parameter types and values
        param_map = {p.name: p for p in instruction.parameters}

        for param_name, param_value in parameter_values.items():
            if param_name in param_map:
                param_def = param_map[param_name]
                try:
                    self._process_parameter_value(param_def, param_value)
                except ValueError as e:
                    errors.append(str(e))

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_parameter_defaults(self, instruction: Instruction) -> Dict[str, Any]:
        """
        Get default parameter values for an instruction.

        Args:
            instruction: Instruction to get defaults for

        Returns:
            Dictionary of parameter names to default values
        """
        defaults = {}

        if instruction.parameters:
            for parameter in instruction.parameters:
                if parameter.default is not None:
                    defaults[parameter.name] = parameter.default

        return defaults

    def get_required_parameters(self, instruction: Instruction) -> List[Parameter]:
        """
        Get list of required parameters for an instruction.

        Args:
            instruction: Instruction to check

        Returns:
            List of required parameters
        """
        if not instruction.parameters:
            return []

        return [p for p in instruction.parameters if p.required]

    def validate_parameter_definition(self, parameter: Parameter) -> ValidationResult:
        """
        Validate a parameter definition for correctness.

        Args:
            parameter: Parameter to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []

        # Validate parameter name
        if not parameter.name or not isinstance(parameter.name, str):
            errors.append("Parameter name must be a non-empty string")
        elif not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", parameter.name):
            errors.append(
                f"Parameter name '{parameter.name}' must be a valid identifier"
            )

        # Validate parameter type
        valid_types = ["string", "number", "boolean", "array"]
        if parameter.type not in valid_types:
            errors.append(f"Parameter type must be one of: {', '.join(valid_types)}")

        # Validate default value against type
        if parameter.default is not None:
            try:
                self._process_parameter_value(parameter, parameter.default)
            except ValueError as e:
                errors.append(f"Default value validation failed: {e}")

        # Check for required parameters with defaults
        if parameter.required and parameter.default is not None:
            warnings.append(
                f"Required parameter '{parameter.name}' has a default value"
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def create_parameterized_instruction(
        self, base_instruction: Instruction, parameter_values: Dict[str, Any]
    ) -> Instruction:
        """
        Create a new instruction with parameters substituted.

        Args:
            base_instruction: Original instruction with parameters
            parameter_values: Values to substitute

        Returns:
            New instruction with substituted content
        """
        # Validate parameter values first
        validation = self.validate_parameter_values(base_instruction, parameter_values)
        if not validation.is_valid:
            raise ValueError(
                f"Parameter validation failed: {', '.join(validation.errors)}"
            )

        # Substitute parameters in content
        substituted_content = self.substitute_parameters(
            base_instruction, parameter_values
        )

        # Create new instruction with substituted content
        new_instruction = Instruction(
            id=f"{base_instruction.id}_parameterized",
            version=base_instruction.version,
            tags=base_instruction.tags.copy(),
            content=substituted_content,
            conditions=base_instruction.conditions,
            parameters=None,  # Remove parameters from instantiated instruction
            dependencies=base_instruction.dependencies,
            metadata=base_instruction.metadata,
        )

        return new_instruction

    def visualize_dependency_graph(
        self, instruction_ids: List[str], output_format: str = "text"
    ) -> str:
        """
        Create a visualization of instruction dependencies.

        Args:
            instruction_ids: List of instruction IDs to include in visualization
            output_format: Format for output ("text", "dot", "mermaid")

        Returns:
            String representation of the dependency graph
        """
        if not self._loaded:
            self.load_instructions()

        # Build dependency graph for requested instructions
        dependency_graph: Dict[str, List[str]] = {}
        all_instructions = set(instruction_ids)

        # Collect all dependencies recursively
        def collect_dependencies(inst_id: str) -> None:
            if inst_id in dependency_graph:
                return

            instruction = self._instructions.get(inst_id)
            if not instruction:
                dependency_graph[inst_id] = []
                return

            deps = instruction.dependencies or []
            dependency_graph[inst_id] = deps

            for dep_id in deps:
                all_instructions.add(dep_id)
                collect_dependencies(dep_id)

        for inst_id in instruction_ids:
            collect_dependencies(inst_id)

        if output_format == "dot":
            return self._generate_dot_graph(dependency_graph, all_instructions)
        elif output_format == "mermaid":
            return self._generate_mermaid_graph(dependency_graph, all_instructions)
        else:
            return self._generate_text_graph(dependency_graph, all_instructions)

    def _generate_text_graph(
        self,
        dependency_graph: Dict[str, List[str]],
        all_instructions: Set[str],
    ) -> str:
        """Generate text representation of dependency graph"""
        lines = ["Instruction Dependency Graph:", "=" * 30]

        for inst_id in sorted(all_instructions):
            deps = dependency_graph.get(inst_id, [])
            if deps:
                lines.append(f"{inst_id} depends on:")
                for dep in deps:
                    lines.append(f"  └─ {dep}")
            else:
                lines.append(f"{inst_id} (no dependencies)")
            lines.append("")

        return "\n".join(lines)

    def _generate_dot_graph(
        self,
        dependency_graph: Dict[str, List[str]],
        all_instructions: Set[str],
    ) -> str:
        """Generate DOT format graph for Graphviz"""
        lines = ["digraph InstructionDependencies {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box, style=rounded];")
        lines.append("")

        # Add nodes
        for inst_id in sorted(all_instructions):
            safe_id = inst_id.replace("-", "_").replace(".", "_")
            lines.append(f'  {safe_id} [label="{inst_id}"];')

        lines.append("")

        # Add edges
        for inst_id, deps in dependency_graph.items():
            safe_inst_id = inst_id.replace("-", "_").replace(".", "_")
            for dep_id in deps:
                safe_dep_id = dep_id.replace("-", "_").replace(".", "_")
                lines.append(f"  {safe_dep_id} -> {safe_inst_id};")

        lines.append("}")
        return "\n".join(lines)

    def _generate_mermaid_graph(
        self,
        dependency_graph: Dict[str, List[str]],
        all_instructions: Set[str],
    ) -> str:
        """Generate Mermaid format graph"""
        lines = ["graph TD"]

        # Add nodes and edges
        for inst_id, deps in dependency_graph.items():
            safe_inst_id = inst_id.replace("-", "_").replace(".", "_")
            for dep_id in deps:
                safe_dep_id = dep_id.replace("-", "_").replace(".", "_")
                lines.append(f"  {safe_dep_id} --> {safe_inst_id}")

        # Add standalone nodes (no dependencies)
        for inst_id in all_instructions:
            if not dependency_graph.get(inst_id):
                safe_inst_id = inst_id.replace("-", "_").replace(".", "_")
                lines.append(f"  {safe_inst_id}")

        return "\n".join(lines)

    def get_dependency_chain(self, instruction_id: str) -> List[str]:
        """
        Get the complete dependency chain for an instruction.

        Args:
            instruction_id: ID of the instruction

        Returns:
            Ordered list of instruction IDs in dependency order
        """
        try:
            return self.resolve_dependencies([instruction_id])
        except ValueError as e:
            logger.error(
                f"Failed to resolve dependency chain for {instruction_id}: {e}"
            )
            return []

    def get_dependents(self, instruction_id: str) -> List[str]:
        """
        Get instructions that depend on the given instruction.

        Args:
            instruction_id: ID of the instruction

        Returns:
            List of instruction IDs that depend on the given instruction
        """
        if not self._loaded:
            self.load_instructions()

        dependents = []

        for inst_id, instruction in self._instructions.items():
            if instruction.dependencies and instruction_id in instruction.dependencies:
                dependents.append(inst_id)

        return dependents

    def validate_dependency_graph(self, instruction_ids: List[str]) -> ValidationResult:
        """
        Validate the dependency graph for a set of instructions.

        Args:
            instruction_ids: List of instruction IDs to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []

        if not self._loaded:
            self.load_instructions()

        # Check for missing instructions
        missing_instructions = []
        for inst_id in instruction_ids:
            if inst_id not in self._instructions:
                missing_instructions.append(inst_id)

        if missing_instructions:
            errors.extend(
                [f"Missing instruction: {inst_id}" for inst_id in missing_instructions]
            )

        # Check for circular dependencies
        try:
            self.resolve_dependencies(instruction_ids)
        except ValueError as e:
            if "circular dependency" in str(e).lower():
                errors.append(str(e))

        # Check for missing dependencies
        all_required_deps = set()
        for inst_id in instruction_ids:
            instruction = self._instructions.get(inst_id)
            if instruction and instruction.dependencies:
                all_required_deps.update(instruction.dependencies)

        missing_deps = (
            all_required_deps - set(instruction_ids) - set(self._instructions.keys())
        )
        if missing_deps:
            errors.extend([f"Missing dependency: {dep_id}" for dep_id in missing_deps])

        # Check for orphaned dependencies (dependencies not in the instruction set)
        orphaned_deps = all_required_deps - set(instruction_ids)
        if orphaned_deps:
            warnings.extend(
                [
                    f"Orphaned dependency (not in instruction set): {dep_id}"
                    for dep_id in orphaned_deps
                ]
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def optimize_dependency_order(self, instruction_ids: List[str]) -> List[str]:
        """
        Optimize the order of instructions based on dependencies and priorities.

        Args:
            instruction_ids: List of instruction IDs to order

        Returns:
            Optimally ordered list of instruction IDs
        """
        # First resolve dependencies to get basic ordering
        try:
            dependency_ordered = self.resolve_dependencies(instruction_ids)
        except ValueError:
            # If there are circular dependencies, fall back to original order
            dependency_ordered = instruction_ids

        # Group by priority levels
        priority_groups: Dict[int, List[str]] = {}
        for inst_id in dependency_ordered:
            instruction = self._instructions.get(inst_id)
            priority = (
                instruction.metadata.priority
                if instruction and instruction.metadata
                else 5
            )

            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(inst_id)

        # Rebuild order respecting both dependencies and priorities
        optimized_order = []
        for priority in sorted(
            priority_groups.keys(), reverse=True
        ):  # Higher priority first
            optimized_order.extend(priority_groups[priority])

        return optimized_order

    def get_dependency_statistics(
        self, instruction_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about instruction dependencies.

        Args:
            instruction_ids: Optional list to limit analysis to specific instructions

        Returns:
            Dictionary with dependency statistics
        """
        if not self._loaded:
            self.load_instructions()

        instructions_to_analyze = instruction_ids or list(self._instructions.keys())

        stats: Dict[str, Any] = {
            "total_instructions": len(instructions_to_analyze),
            "instructions_with_dependencies": 0,
            "total_dependencies": 0,
            "max_dependency_depth": 0,
            "circular_dependencies": 0,
            "orphaned_dependencies": 0,
            "dependency_distribution": {},
        }

        dependency_counts = {}

        for inst_id in instructions_to_analyze:
            instruction = self._instructions.get(inst_id)
            if instruction and instruction.dependencies:
                stats["instructions_with_dependencies"] += 1
                dep_count = len(instruction.dependencies)
                stats["total_dependencies"] += dep_count

                # Track dependency count distribution
                if dep_count not in dependency_counts:
                    dependency_counts[dep_count] = 0
                dependency_counts[dep_count] += 1

                # Calculate dependency depth
                try:
                    chain = self.get_dependency_chain(inst_id)
                    depth = (
                        len(chain) - 1
                    )  # Subtract 1 because chain includes the instruction itself
                    stats["max_dependency_depth"] = max(
                        stats["max_dependency_depth"], depth
                    )
                except Exception:
                    pass  # nosec B110 # Intentionally ignore calculation errors

        stats["dependency_distribution"] = dependency_counts

        # Check for circular dependencies
        conflicts = self.detect_conflicts()
        stats["circular_dependencies"] = len(
            [c for c in conflicts if c.conflict_type == "circular_dependency"]
        )

        return stats

    def get_instruction_in_language(
        self,
        instruction_id: str,
        language: str,
        fallback_to_default: bool = True,
    ) -> Optional[Instruction]:
        """
        Get instruction in a specific language.

        Args:
            instruction_id: ID of the instruction
            language: ISO 639-1 language code
            fallback_to_default: Whether to fallback to default language if variant not found

        Returns:
            Instruction with content in requested language, or None if not found
        """
        if not self._loaded:
            self.load_instructions()

        instruction = self._instructions.get(instruction_id)
        if not instruction:
            return None

        # If no language variants, return original instruction
        if not instruction.language_variants:
            default_lang = (
                instruction.metadata.default_language if instruction.metadata else "en"
            )
            if language == default_lang or fallback_to_default:
                return instruction
            else:
                return None

        # Check if requested language variant exists
        if language in instruction.language_variants:
            variant = instruction.language_variants[language]

            # Create new instruction with variant content
            localized_instruction = Instruction(
                id=instruction.id,
                version=instruction.version,
                tags=instruction.tags,
                content=variant.content,
                conditions=instruction.conditions,
                parameters=variant.parameters or instruction.parameters,
                dependencies=instruction.dependencies,
                metadata=instruction.metadata,
                language_variants=instruction.language_variants,
            )

            return localized_instruction

        # Fallback to default language if requested
        if fallback_to_default:
            default_lang = (
                instruction.metadata.default_language if instruction.metadata else "en"
            )
            if (
                default_lang != language
                and default_lang in instruction.language_variants
            ):
                return self.get_instruction_in_language(
                    instruction_id, default_lang, False
                )
            else:
                return instruction  # Return original if no default variant

        return None

    def get_available_languages(self, instruction_id: Optional[str] = None) -> Set[str]:
        """
        Get available languages for instructions.

        Args:
            instruction_id: Optional specific instruction ID, or None for all instructions

        Returns:
            Set of available language codes
        """
        if not self._loaded:
            self.load_instructions()

        languages = set()

        instructions_to_check = (
            [self._instructions[instruction_id]]
            if instruction_id and instruction_id in self._instructions
            else self._instructions.values()
        )

        for instruction in instructions_to_check:
            # Add default language
            default_lang = (
                instruction.metadata.default_language if instruction.metadata else "en"
            )
            languages.add(default_lang)

            # Add variant languages
            if instruction.language_variants:
                languages.update(instruction.language_variants.keys())

        return languages

    def detect_user_language(self, context: Optional["ProjectContext"] = None) -> str:
        """
        Detect user's preferred language from various sources.

        Args:
            context: Optional project context for language hints

        Returns:
            Detected language code (defaults to 'en')
        """
        # Try to detect from environment variables
        import locale
        import os

        # Check environment variables
        for env_var in ["LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES"]:
            lang_env = os.environ.get(env_var)
            if lang_env:
                # Extract language code (e.g., 'en_US.UTF-8' -> 'en')
                lang_code = lang_env.split("_")[0].split(".")[0].lower()
                if len(lang_code) == 2:
                    return lang_code

        # Try system locale
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if len(lang_code) == 2:
                    return lang_code
        except Exception:
            pass  # nosec B110 # Intentionally ignore locale detection errors

        # Check project context for language hints
        if context and hasattr(context, "technology_stack"):
            # Some basic heuristics based on technology stack
            tech_stack = context.technology_stack
            if hasattr(tech_stack, "languages"):
                for lang in tech_stack.languages:
                    lang_name = lang.value if hasattr(lang, "value") else str(lang)
                    # This is a very basic mapping - could be expanded
                    if "java" in lang_name.lower():
                        return "en"  # Java is predominantly English

        # Default to English
        return "en"

    def get_instructions_by_language(
        self, language: str, tags: Optional[List[str]] = None
    ) -> List[Instruction]:
        """
        Get all instructions available in a specific language.

        Args:
            language: Language code to filter by
            tags: Optional tags to further filter instructions

        Returns:
            List of instructions available in the specified language
        """
        if not self._loaded:
            self.load_instructions()

        available_instructions = []

        for instruction in self._instructions.values():
            # Check if instruction is available in the requested language
            localized_instruction = self.get_instruction_in_language(
                instruction.id, language, fallback_to_default=False
            )
            if localized_instruction:
                # Apply tag filtering if specified
                if tags:
                    instruction_tags = set(
                        tag.lower() for tag in localized_instruction.tags
                    )
                    filter_tags = set(tag.lower() for tag in tags)
                    if filter_tags.intersection(instruction_tags):
                        available_instructions.append(localized_instruction)
                else:
                    available_instructions.append(localized_instruction)

        return available_instructions

    def add_language_variant(
        self,
        instruction_id: str,
        language: str,
        content: str,
        parameters: Optional[List[Parameter]] = None,
    ) -> bool:
        """
        Add a language variant to an existing instruction.

        Args:
            instruction_id: ID of the instruction
            language: Language code for the variant
            content: Localized content
            parameters: Optional localized parameters

        Returns:
            True if variant was added successfully, False otherwise
        """
        if not self._loaded:
            self.load_instructions()

        instruction = self._instructions.get(instruction_id)
        if not instruction:
            logger.error(f"Instruction {instruction_id} not found")
            return False

        # Initialize language_variants if not present
        if instruction.language_variants is None:
            instruction.language_variants = {}

        # Create language variant
        variant = LanguageVariant(
            language=language, content=content, parameters=parameters
        )

        # Add variant
        instruction.language_variants[language] = variant

        logger.info(f"Added {language} variant to instruction {instruction_id}")
        return True

    def validate_language_variant(self, variant: LanguageVariant) -> ValidationResult:
        """
        Validate a language variant for correctness.

        Args:
            variant: Language variant to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        warnings = []

        # Validate language code
        if not variant.language or len(variant.language) != 2:
            errors.append("Language code must be a 2-character ISO 639-1 code")
        elif not variant.language.islower():
            warnings.append("Language code should be lowercase")

        # Validate content
        if not variant.content or len(variant.content.strip()) < 10:
            errors.append("Variant content must be at least 10 characters")

        # Validate parameters if present
        if variant.parameters:
            for parameter in variant.parameters:
                param_validation = self.validate_parameter_definition(parameter)
                if not param_validation.is_valid:
                    errors.extend(
                        [
                            f"Parameter validation failed: {error}"
                            for error in param_validation.errors
                        ]
                    )
                warnings.extend(param_validation.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def translate_instruction_content(
        self, content: str, source_language: str, target_language: str
    ) -> str:
        """
        Placeholder for instruction content translation.

        This method provides a framework for translation functionality.
        In a real implementation, this would integrate with translation services.

        Args:
            content: Content to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            Translated content (currently returns original content with a note)
        """
        # This is a placeholder implementation
        # In a real system, you would integrate with translation services like:
        # - Google Translate API
        # - Microsoft Translator
        # - AWS Translate
        # - DeepL API

        logger.warning(
            f"Translation from {source_language} to {target_language} not implemented"
        )
        return f"[TRANSLATION NEEDED: {source_language} -> {target_language}] {content}"

    def get_language_coverage_report(self) -> Dict[str, Any]:
        """
        Generate a report on language coverage across all instructions.

        Returns:
            Dictionary with language coverage statistics
        """
        if not self._loaded:
            self.load_instructions()

        total_instructions = len(self._instructions)
        language_stats = {}

        # Count instructions available in each language
        all_languages = self.get_available_languages()

        for language in all_languages:
            available_count = 0
            for instruction in self._instructions.values():
                if self.get_instruction_in_language(
                    instruction.id, language, fallback_to_default=False
                ):
                    available_count += 1

            coverage_percentage = (
                (available_count / total_instructions * 100)
                if total_instructions > 0
                else 0
            )
            language_stats[language] = {
                "available_instructions": available_count,
                "total_instructions": total_instructions,
                "coverage_percentage": round(coverage_percentage, 2),
            }

        # Find instructions missing translations
        missing_translations = {}
        for language in all_languages:
            missing_for_lang = []
            for inst_id, instruction in self._instructions.items():
                if not self.get_instruction_in_language(
                    inst_id, language, fallback_to_default=False
                ):
                    missing_for_lang.append(inst_id)

            if missing_for_lang:
                missing_translations[language] = missing_for_lang

        return {
            "total_instructions": total_instructions,
            "available_languages": sorted(all_languages),
            "language_statistics": language_stats,
            "missing_translations": missing_translations,
        }

    def get_latest_version(self, instruction_id: str) -> Optional[Instruction]:
        """
        Get the latest version of an instruction.

        Args:
            instruction_id: Base instruction ID

        Returns:
            Latest version of the instruction, or None if not found
        """
        if not self._loaded:
            self.load_instructions()

        # Find all versions of this instruction
        versions = []
        for inst_id, instruction in self._instructions.items():
            if inst_id.startswith(instruction_id):
                try:
                    version_info = VersionInfo.from_string(instruction.version)
                    versions.append((version_info, instruction))
                except ValueError:
                    continue

        if not versions:
            return None

        # Return the highest version
        versions.sort(key=lambda x: x[0], reverse=True)
        return versions[0][1]

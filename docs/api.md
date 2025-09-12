# AgentSpec API Documentation

This document provides comprehensive API documentation for AgentSpec's Python modules and classes.

## Table of Contents

- [Core Modules](#core-modules)
  - [InstructionDatabase](#instructiondatabase)
  - [TemplateManager](#templatemanager)
  - [ContextDetector](#contextdetector)
  - [SpecGenerator](#specgenerator)
  - [TaskContextManager](#taskcontextmanager)
- [CLI Modules](#cli-modules)
- [Utility Modules](#utility-modules)
- [Data Models](#data-models)
- [Examples](#examples)

## Core Modules

### InstructionDatabase

The `InstructionDatabase` class manages loading, validation, and querying of AgentSpec instructions.

#### Class Definition

```python
from agentspec.core.instruction_database import InstructionDatabase

class InstructionDatabase:
    def __init__(self, instructions_path: Optional[Path] = None, 
                 schema_path: Optional[Path] = None)
```

#### Methods

##### `load_instructions() -> Dict[str, Instruction]`

Loads all instructions from JSON files in the instructions directory.

**Returns:**
- `Dict[str, Instruction]`: Dictionary mapping instruction IDs to Instruction objects

**Raises:**
- `FileNotFoundError`: If instructions directory doesn't exist
- `ValueError`: If instruction files contain invalid data

**Example:**
```python
db = InstructionDatabase()
instructions = db.load_instructions()
print(f"Loaded {len(instructions)} instructions")
```

##### `get_by_tags(tags: List[str]) -> List[Instruction]`

Retrieves instructions that match any of the specified tags.

**Parameters:**
- `tags`: List of tags to filter by

**Returns:**
- `List[Instruction]`: List of matching instructions, sorted by priority

**Example:**
```python
testing_instructions = db.get_by_tags(["testing", "quality"])
for instruction in testing_instructions:
    print(f"{instruction.id}: {instruction.tags}")
```

##### `validate_instruction(instruction: Instruction) -> ValidationResult`

Validates an instruction against schema and business rules.

**Parameters:**
- `instruction`: Instruction object to validate

**Returns:**
- `ValidationResult`: Validation status with errors and warnings

**Example:**
```python
result = db.validate_instruction(instruction)
if not result.is_valid:
    print(f"Validation errors: {result.errors}")
```

##### `detect_conflicts(instructions: Optional[List[Instruction]] = None) -> List[Conflict]`

Detects conflicts between instructions.

**Parameters:**
- `instructions`: Optional list of instructions to check (defaults to all loaded)

**Returns:**
- `List[Conflict]`: List of detected conflicts

**Example:**
```python
conflicts = db.detect_conflicts()
for conflict in conflicts:
    print(f"Conflict: {conflict.description}")
```

##### `resolve_dependencies(instruction_ids: List[str]) -> List[str]`

Resolves instruction dependencies and returns ordered list.

**Parameters:**
- `instruction_ids`: List of instruction IDs to resolve

**Returns:**
- `List[str]`: Ordered list with dependencies resolved

**Raises:**
- `ValueError`: If circular dependencies are detected

**Example:**
```python
ordered_ids = db.resolve_dependencies(["inst1", "inst2", "inst3"])
print(f"Execution order: {ordered_ids}")
```

### TemplateManager

The `TemplateManager` class handles loading, validation, and recommendation of project templates.

#### Class Definition

```python
from agentspec.core.template_manager import TemplateManager

class TemplateManager:
    def __init__(self, templates_path: Optional[Path] = None,
                 schema_path: Optional[Path] = None)
```

#### Methods

##### `load_templates() -> Dict[str, Template]`

Loads all templates from JSON files and resolves inheritance.

**Returns:**
- `Dict[str, Template]`: Dictionary mapping template IDs to Template objects

**Example:**
```python
manager = TemplateManager()
templates = manager.load_templates()
print(f"Available templates: {list(templates.keys())}")
```

##### `get_template(template_id: str) -> Optional[Template]`

Retrieves a specific template by ID.

**Parameters:**
- `template_id`: ID of the template to retrieve

**Returns:**
- `Optional[Template]`: Template object if found, None otherwise

**Example:**
```python
react_template = manager.get_template("react_app")
if react_template:
    print(f"Template: {react_template.name}")
```

##### `get_recommended_templates(project_context: Dict[str, Any]) -> List[TemplateRecommendation]`

Gets template recommendations based on project context.

**Parameters:**
- `project_context`: Dictionary containing project information

**Returns:**
- `List[TemplateRecommendation]`: Sorted list of recommendations

**Example:**
```python
context = {
    "project_type": "web_frontend",
    "technology_stack": ["react", "typescript"],
    "files": ["package.json", "tsconfig.json"]
}
recommendations = manager.get_recommended_templates(context)
for rec in recommendations:
    print(f"{rec.template.name}: {rec.confidence_score:.2f}")
```

##### `create_template(template: Template) -> str`

Creates a new template and saves it to file.

**Parameters:**
- `template`: Template object to create

**Returns:**
- `str`: Template ID

**Raises:**
- `ValueError`: If template is invalid or ID already exists

**Example:**
```python
new_template = Template(
    id="custom_template",
    name="Custom Template",
    description="My custom template",
    version="1.0.0",
    project_type="web_frontend",
    technology_stack=["custom"],
    default_tags=["custom"]
)
template_id = manager.create_template(new_template)
```

### ContextDetector

The `ContextDetector` class analyzes projects to detect technology stacks and suggest relevant instructions.

#### Class Definition

```python
from agentspec.core.context_detector import ContextDetector

class ContextDetector:
    def __init__(self)
```

#### Methods

##### `analyze_project(project_path: str) -> ProjectContext`

Performs comprehensive project analysis.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:**
- `ProjectContext`: Complete project analysis results

**Raises:**
- `ValueError`: If project path is invalid

**Example:**
```python
detector = ContextDetector()
context = detector.analyze_project("./my-project")
print(f"Project type: {context.project_type.value}")
print(f"Confidence: {context.confidence_score:.2f}")
```

##### `detect_technology_stack(project_path: str) -> TechnologyStack`

Detects technology stack from project files.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:**
- `TechnologyStack`: Detected technologies

**Example:**
```python
stack = detector.detect_technology_stack("./my-project")
print(f"Languages: {[lang.value for lang in stack.languages]}")
print(f"Frameworks: {[fw.name for fw in stack.frameworks]}")
```

##### `suggest_instructions(context: ProjectContext) -> List[InstructionSuggestion]`

Suggests relevant instructions based on project context.

**Parameters:**
- `context`: Project context information

**Returns:**
- `List[InstructionSuggestion]`: Sorted list of suggestions

**Example:**
```python
suggestions = detector.suggest_instructions(context)
for suggestion in suggestions[:5]:  # Top 5
    print(f"{suggestion.instruction_id}: {suggestion.confidence:.2f}")
```

### SpecGenerator

The `SpecGenerator` class generates specifications from instructions and templates.

#### Class Definition

```python
from agentspec.core.spec_generator import SpecGenerator, SpecConfig

class SpecGenerator:
    def __init__(self, instruction_db: Optional[InstructionDatabase] = None,
                 template_manager: Optional[TemplateManager] = None,
                 context_detector: Optional[ContextDetector] = None)
```

#### Methods

##### `generate_spec(config: SpecConfig) -> GeneratedSpec`

Generates a specification based on configuration.

**Parameters:**
- `config`: SpecConfig with generation parameters

**Returns:**
- `GeneratedSpec`: Generated specification with metadata

**Raises:**
- `ValueError`: If configuration is invalid

**Example:**
```python
generator = SpecGenerator()
config = SpecConfig(
    selected_tags=["frontend", "testing"],
    output_format="markdown"
)
spec = generator.generate_spec(config)
print(spec.content)
```

##### `apply_template(template: Template, context: Optional[ProjectContext] = None) -> SpecConfig`

Applies a template to create specification configuration.

**Parameters:**
- `template`: Template to apply
- `context`: Optional project context for customization

**Returns:**
- `SpecConfig`: Configuration based on template

**Example:**
```python
template = template_manager.get_template("react_app")
config = generator.apply_template(template, project_context)
spec = generator.generate_spec(config)
```

##### `validate_spec(spec: GeneratedSpec) -> ValidationResult`

Validates a generated specification.

**Parameters:**
- `spec`: Generated specification to validate

**Returns:**
- `ValidationResult`: Validation status and messages

**Example:**
```python
result = generator.validate_spec(spec)
if not result.is_valid:
    print(f"Validation errors: {result.errors}")
if result.warnings:
    print(f"Warnings: {result.warnings}")
```

##### `export_spec(spec: GeneratedSpec, output_path: Optional[str] = None) -> str`

Exports specification to file or returns as string.

**Parameters:**
- `spec`: Generated specification to export
- `output_path`: Optional file path to save

**Returns:**
- `str`: Specification content

**Example:**
```python
# Export to file
generator.export_spec(spec, "project_spec.md")

# Get as string
content = generator.export_spec(spec)
```

### TaskContextManager

The `TaskContextManager` class manages enhanced task contexts with metadata and dependencies.

#### Class Definition

```python
from agentspec.core.task_context import TaskContextManager, TaskDefinition

class TaskContextManager:
    def __init__(self, contexts_path: Optional[Path] = None,
                 schema_path: Optional[Path] = None)
```

#### Methods

##### `create_task_context(task: TaskDefinition) -> TaskContext`

Creates a new task context from definition.

**Parameters:**
- `task`: TaskDefinition with basic task information

**Returns:**
- `TaskContext`: Created task context

**Raises:**
- `ValueError`: If task definition is invalid

**Example:**
```python
from agentspec.core.task_context import TaskDefinition, TaskPriority

manager = TaskContextManager()
task_def = TaskDefinition(
    title="Implement Authentication",
    description="Add user login and registration",
    category="feature",
    priority=TaskPriority.HIGH
)
context = manager.create_task_context(task_def)
```

##### `load_task_context(task_id: str) -> Optional[TaskContext]`

Loads a task context by ID.

**Parameters:**
- `task_id`: ID of the task context to load

**Returns:**
- `Optional[TaskContext]`: Task context if found

**Example:**
```python
context = manager.load_task_context("task_123")
if context:
    print(f"Task: {context.title}")
```

##### `add_task_dependency(task_id: str, dependency: TaskDependency) -> None`

Adds a dependency to a task.

**Parameters:**
- `task_id`: ID of the task to add dependency to
- `dependency`: TaskDependency to add

**Raises:**
- `ValueError`: If task not found or dependency creates cycle

**Example:**
```python
from agentspec.core.task_context import TaskDependency

dependency = TaskDependency(
    task_id="prerequisite_task",
    dependency_type="blocks",
    description="Must complete setup first"
)
manager.add_task_dependency("main_task", dependency)
```

##### `visualize_task_graph(task_ids: List[str]) -> TaskGraph`

Creates visualization of task dependencies.

**Parameters:**
- `task_ids`: List of task IDs to include

**Returns:**
- `TaskGraph`: Graph with nodes, edges, and cycle information

**Example:**
```python
graph = manager.visualize_task_graph(["task1", "task2", "task3"])
print(f"Tasks: {len(graph.nodes)}")
print(f"Dependencies: {len(graph.edges)}")
if graph.cycles:
    print(f"Cycles detected: {graph.cycles}")
```

## CLI Modules

### Main CLI

The main CLI entry point provides command-line interface functionality.

```python
from agentspec.cli.main import AgentSpecCLI

cli = AgentSpecCLI()
exit_code = cli.run(['generate', '--tags', 'frontend,testing'])
```

### Command Handlers

Individual command handlers for specific CLI operations.

```python
from agentspec.cli.commands import (
    list_tags_command,
    generate_spec_command,
    analyze_project_command
)

# Use command handlers directly
result = list_tags_command(instruction_db, verbose=True)
```

## Utility Modules

### Configuration Management

```python
from agentspec.utils.config import ConfigManager

manager = ConfigManager()
config = manager.load_config()
value = manager.get_config_value("agentspec.paths.instructions")
```

### Logging Setup

```python
from agentspec.utils.logging import setup_logging

setup_logging(
    log_level="DEBUG",
    log_file="agentspec.log",
    structured=True
)
```

### Feature Flags

```python
from agentspec.utils.feature_flags import is_feature_enabled

if is_feature_enabled("advanced_analysis"):
    # Use advanced features
    pass
```

## Data Models

### Core Data Classes

#### Instruction

```python
@dataclass
class Instruction:
    id: str
    version: str
    tags: List[str]
    content: str
    conditions: Optional[List[Condition]] = None
    parameters: Optional[List[Parameter]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[InstructionMetadata] = None
    language_variants: Optional[Dict[str, LanguageVariant]] = None
```

#### Template

```python
@dataclass
class Template:
    id: str
    name: str
    description: str
    version: str
    project_type: str
    technology_stack: List[str]
    default_tags: List[str]
    required_instructions: List[str] = field(default_factory=list)
    optional_instructions: List[str] = field(default_factory=list)
    excluded_instructions: List[str] = field(default_factory=list)
    parameters: Dict[str, TemplateParameter] = field(default_factory=dict)
    inheritance: Optional[TemplateInheritance] = None
    conditions: List[TemplateCondition] = field(default_factory=list)
    metadata: Optional[TemplateMetadata] = None
```

#### ProjectContext

```python
@dataclass
class ProjectContext:
    project_path: str
    project_type: ProjectType
    technology_stack: TechnologyStack
    dependencies: List[Dependency] = field(default_factory=list)
    file_structure: FileStructure = field(default_factory=FileStructure)
    git_info: Optional[GitInfo] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### TaskContext

```python
@dataclass
class TaskContext:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: TaskMetadata = field(default_factory=lambda: TaskMetadata(category="general"))
    dependencies: List[TaskDependency] = field(default_factory=list)
    sub_tasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None
    template_id: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
```

## Examples

### Complete Workflow Example

```python
from agentspec.core import (
    InstructionDatabase, TemplateManager, 
    ContextDetector, SpecGenerator, SpecConfig
)

# Initialize components
instruction_db = InstructionDatabase()
template_manager = TemplateManager()
context_detector = ContextDetector()
spec_generator = SpecGenerator(
    instruction_db=instruction_db,
    template_manager=template_manager,
    context_detector=context_detector
)

# Analyze project
project_context = context_detector.analyze_project("./my-project")
print(f"Detected: {project_context.project_type.value}")

# Get template recommendations
recommendations = template_manager.get_recommended_templates({
    "project_type": project_context.project_type.value,
    "technology_stack": [fw.name for fw in project_context.technology_stack.frameworks]
})

# Use best template
if recommendations:
    template = recommendations[0].template
    config = spec_generator.apply_template(template, project_context)
else:
    # Manual configuration
    config = SpecConfig(
        selected_tags=["frontend", "testing", "security"],
        project_context=project_context
    )

# Generate specification
spec = spec_generator.generate_spec(config)

# Validate and export
validation = spec_generator.validate_spec(spec)
if validation.is_valid:
    spec_generator.export_spec(spec, "project_spec.md")
    print("Specification generated successfully!")
else:
    print(f"Validation errors: {validation.errors}")
```

### Custom Instruction Creation

```python
from agentspec.core.instruction_database import (
    Instruction, InstructionMetadata, Condition, Parameter
)

# Create custom instruction
custom_instruction = Instruction(
    id="custom_react_testing",
    version="1.0.0",
    tags=["react", "testing", "custom"],
    content="Implement comprehensive React testing with {test_framework}.",
    conditions=[
        Condition(
            type="technology",
            value="react",
            operator="equals"
        )
    ],
    parameters=[
        Parameter(
            name="test_framework",
            type="string",
            default="jest",
            description="Testing framework to use"
        )
    ],
    metadata=InstructionMetadata(
        category="testing",
        priority=8,
        author="custom_author"
    )
)

# Validate instruction
db = InstructionDatabase()
result = db.validate_instruction(custom_instruction)
if result.is_valid:
    print("Custom instruction is valid!")
```

### Task Management Example

```python
from agentspec.core.task_context import (
    TaskContextManager, TaskDefinition, TaskPriority,
    TaskDependency, TaskStatus
)

# Initialize task manager
manager = TaskContextManager()

# Create tasks
setup_task = manager.create_task_context(TaskDefinition(
    title="Project Setup",
    description="Initialize project structure",
    category="setup",
    priority=TaskPriority.HIGH
))

dev_task = manager.create_task_context(TaskDefinition(
    title="Feature Development", 
    description="Implement main features",
    category="development",
    priority=TaskPriority.MEDIUM
))

# Add dependency
dependency = TaskDependency(
    task_id=setup_task.id,
    dependency_type="blocks",
    description="Setup must complete first"
)
manager.add_task_dependency(dev_task.id, dependency)

# Get execution order
ordered_tasks = manager.get_task_order([setup_task.id, dev_task.id])
print(f"Execution order: {ordered_tasks}")

# Update task status
dev_task.status = TaskStatus.IN_PROGRESS
manager.update_task_context(dev_task)
```

## Error Handling

All AgentSpec APIs use consistent error handling patterns:

```python
from agentspec.core.instruction_database import InstructionDatabase
from agentspec.core.exceptions import AgentSpecError, ValidationError

try:
    db = InstructionDatabase()
    instructions = db.load_instructions()
except FileNotFoundError as e:
    print(f"Instructions directory not found: {e}")
except ValidationError as e:
    print(f"Validation failed: {e}")
except AgentSpecError as e:
    print(f"AgentSpec error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Large Datasets

For large instruction databases or project analysis:

```python
# Use lazy loading
db = InstructionDatabase()
# Instructions loaded on first access
instructions = db.load_instructions()

# Cache results for repeated queries
cached_instructions = db.get_by_tags(["frontend"])
```

### Memory Management

```python
# Clear caches when needed
db.reload()  # Reloads from files
template_manager.reload()  # Reloads templates
```

### Concurrent Usage

AgentSpec components are thread-safe for read operations:

```python
import threading

def analyze_project(path):
    detector = ContextDetector()
    return detector.analyze_project(path)

# Safe to run concurrently
threads = [
    threading.Thread(target=analyze_project, args=(path,))
    for path in project_paths
]
```

This API documentation provides comprehensive coverage of AgentSpec's Python interface. For more examples and advanced usage patterns, see the [examples directory](../examples/) in the repository.
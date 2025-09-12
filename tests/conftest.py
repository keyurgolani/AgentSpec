"""
Pytest configuration and shared fixtures for AgentSpec tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from agentspec.core.context_detector import (
    ContextDetector,
    FileStructure,
    Framework,
    Language,
    ProjectContext,
    ProjectType,
    TechnologyStack,
)
from agentspec.core.instruction_database import (
    Condition,
    Instruction,
    InstructionDatabase,
    InstructionMetadata,
    LanguageVariant,
    Parameter,
)
from agentspec.core.spec_generator import SpecConfig, SpecGenerator
from agentspec.core.task_context import (
    TaskContext,
    TaskContextManager,
    TaskDefinition,
    TaskMetadata,
    TaskPriority,
    TaskStatus,
)
from agentspec.core.template_manager import (
    Template,
    TemplateCondition,
    TemplateManager,
    TemplateMetadata,
    TemplateParameter,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_instruction():
    """Create a sample instruction for testing."""
    metadata = InstructionMetadata(category="testing", priority=5, author="test_author")

    return Instruction(
        id="test_instruction",
        version="1.0.0",
        tags=["testing", "quality"],
        content="This is a test instruction for unit testing.",
        metadata=metadata,
    )


@pytest.fixture
def sample_instruction_with_conditions():
    """Create a sample instruction with conditions for testing."""
    conditions = [
        Condition(type="project_type", value="web_frontend", operator="equals")
    ]

    parameters = [
        Parameter(
            name="test_param",
            type="string",
            default="default_value",
            description="Test parameter",
        )
    ]

    metadata = InstructionMetadata(category="frontend", priority=7)

    return Instruction(
        id="conditional_instruction",
        version="2.0.0",
        tags=["frontend", "react"],
        content="Frontend-specific instruction with {test_param}.",
        conditions=conditions,
        parameters=parameters,
        metadata=metadata,
    )


@pytest.fixture
def sample_template():
    """Create a sample template for testing."""
    parameters = {
        "project_name": TemplateParameter(
            name="project_name",
            type="string",
            default="my-project",
            description="Name of the project",
        )
    }

    conditions = [
        TemplateCondition(
            type="file_exists", value="package.json", operator="exists", weight=0.8
        )
    ]

    metadata = TemplateMetadata(
        category="web", complexity="intermediate", tags=["react", "frontend"]
    )

    return Template(
        id="react_app",
        name="React Application",
        description="Template for React applications",
        version="1.0.0",
        project_type="web_frontend",
        technology_stack=["react", "javascript"],
        default_tags=["frontend", "react", "testing"],
        required_instructions=["test_instruction"],
        optional_instructions=["conditional_instruction"],
        parameters=parameters,
        conditions=conditions,
        metadata=metadata,
    )


@pytest.fixture
def sample_project_context():
    """Create a sample project context for testing."""
    tech_stack = TechnologyStack(
        languages=[Language.JAVASCRIPT, Language.TYPESCRIPT],
        frameworks=[Framework(name="react", version="18.0.0", confidence=0.9)],
        databases=["postgresql"],
        tools=["webpack", "jest"],
        platforms=["web"],
    )

    file_structure = FileStructure(
        total_files=50,
        directories=["src", "public", "tests"],
        file_types={".js": 20, ".ts": 15, ".json": 5},
        config_files=["package.json", "tsconfig.json"],
        source_files=["src/App.js", "src/index.js"],
        test_files=["tests/App.test.js"],
    )

    return ProjectContext(
        project_path="/test/project",
        project_type=ProjectType.WEB_FRONTEND,
        technology_stack=tech_stack,
        file_structure=file_structure,
        confidence_score=0.85,
    )


@pytest.fixture
def sample_task_context():
    """Create a sample task context for testing."""
    metadata = TaskMetadata(
        category="development",
        priority=TaskPriority.HIGH,
        estimated_duration=120,
        tags=["frontend", "testing"],
    )

    return TaskContext(
        id="test_task_123",
        title="Implement user authentication",
        description="Add login and registration functionality",
        status=TaskStatus.PENDING,
        metadata=metadata,
    )


@pytest.fixture
def mock_instruction_files(temp_dir):
    """Create mock instruction files for testing."""
    instructions_dir = temp_dir / "instructions"
    instructions_dir.mkdir()

    # Create sample instruction files
    general_instructions = {
        "instructions": [
            {
                "id": "general_quality",
                "version": "1.0.0",
                "tags": ["general", "quality"],
                "content": "Maintain high code quality standards.",
                "metadata": {"category": "general", "priority": 5},
            }
        ]
    }

    testing_instructions = {
        "instructions": [
            {
                "id": "unit_testing",
                "version": "1.0.0",
                "tags": ["testing", "unit"],
                "content": "Write comprehensive unit tests.",
                "metadata": {"category": "testing", "priority": 8},
            }
        ]
    }

    with open(instructions_dir / "general.json", "w") as f:
        json.dump(general_instructions, f)

    with open(instructions_dir / "testing.json", "w") as f:
        json.dump(testing_instructions, f)

    return instructions_dir


@pytest.fixture
def mock_template_files(temp_dir):
    """Create mock template files for testing."""
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir()

    # Create sample template file
    react_template = {
        "id": "react_app",
        "name": "React Application",
        "description": "Template for React applications",
        "version": "1.0.0",
        "project_type": "web_frontend",
        "technology_stack": ["react", "javascript"],
        "default_tags": ["frontend", "react", "testing"],
        "required_instructions": ["unit_testing"],
        "optional_instructions": ["general_quality"],
        "parameters": {
            "project_name": {
                "type": "string",
                "default": "my-react-app",
                "description": "Name of the React project",
            }
        },
        "metadata": {"category": "web", "complexity": "intermediate"},
    }

    with open(templates_dir / "react-app.json", "w") as f:
        json.dump(react_template, f)

    return templates_dir


@pytest.fixture
def mock_project_structure(temp_dir):
    """Create a mock project structure for testing."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()

    # Create package.json
    package_json = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"},
        "devDependencies": {"jest": "^28.0.0", "@testing-library/react": "^13.0.0"},
    }

    with open(project_dir / "package.json", "w") as f:
        json.dump(package_json, f)

    # Create source files
    src_dir = project_dir / "src"
    src_dir.mkdir()

    with open(src_dir / "App.js", "w") as f:
        f.write(
            """
import React from 'react';

function App() {
  return <div>Hello World</div>;
}

export default App;
        """
        )

    with open(src_dir / "index.js", "w") as f:
        f.write(
            """
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(<App />, document.getElementById('root'));
        """
        )

    # Create test files
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()

    with open(tests_dir / "App.test.js", "w") as f:
        f.write(
            """
import { render } from '@testing-library/react';
import App from '../src/App';

test('renders hello world', () => {
  render(<App />);
});
        """
        )

    return project_dir


@pytest.fixture
def instruction_database(mock_instruction_files):
    """Create an InstructionDatabase instance with mock data."""
    return InstructionDatabase(instructions_path=mock_instruction_files)


@pytest.fixture
def template_manager(mock_template_files):
    """Create a TemplateManager instance with mock data."""
    return TemplateManager(templates_path=mock_template_files)


@pytest.fixture
def context_detector():
    """Create a ContextDetector instance."""
    return ContextDetector()


@pytest.fixture
def spec_generator(instruction_database, template_manager, context_detector):
    """Create a SpecGenerator instance with dependencies."""
    return SpecGenerator(
        instruction_db=instruction_database,
        template_manager=template_manager,
        context_detector=context_detector,
    )


@pytest.fixture
def task_context_manager(temp_dir):
    """Create a TaskContextManager instance with temporary directory."""
    return TaskContextManager(contexts_path=temp_dir / "task_contexts")


# Mock external dependencies
@pytest.fixture
def mock_git_repo():
    """Mock git repository information."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\n"
        yield mock_run


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.is_dir"
    ) as mock_is_dir, patch("os.walk") as mock_walk:

        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_walk.return_value = [
            ("/test", ["src"], ["package.json"]),
            ("/test/src", [], ["App.js", "index.js"]),
        ]

        yield {"exists": mock_exists, "is_dir": mock_is_dir, "walk": mock_walk}


# Utility functions for tests
def create_test_instruction(
    instruction_id: str = "test_inst", tags: list = None, content: str = "Test content"
) -> Instruction:
    """Helper function to create test instructions."""
    if tags is None:
        tags = ["test"]

    return Instruction(
        id=instruction_id,
        version="1.0.0",
        tags=tags,
        content=content,
        metadata=InstructionMetadata(category="test"),
    )


def create_test_template(
    template_id: str = "test_template", project_type: str = "web_frontend"
) -> Template:
    """Helper function to create test templates."""
    return Template(
        id=template_id,
        name="Test Template",
        description="A test template",
        version="1.0.0",
        project_type=project_type,
        technology_stack=["test"],
        default_tags=["test"],
        metadata=TemplateMetadata(category="test"),
    )


def assert_validation_result(
    result,
    should_be_valid: bool = True,
    expected_errors: int = 0,
    expected_warnings: int = 0,
):
    """Helper function to assert validation results."""
    assert result.is_valid == should_be_valid
    assert len(result.errors) == expected_errors
    assert len(result.warnings) == expected_warnings

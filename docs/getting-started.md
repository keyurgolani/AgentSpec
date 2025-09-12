# Getting Started with AgentSpec

Welcome to AgentSpec! This guide will help you get up and running with specification-driven development for AI agents.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Basic Concepts](#basic-concepts)
4. [Your First Specification](#your-first-specification)
5. [Project Analysis](#project-analysis)
6. [Using Templates](#using-templates)
7. [Customization](#customization)
8. [Best Practices](#best-practices)
9. [Next Steps](#next-steps)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Install AgentSpec

#### Option 1: Install from PyPI (Recommended)

```bash
pip install agentspec
```

#### Option 2: Install from Source

```bash
git clone https://github.com/agentspec/agentspec.git
cd agentspec
pip install -e .
```

#### Option 3: Development Installation

```bash
git clone https://github.com/agentspec/agentspec.git
cd agentspec
pip install -e .[dev]
```

### Verify Installation

```bash
agentspec --version
```

You should see output like:
```
AgentSpec 2.0.0
Specification-Driven Development for AI Agents
```

## Quick Start

### 1. Interactive Mode (Recommended for Beginners)

The easiest way to get started is with the interactive wizard:

```bash
agentspec interactive
```

This will guide you through:
- Project type detection
- Template selection
- Instruction customization
- Specification generation

### 2. Generate Your First Spec

For a quick start, generate a specification with common tags:

```bash
agentspec generate --tags general,testing,quality --output my_first_spec.md
```

### 3. Analyze an Existing Project

If you have an existing project, let AgentSpec analyze it:

```bash
cd /path/to/your/project
agentspec analyze . --output analysis.json
```

## Basic Concepts

### Specifications

A **specification** is a comprehensive document that guides AI agents through development tasks. It includes:

- **Guidelines**: Best practices for your technology stack
- **Quality Gates**: Validation criteria that must be met
- **Implementation Framework**: Step-by-step process for development
- **Validation Commands**: Scripts to verify compliance

### Instructions

**Instructions** are modular guidelines that cover specific aspects of development:

- **General**: Core development practices
- **Testing**: Testing strategies and frameworks
- **Security**: Security best practices
- **Frontend**: UI/UX development guidelines
- **Backend**: Server-side development practices

### Templates

**Templates** are pre-configured sets of instructions for specific project types and industries:

**Web Applications:**
- **React App**: Modern React applications with TypeScript
- **Vue App**: Vue.js applications with modern tooling
- **Enterprise Web App**: Large-scale enterprise applications
- **Base Web App**: Generic web application foundation

**Backend Services:**
- **Python API**: FastAPI/Django REST APIs
- **Node.js API**: Express.js REST APIs
- **Microservice**: Distributed microservice architectures

**Specialized Platforms:**
- **SaaS Platform**: Multi-tenant SaaS applications
- **E-commerce Platform**: Online retail and marketplace platforms
- **Fintech App**: Financial technology applications
- **Healthcare Platform**: HIPAA-compliant healthcare applications
- **Data Science Platform**: ML and analytics platforms

**Mobile & Cross-Platform:**
- **Mobile App**: React Native/Flutter applications

**AI & Security:**
- **AI-Enhanced Development**: AI-assisted development workflows
- **Secure Enterprise App**: High-security enterprise applications

### Tags

**Tags** categorize instructions by topic, technology, or domain:

- `general`, `quality`, `standards`
- `testing`, `tdd`, `validation`
- `frontend`, `react`, `vue`, `angular`
- `backend`, `api`, `database`
- `security`, `performance`, `accessibility`

## Your First Specification

Let's create a specification for a React application step by step.

### Step 1: Create Project Directory

```bash
mkdir my-react-app
cd my-react-app
```

### Step 2: Generate Specification

```bash
agentspec generate \
  --tags frontend,react,testing,typescript \
  --output react_spec.md \
  --format markdown
```

### Step 3: Review the Generated Specification

Open `react_spec.md` to see your specification:

```markdown
# AgentSpec - Project Specification

Generated: 2023-12-01 10:00:00
Selected tags: frontend, react, testing, typescript
Total instructions: 12

## FRONTEND GUIDELINES

### 1. React Component Architecture
**Tags**: react, components, architecture
**Priority**: 9

Implement a modular component architecture using React functional components...

### 2. TypeScript Integration
**Tags**: typescript, type-safety, frontend
**Priority**: 8

Configure and use TypeScript throughout the React application...

## IMPLEMENTATION FRAMEWORK

### Pre-Task Checklist
- [ ] Load existing task context from `task_contexts/<task_name>.md`
- [ ] Analyze codebase thoroughly
- [ ] Define clear exit criteria

### During Implementation
- [ ] Update task context after each significant step
- [ ] Run tests continuously
- [ ] Validate integration points

## QUALITY GATES

Every task must pass these quality gates:

1. **Zero Errors**: No linting, compilation, or build errors
2. **Test Coverage**: All new code covered by tests
3. **Documentation**: Public APIs documented
4. **Security**: Security best practices followed
5. **Performance**: No performance regressions
```

### Step 4: Use the Specification

The generated specification serves as a comprehensive guide for AI agents working on your project. It includes:

- Specific guidelines for your technology stack
- Quality requirements that must be met
- A structured implementation process
- Validation commands to verify compliance

## Project Analysis

AgentSpec can automatically analyze existing projects to understand their structure and suggest relevant instructions.

### Analyze Current Directory

```bash
agentspec analyze .
```

### Analyze Specific Project

```bash
agentspec analyze /path/to/project --output analysis.json
```

### Example Analysis Output

```
PROJECT ANALYSIS RESULTS
========================

Project Type: web_frontend
Confidence Score: 0.92

Technology Stack:
  Languages: javascript, typescript
  Frameworks: react (0.9), webpack (0.8)
  Databases: postgresql
  Tools: jest, eslint

File Structure:
  Total files: 45
  Directories: 8
  Config files: 5
  Test files: 12

INSTRUCTION SUGGESTIONS
======================

Top 10 suggested instructions:

1. react_component_architecture
   Confidence: 0.95
   Tags: react, components, architecture
   Reasons: React framework detected; Component files found

2. typescript_configuration
   Confidence: 0.88
   Tags: typescript, type-safety
   Reasons: TypeScript config found; .ts/.tsx files detected

3. jest_testing_setup
   Confidence: 0.85
   Tags: testing, jest, unit-tests
   Reasons: Jest config found; Test files detected
```

### Generate Spec from Analysis

Use analysis results to generate a targeted specification:

```bash
agentspec generate \
  --project-path . \
  --tags auto \
  --output analyzed_spec.md
```

The `--tags auto` flag uses suggestions from project analysis.

## Using Templates

Templates provide quick setup for common project types.

### List Available Templates

```bash
agentspec list-templates
```

Output:
```
All templates (5 total):
========================

## WEB FRONTEND

React Application (ID: react_app)
  Version: 1.0.0
  Description: Template for React applications with modern tooling
  Technologies: react, javascript, webpack
  Complexity: intermediate

Vue Application (ID: vue_app)
  Version: 1.2.0
  Description: Template for Vue.js applications
  Technologies: vue, javascript
  Complexity: beginner

## WEB BACKEND

Python API (ID: python_api)
  Version: 2.0.0
  Description: Template for Python REST APIs using FastAPI
  Technologies: python, fastapi, postgresql
  Complexity: intermediate
```

### Use a Template

```bash
agentspec generate \
  --template react_app \
  --output react_template_spec.md
```

### Template with Parameters

Some templates support customization parameters:

```bash
agentspec generate \
  --template react_app \
  --output custom_react_spec.md \
  --project-name "MyAwesomeApp" \
  --use-typescript true
```

### Template Recommendations

Get template recommendations based on your project:

```bash
agentspec analyze . --suggest-templates
```

## Customization

### Configuration File

Create `.agentspec.yaml` in your project root:

```yaml
agentspec:
  version: "2.0.0"
  
  # Paths
  paths:
    instructions: "custom/instructions"
    templates: "custom/templates"
    output: "specs"
  
  # Behavior
  behavior:
    auto_detect_project: true
    suggest_templates: true
    validate_on_generate: true
  
  # Output preferences
  output:
    format: "markdown"
    include_metadata: true
    language: "en"
  
  # Quality gates
  quality:
    require_tests: true
    min_coverage: 90
    strict_linting: true
```

### Custom Instructions

Create custom instructions in `custom/instructions/`:

```json
{
  "instructions": [
    {
      "id": "my_custom_instruction",
      "version": "1.0.0",
      "tags": ["custom", "company-specific"],
      "content": "Follow our company-specific coding standards...",
      "metadata": {
        "category": "standards",
        "priority": 9,
        "author": "engineering-team"
      }
    }
  ]
}
```

### Custom Templates

Create custom templates in `custom/templates/`:

```json
{
  "id": "company_react_app",
  "name": "Company React Application",
  "description": "React app template with company standards",
  "version": "1.0.0",
  "project_type": "web_frontend",
  "technology_stack": ["react", "typescript", "company-ui-lib"],
  "default_tags": ["react", "typescript", "company-standards"],
  "required_instructions": ["my_custom_instruction", "react_setup"],
  "parameters": {
    "app_name": {
      "type": "string",
      "required": true,
      "description": "Application name"
    }
  }
}
```

## Best Practices

### 1. Start with Analysis

Always analyze your project first to get relevant suggestions:

```bash
agentspec analyze . --output analysis.json
agentspec generate --project-path . --tags auto --output spec.md
```

### 2. Use Templates for Common Patterns

Leverage templates for standard project types:

```bash
agentspec list-templates
agentspec generate --template react_app --output spec.md
```

### 3. Customize for Your Needs

Add project-specific instructions and modify templates:

```bash
agentspec generate \
  --template react_app \
  --tags +security,+accessibility \
  --exclude deprecated_practices \
  --output custom_spec.md
```

### 4. Validate Specifications

Always validate generated specifications:

```bash
agentspec validate spec.md
```

### 5. Version Control Specifications

Include specifications in version control:

```bash
git add project_spec.md
git commit -m "Add AgentSpec specification"
```

### 6. Update Regularly

Keep specifications updated as your project evolves:

```bash
# Re-analyze and update
agentspec analyze . --output new_analysis.json
agentspec generate --project-path . --tags auto --output updated_spec.md
```

## Common Workflows

### New Project Setup

```bash
# 1. Create project directory
mkdir my-new-project
cd my-new-project

# 2. Use interactive mode for guided setup
agentspec interactive

# 3. Or use template for quick start
agentspec generate --template react_app --output spec.md

# 4. Initialize project structure based on spec
# (Follow the generated specification guidelines)
```

### Existing Project Integration

```bash
# 1. Navigate to project
cd existing-project

# 2. Analyze project
agentspec analyze . --output analysis.json

# 3. Generate specification based on analysis
agentspec generate --project-path . --tags auto --output spec.md

# 4. Review and customize specification
agentspec validate spec.md
```

### Team Standardization

```bash
# 1. Create organization templates
mkdir -p .agentspec/templates
# Add custom templates

# 2. Create shared instructions
mkdir -p .agentspec/instructions  
# Add company-specific instructions

# 3. Generate team specification
agentspec generate \
  --template company_standard \
  --tags team-standards,security,testing \
  --output team_spec.md

# 4. Share with team
git add .agentspec/ team_spec.md
git commit -m "Add team AgentSpec standards"
```

## Troubleshooting

### Common Issues

#### 1. Command Not Found

```bash
agentspec: command not found
```

**Solution**: Ensure AgentSpec is installed and in your PATH:
```bash
pip install agentspec
# Or add to PATH if installed locally
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. No Instructions Found

```bash
No instructions found.
```

**Solution**: Check instructions directory exists:
```bash
agentspec list-tags  # Should show available tags
```

#### 3. Template Not Found

```bash
Template not found: my_template
```

**Solution**: List available templates:
```bash
agentspec list-templates
```

#### 4. Project Analysis Fails

```bash
Error analyzing project: Invalid project path
```

**Solution**: Ensure you're in a valid project directory:
```bash
ls -la  # Check for project files (package.json, etc.)
agentspec analyze . --verbose  # Get detailed error info
```

### Getting Help

#### Built-in Help

```bash
agentspec --help
agentspec generate --help
agentspec interactive --help
```

#### Verbose Output

```bash
agentspec --verbose generate --tags frontend,testing
```

#### Debug Mode

```bash
agentspec --debug analyze .
```

## Next Steps

Now that you're familiar with the basics, explore these advanced topics:

### 1. Advanced Configuration
- [Configuration Guide](configuration.md)
- [Custom Instructions](instructions.md)
- [Template Development](templates.md)

### 2. Integration
- [CI/CD Integration](ci-cd.md)
- [IDE Integration](ide-integration.md)
- [Team Workflows](team-workflows.md)

### 3. API Usage
- [Python API](api.md)
- [Plugin Development](plugins.md)
- [Custom Extensions](extensions.md)

### 4. Enterprise Features
- [Enterprise Deployment](enterprise.md)
- [Security Configuration](security.md)
- [Performance Tuning](performance.md)

## Community and Support

- **Documentation**: [docs.agentspec.io](https://docs.agentspec.io)
- **GitHub**: [github.com/agentspec/agentspec](https://github.com/agentspec/agentspec)
- **Issues**: [GitHub Issues](https://github.com/agentspec/agentspec/issues)
- **Discussions**: [GitHub Discussions](https://github.com/agentspec/agentspec/discussions)

Welcome to the AgentSpec community! 🚀
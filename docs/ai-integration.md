# AI Best Practices Integration

AgentSpec provides comprehensive AI best practices integration to help existing projects adopt AI-assisted development workflows safely and effectively.

## Overview

The `agentspec integrate` command analyzes your project and provides tailored recommendations for integrating AI development practices, including:

- **Project Analysis**: Detects project type, technologies, and existing AI tools
- **Security Assessment**: Evaluates security requirements and recommends appropriate guardrails
- **Instruction Recommendations**: Suggests relevant AI development instructions based on your stack
- **Template Suggestions**: Recommends templates for generating comprehensive AI specifications
- **Integration Planning**: Creates phased implementation plans with timelines and tasks
- **File Generation**: Automatically creates configuration files and documentation

## Quick Start

```bash
# Analyze your project for AI integration opportunities
agentspec integrate --analyze-only

# Perform full integration with file generation
agentspec integrate

# Analyze a specific project directory
agentspec integrate /path/to/project --analyze-only

# Get JSON output for programmatic use
agentspec integrate --analyze-only --output-format json
```

## Command Options

### Basic Usage

```bash
agentspec integrate [PROJECT_PATH] [OPTIONS]
```

### Arguments

- `PROJECT_PATH` - Path to project directory (default: current directory)

### Options

- `--analyze-only` - Only analyze the project, don't create integration files
- `--output-format {text,json}` - Output format for analysis results (default: text)

## Analysis Features

### Project Detection

The integration analyzer automatically detects:

- **Project Type**: Web application, mobile app, API service, etc.
- **Technology Stack**: Languages, frameworks, databases, and tools
- **Existing AI Tools**: Copilot, Cursor, OpenAI dependencies, etc.
- **Security Level**: Basic, intermediate, or enterprise based on project characteristics

### AI Tool Detection

Automatically identifies existing AI development tools:

- GitHub Copilot (`.copilot`, `copilot.yml`)
- Cursor IDE (`.cursor`)
- AI dependencies (`openai`, `anthropic`, `langchain`, etc.)
- Custom AI configurations (`ai-config.json`, `.ai/`)
- Prompt directories (`prompts/`, `.prompts/`)

### Security Assessment

Evaluates security requirements based on:

- **Enterprise Indicators**: `SECURITY.md`, `COMPLIANCE.md` files
- **Domain Sensitivity**: Healthcare, finance, banking projects
- **Security Technologies**: Auth, OAuth, encryption, crypto libraries

## Recommendations

### AI Instructions

The analyzer recommends AI development instructions based on your project:

#### Foundational (Always Recommended)
- `human_in_the_loop_architect` - Human oversight in AI-assisted development
- `rich_scratchpad_context` - Comprehensive context management
- `continuous_validation_loop` - Ongoing validation and testing
- `avoid_vibe_coding` - Structured approach over intuitive coding
- `never_commit_unknown_code` - Zero-tolerance for unvalidated code

#### Prompt Engineering (When AI Tools Detected)
- `clarity_context_constraints` - Clear, contextual prompts
- `chain_of_thought_prompting` - Step-by-step reasoning
- `decomposition_prompting` - Breaking down complex tasks

#### Security (Based on Security Level)
- `productivity_risk_paradox` - Balancing speed and security
- `validation_guardrails` - Automated security validation
- `regulatory_compliance_guardrails` - Compliance-focused development
- `enterprise_guardrail_implementation` - Enterprise-grade security
- `alignment_guardrails` - AI alignment and safety measures

#### Domain-Specific

**Frontend Projects**:
- `automated_accessibility_audits` - Accessibility compliance
- `frontend_performance_optimization` - Performance best practices
- `intelligent_component_generation` - Smart component creation

**Backend Projects**:
- `ai_driven_tdd` - AI-assisted test-driven development
- `api_data_model_generation` - Intelligent API design
- `backend_incremental_complexity` - Gradual complexity management

**DevOps Projects**:
- `ai_enhanced_ci_cd` - AI-powered CI/CD pipelines
- `proactive_vulnerability_management` - Security monitoring
- `intelligent_monitoring_observability` - Smart monitoring setup

### Templates

Recommends appropriate templates for generating specifications:

- `ai-prompt-engineering` - Always recommended for prompt best practices
- `ai-security-framework` - For intermediate+ security requirements
- `ai-comprehensive-framework` - For complex projects with multiple technologies

## Integration Planning

### Phased Implementation

The integration planner creates a structured approach:

#### Phase 1: Foundation Setup (1 week)
- Set up rich scratchpad document
- Establish AI collaboration principles
- Train team on basic AI best practices

#### Phase 2: Security Implementation (1-2 weeks, if needed)
- Implement security guardrails
- Set up compliance monitoring
- Configure validation pipelines

#### Phase 3: Domain Specialization (1-2 weeks, if applicable)
- Implement domain-specific AI practices
- Set up specialized validation
- Train team on domain techniques

### Prerequisites

Standard prerequisites for all projects:
- AgentSpec v1.0+ installed
- Team familiar with basic AI tools
- Project has established development workflow

Enterprise-specific prerequisites:
- Security team approval
- Compliance requirements documented
- Identity provider integration available

### Success Metrics

- Zero AI-generated security vulnerabilities in production
- Improved code quality metrics
- Reduced time-to-delivery for new features
- High developer satisfaction with AI tools

## Generated Files

When running full integration (without `--analyze-only`), the following files are created in `.agentspec/`:

### AI Configuration (`ai_config.json`)

```json
{
  "ai_assistance": {
    "enabled": true,
    "collaboration_mode": "peer_programmer",
    "context_management": {
      "rich_scratchpad_enabled": true,
      "scratchpad_path": ".agentspec/ai_scratchpad.md"
    },
    "validation_framework": {
      "continuous_validation": true,
      "zero_tolerance_policy": true
    }
  },
  "security_guardrails": {
    "enabled": true,
    "implementation_level": "intermediate"
  },
  "prompt_engineering": {
    "default_technique": "chain_of_thought",
    "complexity_handling": "incremental"
  }
}
```

### AI Scratchpad (`ai_scratchpad.md`)

A comprehensive template for tracking AI development sessions:

- Project context and technologies
- Session objectives and context
- Changes made and issues encountered
- Prompt library for reuse
- Lessons learned and validation checklist

### Integration Plan (`ai_integration_plan.md`)

Detailed implementation plan including:

- Project analysis summary
- Recommended instructions and templates
- Phased implementation approach
- Prerequisites and success metrics
- Next steps and commands to run

## Example Workflows

### Analyzing a React Project

```bash
$ agentspec integrate ./my-react-app --analyze-only

🔍 Analyzing project: /path/to/my-react-app

🔍 Project Analysis Results
==================================================
Project Type: web_frontend
Technologies: React, TypeScript, Node.js
AI Tools Present: true
Security Level: intermediate
Integration Priority: high

📋 Recommended AI Instructions (8):
  - human_in_the_loop_architect
  - rich_scratchpad_context
  - continuous_validation_loop
  - clarity_context_constraints
  - chain_of_thought_prompting
  - automated_accessibility_audits
  - frontend_performance_optimization
  - intelligent_component_generation

📄 Recommended Templates (2):
  - ai-prompt-engineering
  - ai-comprehensive-framework
```

### Full Integration

```bash
$ agentspec integrate ./my-react-app

🔍 Analyzing project: /path/to/my-react-app
[Analysis output...]

✅ AI Best Practices Integration Complete!
📁 Files created in: /path/to/my-react-app/.agentspec
📖 Review the integration plan: .agentspec/ai_integration_plan.md
🚀 Start with: agentspec generate --template ai-comprehensive-framework
```

### JSON Output for Automation

```bash
$ agentspec integrate --analyze-only --output-format json | jq '.recommended_ai_instructions'

[
  "human_in_the_loop_architect",
  "rich_scratchpad_context",
  "continuous_validation_loop",
  "avoid_vibe_coding",
  "never_commit_unknown_code"
]
```

## Integration with Existing Workflows

### CI/CD Integration

Add AI integration analysis to your CI pipeline:

```yaml
# .github/workflows/ai-integration.yml
name: AI Integration Analysis
on: [push, pull_request]

jobs:
  ai-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install AgentSpec
        run: pip install agentspec
      - name: Analyze AI Integration
        run: |
          agentspec integrate --analyze-only --output-format json > ai-analysis.json
          cat ai-analysis.json
      - name: Upload Analysis
        uses: actions/upload-artifact@v3
        with:
          name: ai-integration-analysis
          path: ai-analysis.json
```

### Pre-commit Hooks

Validate AI integration before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ai-integration-check
        name: AI Integration Check
        entry: agentspec integrate --analyze-only
        language: system
        pass_filenames: false
```

## Best Practices

### Regular Analysis

- Run integration analysis when adding new technologies
- Re-evaluate security level when handling sensitive data
- Update AI instructions as project complexity grows

### Team Adoption

- Start with foundational instructions for all team members
- Gradually introduce domain-specific practices
- Provide training on prompt engineering techniques

### Security Considerations

- Always review generated AI configurations
- Implement validation guardrails before production
- Regular security audits of AI-generated code

### Monitoring and Metrics

- Track AI tool usage and effectiveness
- Monitor code quality metrics over time
- Collect team feedback on AI integration experience

## Troubleshooting

### Common Issues

**Project not detected correctly**:
- Ensure project has recognizable configuration files
- Check that project structure follows standard conventions
- Manually specify project type if needed

**Security level assessment incorrect**:
- Add `SECURITY.md` file for enterprise projects
- Include security-related dependencies in package files
- Review and adjust security recommendations manually

**Missing AI tool detection**:
- Ensure AI tool configuration files are present
- Check that AI dependencies are listed in package files
- Manually configure AI settings if needed

### Getting Help

- Check the integration plan for detailed next steps
- Review generated scratchpad template for guidance
- Consult AgentSpec documentation for specific instructions
- Open issues on GitHub for integration problems

## Advanced Usage

### Custom Integration Rules

Create custom integration rules by extending the analyzer:

```python
from agentspec.core.ai_integrator import AIBestPracticesIntegrator

class CustomIntegrator(AIBestPracticesIntegrator):
    def _assess_security_requirements(self, analysis):
        # Custom security assessment logic
        if "custom-security-framework" in analysis.get("technologies", []):
            return "enterprise"
        return super()._assess_security_requirements(analysis)
```

### Programmatic Usage

Use the integrator programmatically:

```python
from pathlib import Path
from agentspec.core.ai_integrator import AIBestPracticesIntegrator
from agentspec.core.instruction_database import InstructionDatabase
from agentspec.core.template_manager import TemplateManager
from agentspec.core.context_detector import ContextDetector

# Initialize services
instruction_db = InstructionDatabase()
template_manager = TemplateManager()
context_detector = ContextDetector()

# Create integrator
integrator = AIBestPracticesIntegrator(
    Path("./my-project"),
    instruction_db,
    template_manager,
    context_detector
)

# Analyze project
analysis = integrator.analyze_project()
plan = integrator.generate_integration_plan(analysis)

# Create integration files
integrator.create_integration_files(analysis, plan)
```

This comprehensive AI integration system helps teams adopt AI-assisted development practices safely and effectively, with tailored recommendations based on project characteristics and security requirements.
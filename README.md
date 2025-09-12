# AgentSpec

[![Tests](https://github.com/keyurgolani/AgentSpec/workflows/CI/badge.svg)](https://github.com/keyurgolani/AgentSpec/actions)
[![Coverage](https://codecov.io/gh/keyurgolani/AgentSpec/branch/main/graph/badge.svg)](https://codecov.io/gh/keyurgolani/AgentSpec)
[![PyPI version](https://badge.fury.io/py/agentspec.svg)](https://badge.fury.io/py/agentspec)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Specification-Driven Development for AI Agents**

AgentSpec is a comprehensive toolkit that enables AI agents to follow best practices through structured specifications, intelligent context detection, and automated validation. Transform your AI development workflow with modular instruction systems and enterprise-ready architecture.

## 🚀 Quick Start

```bash
# Install AgentSpec
pip install agentspec

# Generate your first spec with enhanced features
agentspec interactive

# Analyze your project automatically
agentspec analyze ./my-project

# Integrate AI best practices into existing projects
agentspec integrate ./my-project

# Use templates for quick setup
agentspec generate --template react-app --output spec.md
```

## ✨ Key Features

- **📋 Intelligent Spec Generation**: 100+ curated instructions with smart tagging system
- **🤖 AI Best Practices Integration**: Research-based framework for AI-assisted development
- **🔒 Security Guardrails**: Multi-layered protection against AI-generated vulnerabilities
- **🎯 Domain-Specific Guidance**: Specialized blueprints for DevOps, Frontend, Backend, and more
- **🔄 Resumable Development**: Task contexts that preserve state across sessions
- **✅ Quality Enforcement**: Zero-tolerance validation with comprehensive testing
- **🏗️ Modular Architecture**: Clean separation of concerns and DRY principles
- **📊 Progress Tracking**: Automated compliance reporting and metrics

## 🎯 Core Concepts

### Specification-Driven Development

AgentSpec uses structured specifications to guide AI agents through complex development tasks while maintaining code quality and consistency.

### Task Context Management

Every development task creates a markdown context file that records:

- Objective and requirements
- Context gathered during analysis
- Changes made step-by-step
- Issues encountered and solutions
- Next steps and completion status

### Validation Framework

Comprehensive validation ensures:

- No linting, compilation, or build errors
- Test coverage requirements met
- Documentation stays current
- Security best practices followed

## 📁 Project Structure

```
your-project/
├── .agentspec/              # AgentSpec configuration
├── task_contexts/           # Resumable task contexts
├── project_context.md       # Shared project knowledge
├── project_spec.md         # Generated specification
├── tests/                  # Test directories (unit/, integration/, e2e/)
├── test                    # Consolidated test runner
└── scripts/
    └── validate.sh          # Validation suite
```

## 🛠️ Usage Examples

#### Generate a Full-Stack Web App Spec

```bash
agentspec generate --tags general,testing,frontend,backend,api,security --output fullstack_spec.md
```

#### Generate Project-Specific Specs

```bash
# Enterprise web application with security and compliance
agentspec generate --template enterprise-web-app --output enterprise-spec.md

# SaaS platform with multi-tenancy and billing
agentspec generate --template saas-platform --output saas-spec.md

# E-commerce platform with payments and recommendations
agentspec generate --template e-commerce-platform --output ecommerce-spec.md

# Fintech application with regulatory compliance
agentspec generate --template fintech-app --output fintech-spec.md

# Healthcare platform with HIPAA compliance
agentspec generate --template healthcare-platform --output healthcare-spec.md
```

#### Use Templates for Quick Setup

```bash
# List available templates
agentspec list-templates

# Web applications
agentspec generate --template react-app --output react_spec.md
agentspec generate --template vue-app --output vue_spec.md
agentspec generate --template base-web-app --output webapp_spec.md

# Backend services
agentspec generate --template python-api --output api_spec.md
agentspec generate --template nodejs-api --output node_api_spec.md
agentspec generate --template microservice --output microservice_spec.md

# Mobile and specialized platforms
agentspec generate --template mobile-app --output mobile_spec.md
agentspec generate --template data-science-platform --output datascience_spec.md
```

#### Smart Project Analysis

```bash
# Analyze project and get suggestions
agentspec analyze ./my-project --output analysis.json

# Generate spec with project context
agentspec generate --tags general,testing --project-path ./my-project --output spec.md
```

#### AI Best Practices Integration

```bash
# Analyze project for AI integration opportunities
agentspec integrate ./my-project --analyze-only

# Full integration with file generation
agentspec integrate ./my-project

# Get JSON output for programmatic use
agentspec integrate ./my-project --analyze-only --output-format json
```

#### Interactive Mode

```bash
agentspec interactive
# Features: project detection, template suggestions, smart recommendations
```

## 🧪 Testing

AgentSpec includes a comprehensive test runner that consolidates all testing capabilities:

```bash
# Run comprehensive test suite (default)
./test

# Run specific test types
./test --unit           # Unit tests only
./test --integration    # Integration tests only
./test --e2e           # End-to-end tests only
./test --lint          # Code quality checks
./test --coverage      # Generate coverage report

# Utility commands
./test --clean         # Clean test artifacts
./test --install-deps  # Install test dependencies
./test --verbose       # Verbose output
```

The default comprehensive test suite includes:

- CLI functionality tests
- Spec generation validation
- Setup script testing
- Code quality checks (linting, formatting, security)
- All pytest-based tests with coverage reporting

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [AI Integration Guide](docs/ai-integration.md)
- [AI Best Practices Integration](docs/ai-best-practices.md)
- [Specification Reference](docs/specifications.md)
- [API Documentation](docs/api.md)

## 🏷️ Available Templates & Tags

### Project Templates

| Template                    | Description                                   | Use Case                       |
| --------------------------- | --------------------------------------------- | ------------------------------ |
| **enterprise-web-app**      | Large-scale enterprise applications           | Corporate web platforms        |
| **saas-platform**           | Multi-tenant SaaS applications                | Software as a Service products |
| **e-commerce-platform**     | Online retail and marketplace platforms       | E-commerce and retail          |
| **fintech-app**             | Financial technology applications             | Banking, payments, trading     |
| **healthcare-platform**     | Healthcare applications with HIPAA compliance | Medical and health tech        |
| **microservice**            | Distributed microservice architectures        | Scalable backend services      |
| **mobile-app**              | Cross-platform mobile applications            | iOS and Android apps           |
| **react-app**               | Modern React web applications                 | Frontend single-page apps      |
| **vue-app**                 | Vue.js web applications                       | Frontend applications          |
| **nodejs-api**              | Node.js REST APIs                             | Backend API services           |
| **python-api**              | Python REST APIs                              | Backend API services           |
| **data-science-platform**   | ML and data science platforms                 | Analytics and AI/ML workflows  |
| **ai-enhanced-development** | AI-assisted development workflows             | Projects using AI coding tools |
| **secure-enterprise-app**   | High-security enterprise applications         | Security-critical applications |

### Available Tags

| Category        | Tags                                              | Description                       |
| --------------- | ------------------------------------------------- | --------------------------------- |
| **General**     | `general`, `quality`, `standards`                 | Core development practices        |
| **AI-Enhanced** | `ai-enhanced`, `prompt-engineering`, `validation` | AI-assisted development           |
| **Security**    | `security`, `compliance`, `encryption`, `audit`   | Security and compliance measures  |
| **Testing**     | `testing`, `tdd`, `validation`                    | Testing strategies and frameworks |
| **Frontend**    | `frontend`, `react`, `vue`, `angular`             | Frontend development practices    |
| **Backend**     | `backend`, `api`, `database`, `microservices`     | Server-side development           |
| **Languages**   | `javascript`, `typescript`, `python`, `dart`      | Language-specific guidelines      |
| **DevOps**      | `docker`, `kubernetes`, `ci-cd`, `deployment`     | Infrastructure and deployment     |
| **Industry**    | `fintech`, `healthcare`, `e-commerce`, `saas`     | Industry-specific requirements    |

## 🔧 Configuration

AgentSpec can be customized through configuration files:

```yaml
# ~/.agentspec/config.yaml
agentspec:
  version: "1.0.0"

  paths:
    instructions: "data/instructions"
    templates: "data/templates"
    output: "."

  behavior:
    auto_detect_project: true
    suggest_templates: true
    validate_on_generate: true

  logging:
    level: "INFO"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Ensure all validations pass
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Why AgentSpec?

- **Consistency**: Ensures AI agents follow the same high standards across all tasks
- **Resumability**: Never lose context when development is interrupted
- **Quality**: Zero-tolerance policy for errors and technical debt
- **Scalability**: Grows with your project from prototype to production
- **Community**: Benefit from collective best practices and shared knowledge

---

**Transform your AI development workflow with AgentSpec - where intelligent development meets uncompromising quality.**

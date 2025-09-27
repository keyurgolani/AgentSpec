# AgentSpec

[![Tests](https://github.com/keyurgolani/AgentSpec/workflows/CI/badge.svg)](https://github.com/keyurgolani/AgentSpec/actions)
[![Coverage](https://codecov.io/gh/keyurgolani/AgentSpec/branch/main/graph/badge.svg)](https://codecov.io/gh/keyurgolani/AgentSpec)
[![PyPI version](https://badge.fury.io/py/agentspec.svg)](https://badge.fury.io/py/agentspec)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Transform AI coding assistants into professional development partners with comprehensive instruction guides that ensure production-ready, secure, and maintainable code.

## Quick Start

```bash
# Install
pip install agentspec

# Generate instructions for your project
agentspec generate --template react_app --output instructions.md

# Share instructions.md with your AI assistant and start coding!
```

**Result:** Your AI assistant now follows professional standards and produces production-ready code.

## Features

- **106 Proven Instructions**: Coding guidelines organized by technology and domain
- **15 Project Templates**: Ready-made instruction sets for common scenarios
- **Smart Analysis**: Automatically detects your tech stack and suggests relevant instructions
- **AI-Optimized**: Instructions designed specifically for AI coding assistants
- **Security & Quality**: Built-in best practices for production-ready code

## How It Works

1. **Choose a template** or let AgentSpec analyze your project
2. **Generate instructions** tailored to your technology stack
3. **Share with your AI assistant** (ChatGPT, Copilot, Claude, etc.)
4. **Get professional-grade code** that follows industry standards

## Available Templates

**Technology**: `react_app`, `python-api`, `nodejs-api`, `vue-frontend`, `mobile-app`

**Domain**: `saas-application`, `ecommerce-application`, `fintech-application`, `healthcare-application`, `data-science-application`

**Architecture**: `web-application`, `enterprise-web-application`, `microservice`

**Methodology**: `ai-assisted-development`, `security-focused-development`

## Usage Examples

```bash
# Generate instructions for different project types
agentspec generate --template react_app --output instructions.md
agentspec generate --template python-api --output instructions.md
agentspec generate --template ecommerce-application --output instructions.md

# Analyze existing projects
agentspec analyze ./my-project
agentspec generate --project-path ./my-project --tags auto --output instructions.md

# Interactive mode
agentspec interactive

# Browse available options
agentspec list-templates
agentspec list-tags
```

## Example

**Without AgentSpec:**
```
You: "Create a React login form"
AI: Basic form with no validation, security issues, no tests
```

**With AgentSpec:**
```
You: "Create a React login form" + AgentSpec instructions
AI: Production-ready form with validation, security, accessibility, tests, and documentation
```

## Documentation

- **[Getting Started](docs/)** - Complete documentation and guides
- **[Examples](examples/)** - Real-world project examples
- **[API Reference](docs/api-reference.md)** - Python API documentation



## Who Should Use AgentSpec?

- Developers using AI assistants (GitHub Copilot, ChatGPT, Claude, etc.)
- Teams wanting consistent coding standards
- Anyone building production applications with AI assistance

## Getting Started

1. **Install:** `pip install agentspec`
2. **Generate instructions:** `agentspec generate --template react_app --output instructions.md`
3. **Share with AI:** Copy instructions.md content to your AI assistant
4. **Start coding:** Ask AI to build features following the instructions

For detailed guides, see the [documentation](docs/).



## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

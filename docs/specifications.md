# AgentSpec Specifications Reference

This document provides a comprehensive reference for all available instructions and tags in AgentSpec.

## Instruction Categories

### General Development

Core practices that apply to all projects, focusing on context management, quality enforcement, and systematic development approaches.

#### Context Management
**Tags**: `general`, `persistence`, `resume`, `tracking`

For each task create/update a markdown file (`task_contexts/<task_name>.md`) that records: objective, context gathered, changes made, and next steps. Load this file at task start and resume from where it left off.

#### Project Context
**Tags**: `general`, `persistence`, `commands`, `debugging`

Maintain `project_context.md` that records: failed commands and alternatives, temporary files and purposes, lessons learned. Reference this file to avoid repeating mistakes.

#### Thorough Analysis
**Tags**: `general`, `analysis`, `debugging`, `investigation`

Begin every task with thorough code analysis, identify exact locations to fix, and define crisp exit criteria. Perform comprehensive code review before making changes.

#### No Error Policy
**Tags**: `general`, `quality`, `testing`, `integration`

After every task, ensure zero linting, compilation, build or deployment errors. Fix all issues before marking task complete. Verify backend-frontend integration consistency.

#### Documentation Tracking
**Tags**: `documentation`, `design`, `tracking`, `maintenance`

Log every change that deviates from design, update design docs, record temporary files in context. Keep documentation synchronized with implementation.

### Testing & Quality Assurance

Comprehensive testing strategies and quality enforcement practices.

#### Test-Driven Development
**Tags**: `testing`, `tdd`, `quality`, `validation`

Write or update tests BEFORE implementing code. Ensure tests pass and never modify tests to satisfy failing code. Create comprehensive test cases before implementation.

#### Comprehensive Test Suite
**Tags**: `testing`, `automation`, `validation`, `quality`

Build unit, integration, and end-to-end tests organized by feature. Run suite after every change. Create `test` script that shows progress and exits on first failure.

#### Runtime Validation
**Tags**: `general`, `testing`, `browser`, `validation`

Use browser console logs and automated testing to confirm application loads without errors and all interactions work. Iterate until zero errors remain.

#### Linting Standards
**Tags**: `quality`, `linting`, `standards`, `javascript`, `python`, `general`

Resolve all lint warnings across entire repository. Treat all warnings as errors. Never skip tests or bypass quality guardrails.

### Frontend Development

Modern frontend development practices covering UI/UX, accessibility, and performance.

#### Frontend State Management
**Tags**: `frontend`, `state`, `react`, `vue`, `angular`

Implement proper state management patterns (Redux, Vuex, NgRx) for complex applications. Avoid prop drilling and ensure predictable state updates.

#### Accessibility Compliance
**Tags**: `accessibility`, `frontend`, `ui`, `compliance`

Ensure WCAG 2.1 AA compliance with proper ARIA labels, keyboard navigation, color contrast ratios, and screen reader compatibility.

#### Mobile Responsiveness
**Tags**: `frontend`, `mobile`, `responsive`, `ui`

Ensure full mobile responsiveness with touch-friendly interfaces, proper viewport settings, and performance optimization for mobile devices.

### Backend Development

Server-side development practices focusing on APIs, databases, and system architecture.

#### API Design
**Tags**: `api`, `design`, `rest`, `standards`

Follow RESTful principles with proper HTTP status codes, versioning, pagination, filtering, and comprehensive documentation. Implement consistent error responses.

#### Database Optimization
**Tags**: `database`, `performance`, `optimization`, `queries`

Optimize queries with proper indexing, connection pooling, and query analysis. Implement database migrations with rollback capabilities.

#### Security Best Practices
**Tags**: `security`, `authentication`, `authorization`, `validation`

Implement input validation, sanitization, authentication, secure headers, HTTPS, and proper session management. Never commit secrets to version control.

#### Error Handling
**Tags**: `error-handling`, `reliability`, `logging`, `debugging`

Implement comprehensive error handling with structured logging, user-friendly messages, and graceful degradation. Use appropriate log levels.

### Language-Specific Guidelines

#### TypeScript Safety
**Tags**: `typescript`, `javascript`, `type-safety`, `quality`

Never use 'any' types. Use proper type definitions, interfaces, and generics. Enable strict mode and resolve all type errors.

#### Python Type Hints
**Tags**: `python`, `type-safety`, `quality`, `documentation`

Use comprehensive type hints for all functions, parameters, return values, and class attributes. Import typing modules for complex types.

### DevOps & Infrastructure

Deployment, containerization, and operational practices.

#### Docker Containerization
**Tags**: `docker`, `deployment`, `containerization`, `devops`

Containerize with multi-stage Docker builds. Include development, testing, and production configurations. Use docker-compose for complex setups.

#### CI/CD Pipeline
**Tags**: `ci-cd`, `automation`, `deployment`, `testing`

Implement comprehensive CI/CD pipeline with automated testing, code quality checks, security scanning, and deployment automation.

#### Monitoring & Observability
**Tags**: `monitoring`, `observability`, `logging`, `metrics`

Implement comprehensive monitoring with metrics, logs, and traces. Set up alerts for critical failures and performance degradation.

#### Backup & Recovery
**Tags**: `backup`, `recovery`, `reliability`, `data`

Implement automated backup strategies with regular recovery testing. Document disaster recovery plans and RTO/RPO requirements.

### Architecture & Design

System architecture and design patterns for scalable applications.

#### Modular Architecture
**Tags**: `architecture`, `modularity`, `maintainability`, `refactoring`

Break large files into single-responsibility modules, eliminate duplicate code, remove dead code. Ensure each file has one clear conceptual responsibility.

#### Microservices Architecture
**Tags**: `architecture`, `microservices`, `scalability`, `distributed`

Design microservices with proper boundaries, communication patterns, and distributed system concerns like circuit breakers and bulkheads.

#### Performance Optimization
**Tags**: `performance`, `optimization`, `caching`, `efficiency`

Implement caching strategies, optimize database queries, use lazy loading, and monitor performance metrics. Profile code to identify bottlenecks.

### Advanced Features

#### Feature Flags
**Tags**: `feature-flags`, `deployment`, `rollout`, `experimentation`

Implement feature flag system for controlled rollouts, A/B testing, and quick rollback capabilities. Use proper flag lifecycle management.

#### Rate Limiting
**Tags**: `rate-limiting`, `api`, `security`, `performance`

Implement rate limiting with appropriate strategies (fixed window, sliding window, token bucket) based on use case requirements.

#### Webhook Handling
**Tags**: `webhooks`, `api`, `integration`, `reliability`

Implement robust webhook handling with validation, retry logic, idempotency, and security measures like signature verification.

#### Real-time Features
**Tags**: `realtime`, `websockets`, `sse`, `notifications`

Implement real-time features using WebSockets or Server-Sent Events with connection management, reconnection logic, and scalability considerations.

#### Search Functionality
**Tags**: `search`, `elasticsearch`, `indexing`, `performance`

Implement efficient search with proper indexing, full-text search capabilities, faceted search, and search analytics.

#### Payment Processing
**Tags**: `payments`, `security`, `integration`, `compliance`

Implement secure payment processing with PCI compliance, proper error handling, refund capabilities, and webhook handling for payment providers.

#### GDPR Compliance
**Tags**: `gdpr`, `privacy`, `compliance`, `data-protection`

Implement GDPR compliance with consent management, data portability, right to deletion, and privacy by design principles.

## Tag Reference

### By Category

| Category | Tags | Count |
|----------|------|-------|
| **General** | `general`, `quality`, `standards`, `persistence`, `tracking` | 5 |
| **Testing** | `testing`, `tdd`, `validation`, `automation`, `browser` | 5 |
| **Frontend** | `frontend`, `ui`, `react`, `vue`, `angular`, `mobile`, `responsive` | 7 |
| **Backend** | `backend`, `api`, `database`, `security`, `performance` | 5 |
| **Languages** | `javascript`, `typescript`, `python`, `type-safety` | 4 |
| **DevOps** | `docker`, `ci-cd`, `deployment`, `monitoring`, `backup` | 5 |
| **Architecture** | `architecture`, `microservices`, `modularity`, `maintainability` | 4 |

### By Usage Frequency

| Tag | Instructions | Common Use Cases |
|-----|-------------|------------------|
| `general` | 4 | All projects |
| `testing` | 3 | Quality assurance |
| `security` | 3 | Secure applications |
| `api` | 3 | Backend services |
| `frontend` | 2 | UI applications |
| `performance` | 2 | High-load systems |
| `database` | 2 | Data-driven apps |

## Spec Generation Examples

### Full-Stack Web Application
```bash
python agentspec.py --tags general,testing,frontend,backend,api,database,security,ci-cd
```

**Includes**: Context management, testing frameworks, UI guidelines, API design, database optimization, security practices, deployment automation.

### React Frontend Application
```bash
python agentspec.py --tags general,testing,frontend,react,typescript,accessibility,mobile
```

**Includes**: Component architecture, state management, type safety, accessibility compliance, responsive design.

### Python API Service
```bash
python agentspec.py --tags general,testing,python,api,database,security,monitoring
```

**Includes**: Type hints, API design, database optimization, security practices, observability.

### Microservices Architecture
```bash
python agentspec.py --tags general,testing,microservices,docker,ci-cd,monitoring,security
```

**Includes**: Service boundaries, containerization, deployment pipelines, distributed system patterns.

### Mobile-First Progressive Web App
```bash
python agentspec.py --tags general,testing,frontend,mobile,responsive,realtime,performance
```

**Includes**: Mobile optimization, responsive design, real-time features, performance optimization.

## Custom Instructions

### Adding New Instructions

To extend AgentSpec with custom instructions:

1. **Identify the practice**: What specific development practice does this address?
2. **Define appropriate tags**: Use existing tags when possible
3. **Write clear instruction**: Specific, actionable guidance
4. **Test effectiveness**: Validate with real projects

### Instruction Template

```python
"instruction_key": {
    "tags": ["primary_tag", "secondary_tag", "context_tag"],
    "instruction": "Clear, actionable instruction that an AI agent can follow. Include specific steps, tools, and success criteria."
}
```

### Tag Guidelines

- **Primary tag**: Main category (general, testing, frontend, etc.)
- **Secondary tag**: Specific technology or practice
- **Context tag**: When/where this applies

### Example Custom Instruction

```python
"graphql_optimization": {
    "tags": ["api", "graphql", "performance"],
    "instruction": "Implement GraphQL query optimization with depth limiting (max 10 levels), complexity analysis (max 1000 points), and DataLoader pattern for N+1 prevention. Add query whitelisting for production."
}
```

## Validation Framework

Each generated spec includes validation requirements:

### Quality Gates
1. **Zero Errors**: No linting, compilation, or build errors
2. **Test Coverage**: All new code covered by tests  
3. **Documentation**: Public APIs documented
4. **Security**: Security practices followed
5. **Performance**: No performance regressions

### Implementation Checklist
- [ ] Load existing task context
- [ ] Analyze code thoroughly  
- [ ] Define clear exit criteria
- [ ] Update context after each step
- [ ] Run tests continuously
- [ ] Validate integration points
- [ ] Update documentation

### Validation Commands
```bash
# Comprehensive validation
bash scripts/validate.sh

# Quick validation
bash scripts/validate.sh --quick

# Generate compliance report
bash scripts/validate.sh --report
```

This reference provides the foundation for creating effective, project-specific specifications that guide AI agents through high-quality development practices.
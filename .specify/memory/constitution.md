<!--
Sync Impact Report:
- Version: NEW → 1.0.0
- Modified Principles: Initial creation with 7 core principles
- Added Sections: Core Principles, Project Principles, Technical Constraints, Development Standards, Governance
- Templates Status:
  ✅ plan-template.md - reviewed, compatible with TDD principle (70% coverage requirement)
  ✅ spec-template.md - reviewed, compatible with user story requirements
  ✅ tasks-template.md - reviewed, compatible with TDD and independent testing requirements
  ✅ Command files (.github/prompts/*.md) - reviewed, no agent-specific conflicts
- Follow-up TODOs: None
-->

# mystock3 Constitution

## Project Principles

### Code Quality
- Code MUST be concise and readable
- Each function MUST include documentation comments explaining its purpose and usage
- Prefer clarity over cleverness; avoid obfuscated or overly complex implementations

**Rationale**: Maintainability and team collaboration require code that can be understood quickly by any developer.

### Testing Strategy
- External API requests MUST be minimized to avoid rate limits and unnecessary costs
- Each test MUST verify functionality in a single execution; no repeated identical requests
- Mock external dependencies when practical for unit tests

**Rationale**: Efficient testing reduces development costs and respects external service limitations.

### Deployment & Scalability
- Architecture MUST be designed for Azure cloud deployment from the start
- Start with minimal resource configurations and design for horizontal scaling
- Infrastructure-as-Code (IaC) MUST use Azure Bicep for all deployments

**Rationale**: Azure-native design ensures cost optimization and seamless production deployment.

### User Experience
- User interfaces MUST be intuitive and require minimal learning curve
- Response times MUST be optimized; users should not wait unnecessarily
- UI feedback MUST be immediate for all user actions

**Rationale**: User satisfaction drives adoption; poor UX leads to abandonment.

### Performance & Dependencies
- Unnecessary libraries are PROHIBITED; justify every dependency
- Keep dependency tree minimal to reduce bundle size and attack surface
- Regularly audit and remove unused dependencies

**Rationale**: Minimal dependencies improve performance, security, and maintainability.

## Core Principles

### I. API-First Design
- All backend services MUST expose RESTful APIs with clear contract definitions
- API schemas MUST be validated using Pydantic or equivalent validation frameworks
- API documentation MUST be auto-generated and kept in sync with implementation
- Breaking changes MUST follow semantic versioning with proper deprecation notices

**Rationale**: API-first design enables frontend/backend independence, clear contracts, and easier integration testing.

### II. Serverless-Native Architecture
- Architecture MUST leverage Azure serverless services (Functions, Container Apps, Cosmos DB, etc.)
- Cost optimization MUST be a primary consideration in architectural decisions
- Services MUST be stateless and horizontally scalable by design
- Cold start times MUST be minimized through appropriate service selection

**Rationale**: Serverless architecture on Azure provides cost efficiency, automatic scaling, and reduced operational overhead.

### III. Test-Driven Development (NON-NEGOTIABLE)
- TDD MUST be followed: Write tests → Get approval → Tests fail → Implement → Tests pass
- Code coverage MUST be at least 70% across the entire codebase (measured and enforced)
- Red-Green-Refactor cycle MUST be strictly adhered to
- Tests MUST be committed before implementation code in version control

**Rationale**: TDD ensures correctness, prevents regressions, and creates a safety net for refactoring. The 70% coverage requirement is mandatory for production readiness.

### IV. Real-time Data Efficiency
- API rate limits MUST be respected and managed proactively
- Caching strategies MUST be implemented to minimize redundant API calls
- Data fetch operations MUST be batched when possible
- Rate limit tracking and exponential backoff MUST be implemented for all external APIs

**Rationale**: Efficient data management prevents service disruptions, reduces costs, and ensures reliable operation.

### V. Azure-Native Deployment
- All infrastructure MUST be defined using Azure Bicep (IaC)
- Manual Azure resource creation is PROHIBITED in production environments
- Deployment pipelines MUST validate Bicep templates before applying
- Infrastructure changes MUST be version-controlled and reviewed like code

**Rationale**: Infrastructure-as-Code ensures reproducibility, version control, and prevents configuration drift.

### VI. Security & Authentication
- User authentication MUST use JWT tokens with appropriate expiration
- Password hashing MUST use bcrypt with appropriate work factor (minimum 12 rounds)
- Secrets and credentials MUST NEVER be committed to version control
- Azure Key Vault MUST be used for all production secrets management
- All API endpoints MUST validate authentication and authorization

**Rationale**: Security is non-negotiable. Proper authentication, encryption, and secret management protect user data and prevent breaches.

### VII. Observability & Monitoring
- All services MUST implement structured logging (JSON format)
- Critical operations MUST emit metrics for monitoring
- Error tracking MUST capture stack traces and context
- Performance metrics (latency, throughput) MUST be collected and monitored
- Azure Application Insights or equivalent MUST be configured for production

**Rationale**: Observability enables rapid incident detection, debugging, and performance optimization in production.

## Technical Constraints

### Technology Stack (FIXED)
- **Backend Language**: Python 3.11 (no other Python version permitted)
- **Frontend Framework**: Vue 3 (Composition API preferred)
- **API Framework**: FastAPI
- **UI Components**: Tabler for UI framework
- **Charts**: ECharts for data visualization
- **Testing**: pytest for backend, Playwright for E2E testing
- **Infrastructure**: Azure Bicep for IaC
- **State Management**: Pinia for Vue state management

**Rationale**: Standardizing the technology stack reduces cognitive load, simplifies onboarding, and ensures team expertise remains focused.

### Required Tools
All projects MUST include and use:
- **pytest**: Backend testing framework
- **Pinia**: Frontend state management
- **Tabler**: UI component library
- **ECharts**: Data visualization
- **Playwright**: End-to-end testing
- **Bicep**: Infrastructure-as-Code

## Development Standards

### Code Style & Formatting
- **Python**: Follow PEP 8; use `black` for formatting, `ruff` for linting
- **Vue/JavaScript**: Follow Vue 3 Style Guide; use ESLint + Prettier
- **Bicep**: Follow Azure Bicep best practices; use Bicep linter
- All code MUST pass linting before commit (enforced via pre-commit hooks)

### Environment Variables
- Environment variables MUST follow naming convention: `MYSTOCK3_<CATEGORY>_<NAME>`
- All required environment variables MUST be documented in `.env.example`
- Local development MUST use `.env` files (gitignored)
- Production MUST use Azure Key Vault or App Configuration

### Database Schema (Cosmos DB)
- All Cosmos DB containers MUST have documented schema specifications
- Partition key selection MUST be justified based on access patterns
- Schema migrations MUST be versioned and tested before production deployment
- No schema changes without updating documentation

### TDD Workflow
- Follow strict Red-Green-Refactor cycle:
  1. **Red**: Write a failing test for the desired functionality
  2. **Green**: Write minimal code to make the test pass
  3. **Refactor**: Improve code quality while keeping tests green
- Test coverage MUST be verified before merging PRs (70% minimum)

## Governance

### Constitution Authority
This constitution supersedes all other development practices and guidelines. When conflicts arise, this document takes precedence.

### Amendment Process
1. Amendments MUST be proposed via GitHub issue with `constitution` label
2. Major changes require team discussion and consensus
3. Amendment PR MUST update version number following semantic versioning:
   - **MAJOR**: Breaking changes, principle removal/redefinition
   - **MINOR**: New principle or section added
   - **PATCH**: Clarifications, typo fixes, non-semantic changes
4. Amendment PR MUST include migration plan if existing code is affected
5. All dependent templates and documentation MUST be updated in the same PR

### Semantic Versioning
- Version format: `MAJOR.MINOR.PATCH`
- Starting version: `1.0.0`
- Version increments MUST follow semantic versioning rules
- Version history MUST be maintained in this document

### Compliance & Review
- All Pull Requests MUST verify compliance with this constitution
- Constitution violations MUST be justified in PR description or rejected
- Quarterly constitution review MUST assess if principles remain relevant
- Any complexity that violates principles MUST be documented with justification

### Production Hotfix Process
Hotfixes MAY bypass normal TDD workflow under these conditions:
- Critical production incident (P0/P1 severity)
- Tests added within 24 hours post-deployment
- Retrospective conducted to prevent recurrence
- Hotfix process abuse triggers mandatory TDD training

**Version**: 1.0.0 | **Ratified**: 2025-11-05 | **Last Amended**: 2025-11-05

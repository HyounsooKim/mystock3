# Research: MyStock 주식 포트폴리오 앱

**Feature**: MyStock Stock Portfolio App  
**Date**: 2025-11-05  
**Purpose**: Technology decisions, best practices, and architectural patterns for implementation

## Executive Summary

This research document consolidates technical decisions for building a stock portfolio management web application on Azure. All technology choices are pre-determined by the project constitution, with research focused on best practices, integration patterns, and implementation strategies for the selected stack (Python 3.11, FastAPI, Vue 3, Cosmos DB, Azure serverless architecture).

---

## 1. Authentication & Security

### Decision: JWT with bcrypt Password Hashing

**Rationale**:
- **JWT (JSON Web Tokens)**: Industry standard for stateless authentication in REST APIs. Enables horizontal scaling without session storage. 7-day expiration balances security with user convenience.
- **bcrypt**: Computationally expensive password hashing algorithm resistant to brute-force attacks. Constitution mandates minimum 12 rounds (work factor).
- **Azure Key Vault**: Centralized secrets management prevents credentials in code/config files.

**Best Practices**:
1. **JWT Structure**:
   ```python
   payload = {
       "sub": user_email,
       "user_id": user_id,
       "exp": datetime.utcnow() + timedelta(days=7),
       "iat": datetime.utcnow()
   }
   ```
2. **Token Storage**: Store JWT in `httpOnly` cookie (XSS protection) or `localStorage` with CSRF tokens
3. **Refresh Strategy**: Issue new token at 50% of expiration (3.5 days) for seamless UX
4. **Password Policy**: Minimum 6 characters (per clarification), email format validation

**Implementation Libraries**:
- Backend: `python-jose[cryptography]` for JWT, `passlib[bcrypt]` for hashing
- Frontend: Axios interceptors for automatic token injection

**Alternatives Considered**:
- OAuth2/Social Login: Rejected for MVP to reduce external dependencies
- Session-based auth: Rejected due to poor horizontal scalability
- Longer session (30 days): Rejected due to security concerns for financial data

---

## 2. API Design & Validation

### Decision: FastAPI with Pydantic Models

**Rationale**:
- **FastAPI**: Native async support, automatic OpenAPI generation, high performance (Starlette + Pydantic)
- **Pydantic**: Runtime type checking, data validation, serialization aligned with Python type hints
- **RESTful Conventions**: Standard HTTP methods (GET/POST/PUT/DELETE) for predictable API contracts

**Best Practices**:
1. **Router Organization**: Separate routers by domain (auth, users, watchlist, portfolio, stocks)
2. **Response Models**: Define explicit response schemas to control API surface
   ```python
   @router.get("/watchlist", response_model=List[WatchlistItemResponse])
   async def get_watchlist(current_user: User = Depends(get_current_user)):
       ...
   ```
3. **Error Handling**: Consistent error response format
   ```python
   {
       "detail": "Error message",
       "error_code": "DUPLICATE_STOCK",
       "timestamp": "2025-11-05T12:00:00Z"
   }
   ```
4. **API Versioning**: URL-based versioning (`/api/v1/`) for future compatibility

**Implementation Pattern**:
- Use dependency injection for database, auth, and services
- Middleware for CORS, logging, request ID tracking
- OpenAPI tags for logical grouping in documentation

**Alternatives Considered**:
- Django REST Framework: Rejected due to constitution mandate for FastAPI
- GraphQL: Rejected for MVP simplicity; REST sufficient for CRUD operations

---

## 3. Database Design & Cosmos DB

### Decision: Azure Cosmos DB NoSQL with Partition Strategy

**Rationale**:
- **NoSQL Suitability**: User data with simple relationships (1:N user-to-watchlist/portfolio). No complex joins needed.
- **Cosmos DB**: Serverless billing model, automatic scaling, global distribution capability, SLA guarantees
- **Partition Key Strategy**: Use `user_id` as partition key for all collections to co-locate user data

**Best Practices**:
1. **Container Design**:
   - `users` container: Partition key = `id` (user's email)
   - `watchlist_items` container: Partition key = `user_id`
   - `portfolio_entries` container: Partition key = `user_id`
   
2. **Indexing Policy**:
   ```json
   {
       "indexingMode": "consistent",
       "automatic": true,
       "includedPaths": [
           {"path": "/user_id/?"},
           {"path": "/symbol/?"},
           {"path": "/category/?"}
       ],
       "excludedPaths": [
           {"path": "/memo/?"},
           {"path": "/_etag/?"}
       ]
   }
   ```

3. **Query Patterns**:
   - All queries scoped to single partition (user_id) for cost efficiency
   - Avoid cross-partition queries
   - Use continuation tokens for pagination

4. **Schema Versioning**:
   - Include `schema_version` field in all documents
   - Document migrations in `docs/schema-migrations.md`

**Implementation Libraries**:
- `azure-cosmos` Python SDK (async support)
- Connection via managed identity (no connection strings in code)

**Alternatives Considered**:
- SQL Database: Rejected due to over-engineering for simple data model
- Table Storage: Rejected due to limited query capabilities
- MongoDB: Rejected to stay fully Azure-native

---

## 4. External API Integration (Alpha Vantage)

### Decision: Alpha Vantage with Caching & Rate Limit Handling

**Rationale**:
- **Alpha Vantage**: Free tier available, comprehensive stock data, simple REST API
- **1-Minute Cache TTL**: Balances fresh data with API quota conservation (per clarification)
- **Exponential Backoff**: Gracefully handles 429 rate limit errors

**Best Practices**:
1. **Cache Strategy**:
   ```python
   cache_key = f"stock:{symbol}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
   # Cache expires automatically after 1 minute
   ```
   - Use Azure Cache for Redis (serverless) or in-memory dict for MVP
   - Cache hit rate target: >80%

2. **Rate Limit Handling**:
   ```python
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       retry=retry_if_exception_type(RateLimitError)
   )
   async def fetch_stock_quote(symbol: str):
       ...
   ```

3. **Batch Requests**: Combine multiple stock queries when possible
4. **Fallback Strategy**: Return cached data with "stale" indicator if API unavailable

**Implementation Libraries**:
- `httpx` for async HTTP requests
- `tenacity` for retry logic
- `azure-redis` for distributed caching (optional for MVP)

**Alternatives Considered**:
- Yahoo Finance API: Deprecated, unreliable
- IEX Cloud: Paid only, no free tier
- Finnhub: More complex pricing model

---

## 5. Frontend Architecture (Vue 3)

### Decision: Composition API with Pinia State Management

**Rationale**:
- **Composition API**: Better TypeScript support, improved code reuse via composables
- **Pinia**: Official Vue state management, simpler than Vuex, TypeScript-first
- **Tabler UI**: Pre-built components reduce development time, consistent design

**Best Practices**:
1. **Store Organization**:
   ```typescript
   // stores/auth.ts
   export const useAuthStore = defineStore('auth', () => {
       const user = ref<User | null>(null)
       const token = ref<string | null>(null)
       
       async function login(email: string, password: string) { ... }
       async function logout() { ... }
       
       return { user, token, login, logout }
   })
   ```

2. **Component Structure**:
   - Smart containers (views/) manage state and API calls
   - Dumb components (components/) receive props and emit events
   - Composables (composables/) for reusable logic (useStockData, useDarkMode)

3. **Type Safety**:
   - Define TypeScript interfaces for all API responses
   - Use `<script setup lang="ts">` for type checking

4. **Drag & Drop**: Use `vue-draggable` (SortableJS wrapper) for watchlist reordering

**Implementation Libraries**:
- `@tabler/icons-vue` for icons
- `vue-echarts` for heatmap visualization
- `vee-validate` + `yup` for form validation
- `axios` for HTTP client

**Alternatives Considered**:
- Options API: Rejected in favor of Composition API (constitution preference)
- Vuex: Replaced by Pinia per Vue 3 best practices
- Custom UI components: Rejected to leverage Tabler's mature component library

---

## 6. Infrastructure as Code (Azure Bicep)

### Decision: Modular Bicep Templates with Parameterization

**Rationale**:
- **Bicep**: Native Azure IaC, simpler than ARM JSON, strong tooling support
- **Modular Design**: Separate templates for each resource type (database, backend, frontend, monitoring)
- **Environment Parameterization**: Same templates for dev/staging/prod with different parameter files

**Best Practices**:
1. **Template Structure**:
   ```
   infrastructure/bicep/
   ├── main.bicep           # Orchestration template
   ├── parameters/
   │   ├── dev.json
   │   ├── staging.json
   │   └── prod.json
   └── modules/
       ├── cosmos-db.bicep
       ├── container-apps.bicep
       ├── static-web-app.bicep
       └── monitoring.bicep
   ```

2. **Resource Naming Convention**:
   ```bicep
   var resourcePrefix = 'mystock3-${environment}-${location}'
   var cosmosDbName = '${resourcePrefix}-cosmos'
   ```

3. **Managed Identities**: Use system-assigned managed identities for secure resource access (no connection strings)

4. **Tagging Strategy**:
   ```bicep
   tags: {
       Environment: environment
       Project: 'MyStock3'
       ManagedBy: 'IaC-Bicep'
       CostCenter: 'MVP'
   }
   ```

**Implementation Pattern**:
- Deploy via GitHub Actions workflow
- Use `az deployment group create` with parameter files
- Store secrets in Key Vault, reference in Bicep
- Include Cosmos DB schema creation in post-deployment scripts

**Alternatives Considered**:
- Terraform: Rejected to stay Azure-native (constitution mandate)
- ARM JSON: Rejected in favor of more readable Bicep
- Manual Azure Portal: Prohibited by constitution

---

## 7. CI/CD & Deployment Strategy

### Decision: GitHub Actions with Multi-Stage Pipelines

**Rationale**:
- **GitHub Actions**: Native Git integration, free for public repos, rich ecosystem
- **Multi-Stage**: Separate pipelines for backend, frontend, infrastructure
- **Environment Protection**: Manual approval gates for production

**Best Practices**:
1. **Pipeline Structure**:
   ```yaml
   # .github/workflows/backend-ci.yml
   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run ruff
           run: ruff check backend/
     
     test:
       needs: lint
       runs-on: ubuntu-latest
       steps:
         - name: Run pytest
           run: pytest --cov=backend --cov-report=xml
         - name: Check coverage
           run: coverage report --fail-under=70
     
     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - name: Build Docker image
           run: docker build -t mystock3-backend:${{ github.sha }} backend/
         - name: Push to ACR
           run: docker push ...
     
     deploy:
       needs: build
       runs-on: ubuntu-latest
       environment: production
       steps:
         - name: Deploy to Container Apps
           run: az containerapp update ...
   ```

2. **Secret Management**:
   - Store secrets in GitHub Secrets
   - Use Azure Key Vault for runtime secrets
   - Rotate credentials quarterly

3. **Deployment Order**:
   1. Infrastructure (Bicep)
   2. Database schema migrations
   3. Backend (Container Apps)
   4. Frontend (Static Web Apps)
   5. Smoke tests

**Implementation Libraries**:
- `actions/checkout@v3`
- `actions/setup-python@v4`
- `azure/login@v1`
- `docker/build-push-action@v4`

**Alternatives Considered**:
- Azure DevOps: Rejected for GitHub-native workflow
- Manual deployment: Prohibited by constitution
- Single monolithic pipeline: Rejected for better failure isolation

---

## 8. Observability & Monitoring

### Decision: Azure Log Analytics + Application Insights

**Rationale**:
- **Log Analytics**: Centralized log aggregation, powerful KQL query language
- **Application Insights**: APM for performance monitoring, exception tracking, dependency telemetry
- **Structured Logging**: JSON format for easy parsing and correlation

**Best Practices**:
1. **Logging Strategy**:
   ```python
   import structlog
   
   logger = structlog.get_logger()
   logger.info(
       "stock_data_fetched",
       symbol=symbol,
       cache_hit=cache_hit,
       latency_ms=latency,
       user_id=user_id
   )
   ```

2. **Log Levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General application flow
   - WARNING: Recoverable errors (rate limits, cache misses)
   - ERROR: Unrecoverable errors requiring attention
   - CRITICAL: System-level failures

3. **Metrics to Track**:
   - API response times (p50, p95, p99)
   - Error rates by endpoint
   - Cache hit rates
   - Alpha Vantage API quota usage
   - Active user sessions
   - Database query latencies

4. **Alerting Rules**:
   - API error rate >5% for 5 minutes
   - P95 latency >500ms
   - Alpha Vantage API quota >80%
   - Database throttling events

**Implementation Libraries**:
- `opencensus-ext-azure` for Application Insights
- `structlog` for structured logging
- `prometheus-client` for custom metrics (optional)

**Alternatives Considered**:
- ELK Stack: Over-engineering for MVP, higher operational overhead
- CloudWatch: Not Azure-native
- Manual log files: Insufficient for production observability

---

## 9. Testing Strategy

### Decision: Pytest (Unit/Integration) + Playwright (E2E)

**Rationale**:
- **pytest**: Python standard, rich plugin ecosystem, fixture-based testing
- **Playwright**: Cross-browser E2E testing, auto-wait, powerful selectors
- **70% Coverage**: Constitution mandate, enforced in CI pipeline

**Best Practices**:
1. **Test Organization**:
   ```
   backend/tests/
   ├── unit/
   │   ├── test_auth_service.py     # Mock external dependencies
   │   ├── test_stock_service.py    # Mock Alpha Vantage API
   │   └── test_cache_service.py
   ├── integration/
   │   ├── test_api_auth.py         # Real database (test container)
   │   ├── test_api_watchlist.py
   │   └── test_api_portfolio.py
   └── contract/
       └── test_openapi_spec.py     # Validate API matches OpenAPI schema
   
   frontend/tests/
   └── e2e/
       ├── auth.spec.ts             # Playwright E2E tests
       ├── watchlist.spec.ts
       └── portfolio.spec.ts
   ```

2. **Fixture Strategy**:
   ```python
   @pytest.fixture
   async def test_user(db_client):
       user = await create_test_user(email="test@example.com")
       yield user
       await cleanup_test_user(user.id)
   
   @pytest.fixture
   def mock_alpha_vantage():
       with patch('services.stock_service.httpx.get') as mock:
           mock.return_value.json.return_value = MOCK_STOCK_DATA
           yield mock
   ```

3. **Test Naming Convention**:
   - `test_<function>_<scenario>_<expected_result>`
   - Example: `test_login_invalid_password_returns_401`

4. **Playwright Best Practices**:
   - Use `data-testid` attributes for stable selectors
   - Test user journeys, not individual components
   - Run tests in CI against deployed staging environment

**Implementation Libraries**:
- `pytest-asyncio` for async test support
- `pytest-cov` for coverage reporting
- `pytest-mock` for mocking
- `httpx-mock` for mocking HTTP requests
- `@playwright/test` for E2E testing

**Alternatives Considered**:
- unittest: Rejected in favor of pytest's cleaner syntax
- Selenium: Replaced by Playwright for better reliability
- Cypress: Rejected in favor of Playwright (constitution mandate)

---

## 10. Dark Mode Implementation

### Decision: CSS Variables with Pinia State Persistence

**Rationale**:
- **CSS Variables**: Modern browser support, easy theme switching without component re-renders
- **Pinia Persistence**: Store preference in localStorage for consistency across sessions
- **Tabler Support**: Built-in dark mode styles

**Best Practices**:
1. **Theme Store**:
   ```typescript
   export const useThemeStore = defineStore('theme', () => {
       const isDark = ref(localStorage.getItem('darkMode') === 'true')
       
       function toggleDarkMode() {
           isDark.value = !isDark.value
           localStorage.setItem('darkMode', String(isDark.value))
           document.documentElement.classList.toggle('dark', isDark.value)
       }
       
       return { isDark, toggleDarkMode }
   })
   ```

2. **CSS Structure**:
   ```css
   :root {
       --color-bg: #ffffff;
       --color-text: #000000;
       --color-primary: #0066cc;
   }
   
   :root.dark {
       --color-bg: #1a1a1a;
       --color-text: #ffffff;
       --color-primary: #3399ff;
   }
   ```

3. **Initial Load**: Apply theme class before Vue mounts to prevent flash

**Implementation Pattern**:
- Respect system preference on first visit (`prefers-color-scheme` media query)
- Override with user selection thereafter
- Sync preference to backend user settings (optional for MVP)

**Alternatives Considered**:
- Separate CSS files: Rejected due to increased bundle size
- Component-level theming: Rejected for complexity

---

## Summary of Key Decisions

| Decision Area | Technology | Rationale |
|---------------|------------|-----------|
| **Backend** | Python 3.11 + FastAPI | Constitution mandate, async support, OpenAPI generation |
| **Frontend** | Vue 3 (Composition API) | Constitution mandate, TypeScript support, modern patterns |
| **Database** | Azure Cosmos DB NoSQL | Serverless billing, simple data model, partition strategy |
| **Auth** | JWT + bcrypt | Stateless, horizontally scalable, secure password hashing |
| **External API** | Alpha Vantage | Free tier, comprehensive data, simple REST interface |
| **Caching** | 1-minute TTL | Balance freshness with API quota (clarified requirement) |
| **State Management** | Pinia | Vue 3 official, TypeScript-first, simpler than Vuex |
| **UI Framework** | Tabler + ECharts | Pre-built components, charting library |
| **IaC** | Azure Bicep | Native Azure, simpler than ARM, constitution mandate |
| **CI/CD** | GitHub Actions | Native Git integration, multi-stage pipelines |
| **Observability** | Log Analytics + App Insights | Centralized logging, APM, KQL queries |
| **Testing** | pytest + Playwright | Unit/integration/E2E coverage, 70% mandate |

---

## Risk Mitigation

1. **Alpha Vantage Rate Limits**:
   - **Risk**: API quota exhaustion blocks all users
   - **Mitigation**: 1-minute cache, exponential backoff, quota monitoring alerts

2. **Cold Start Latency**:
   - **Risk**: First request after idle period has high latency
   - **Mitigation**: Container Apps min instances = 1, pre-warm connections

3. **Cosmos DB Costs**:
   - **Risk**: Unpredictable costs from inefficient queries
   - **Mitigation**: Single-partition queries, indexing policy, serverless mode for MVP

4. **Session Hijacking**:
   - **Risk**: JWT token theft
   - **Mitigation**: httpOnly cookies, HTTPS only, short expiration (7 days)

5. **Test Coverage Enforcement**:
   - **Risk**: Developers bypass 70% requirement
   - **Mitigation**: CI pipeline fails if coverage <70%, pre-commit hooks

---

## Next Steps

With all technology decisions finalized and research complete, proceed to:
1. **Phase 1**: Generate `data-model.md` with detailed entity schemas
2. **Phase 1**: Create OpenAPI contracts in `/contracts/`
3. **Phase 1**: Write `quickstart.md` for local development setup
4. **Phase 1**: Update agent context with technology stack
5. **Phase 2**: Generate task breakdown in `tasks.md`

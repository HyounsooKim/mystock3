# MyStock Frontend

Vue 3 + TypeScript frontend for MyStock stock portfolio management application.

## Tech Stack

- **Framework**: Vue 3 with Composition API
- **Build Tool**: Vite 5.x
- **Language**: TypeScript 5.x
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **UI Components**: Tabler (custom theme)
- **Charts**: ECharts 5.x
- **HTTP Client**: Axios
- **Testing**: Playwright (E2E)
- **Code Quality**: ESLint + Prettier

## Project Structure

```
frontend/
├── src/
│   ├── api/                 # API clients
│   │   ├── client.ts        # Axios instance with JWT interceptor
│   │   └── stocks.ts        # Stocks API endpoints
│   ├── assets/              # Static assets
│   │   └── styles/
│   │       ├── main.css     # Global styles
│   │       └── theme.scss   # Tabler theme config
│   ├── components/          # Vue components
│   │   ├── auth/
│   │   ├── stocks/
│   │   ├── watchlist/
│   │   └── portfolio/
│   ├── layouts/             # Layout components
│   │   └── BaseLayout.vue   # Main layout with navigation
│   ├── router/              # Vue Router config
│   │   └── index.ts
│   ├── stores/              # Pinia stores
│   │   ├── auth.ts          # Authentication state
│   │   ├── theme.ts         # Dark mode state
│   │   ├── watchlist.ts     # Watchlist state
│   │   └── portfolio.ts     # Portfolio state
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Utility functions
│   │   └── errorHandler.ts # Error handling
│   ├── views/               # Page components
│   │   ├── LoginView.vue
│   │   ├── SignupView.vue
│   │   ├── DashboardView.vue
│   │   ├── WatchlistView.vue
│   │   └── PortfolioView.vue
│   ├── App.vue              # Root component
│   ├── main.ts              # App entry point
│   └── vite-env.d.ts        # Vite environment types
├── tests/
│   └── e2e/                 # Playwright E2E tests
│       ├── helpers/
│       │   └── auth.ts      # Auth test utilities
│       └── auth/
├── public/                  # Public assets
├── index.html               # HTML entry point
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── package.json
├── playwright.config.ts
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## Getting Started

### Prerequisites

- Node.js 20.x+
- npm 10.x+

### Installation

```powershell
# Navigate to frontend directory
cd mystock3/frontend

# Install dependencies
npm install
```

### Environment Configuration

Copy `.env.example` to `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=MyStock
VITE_APP_VERSION=1.0.0
```

### Running the Development Server

```powershell
# Start dev server
npm run dev

# Server will be available at http://localhost:5173
```

### Building for Production

```powershell
# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

### Code Quality

```powershell
# Lint with ESLint
npm run lint

# Format with Prettier
npm run format

# Type check
npm run type-check
```

### Testing

```powershell
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run E2E tests in specific browser
npx playwright test --project=chromium
```

## Features

### Authentication

- User signup with email/password
- Login with JWT token
- Persistent sessions (7 days)
- Protected routes with route guards
- Automatic token refresh

### Dark Mode

- Toggle between light/dark themes
- Persistent preference in localStorage
- Smooth theme transitions
- All components support both themes

### Watchlist Management

- Search and add stocks
- Add personal memos (max 50 chars)
- Drag-and-drop reordering
- Real-time price updates
- Delete stocks from watchlist

### Portfolio Management

- Track stock holdings by category (장기/단기/정찰병)
- Record purchase price and quantity
- Calculate profit/loss with color coding
- Heatmap visualization
- Edit/delete portfolio entries
- 10 stock limit per category

### Stock Data

- Real-time stock quotes
- Historical price charts (ECharts)
- Search stocks by symbol/name
- Price change indicators

## Component Usage

### BaseLayout

Wrap pages with BaseLayout for consistent navigation:

```vue
<template>
  <BaseLayout>
    <h1>Page Content</h1>
  </BaseLayout>
</template>

<script setup lang="ts">
import BaseLayout from '@/layouts/BaseLayout.vue'
</script>
```

### Auth Store

```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Login
await authStore.login(email, password)

// Signup
await authStore.signup(email, password)

// Logout
await authStore.logout()

// Check auth status
if (authStore.isAuthenticated) {
  console.log('User:', authStore.user)
}
```

### API Client

```typescript
import apiClient from '@/api/client'

// GET request (auto-includes JWT token)
const response = await apiClient.get('/stocks/AAPL/quote')

// POST request
const response = await apiClient.post('/watchlist', {
  symbol: 'AAPL',
  memo: 'Good buy'
})
```

## Routing

### Route Guards

Protected routes automatically redirect to login if not authenticated:

```typescript
{
  path: '/dashboard',
  component: DashboardView,
  meta: { requiresAuth: true }
}
```

### Navigation

```vue
<template>
  <!-- Declarative navigation -->
  <router-link to="/dashboard">Dashboard</router-link>
  
  <!-- Programmatic navigation -->
  <button @click="goToDashboard">Go</button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goToDashboard() {
  router.push('/dashboard')
}
</script>
```

## Styling

### Tabler Theme

Theme colors are defined in `src/styles/theme.scss`:

```scss
// Use CSS variables
<style scoped>
.card {
  background-color: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
</style>
```

### Utility Classes

```vue
<template>
  <div class="profit">+5.23%</div>  <!-- Green -->
  <div class="loss">-2.15%</div>    <!-- Red -->
</template>
```

## API Integration

### Error Handling

```typescript
import { handleApiError } from '@/utils/errorHandler'

try {
  await apiClient.post('/watchlist', data)
} catch (error) {
  handleApiError(error) // Shows user-friendly notification
}
```

### TypeScript Types

```typescript
import type { User, StockQuote, WatchlistItem } from '@/types'

const user: User = {
  user_id: 'user_123',
  email: 'user@example.com',
  created_at: '2025-01-01T00:00:00Z',
  is_active: true
}
```

## Performance

- Lazy loading for routes
- Component code splitting
- Optimized bundle size with tree shaking
- ECharts on-demand loading
- Image optimization

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Troubleshooting

### Common Issues

**Port 5173 already in use**
- Solution: Stop other Vite servers or use `npm run dev -- --port 3000`

**API requests fail with CORS error**
- Solution: Ensure backend CORS configured for http://localhost:5173

**Dark mode not persisting**
- Solution: Check browser localStorage permissions

**Router navigation not working**
- Solution: Verify Vue Router installed and configured

## Contributing

1. Create feature branch
2. Follow Vue 3 Composition API style
3. Use TypeScript for all new code
4. Add E2E tests for user flows
5. Run linting before commit
6. Update documentation

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Playwright Documentation](https://playwright.dev/)
- [ECharts Documentation](https://echarts.apache.org/)

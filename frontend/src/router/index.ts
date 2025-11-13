import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// Route-level code splitting with named chunks (T173)
// Each route generates a separate chunk: [name].[hash].js
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import(/* webpackChunkName: "auth" */ '../views/LoginView.vue')
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import(/* webpackChunkName: "auth" */ '../views/SignupView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import(/* webpackChunkName: "dashboard" */ '../views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import(/* webpackChunkName: "watchlist" */ '../views/WatchlistView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import(/* webpackChunkName: "portfolio" */ '../views/PortfolioView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('auth_token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/signup') && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

<template>
  <div class="base-layout">
    <header class="app-header">
      <div class="header-container">
        <div class="header-left">
          <button v-if="isAuthenticated" @click="toggleMobileMenu" class="navbar-toggler">
            <span class="navbar-toggler-icon"></span>
          </button>
          
          <div class="logo">
            <h1>MyStock</h1>
          </div>
          
          <nav v-if="isAuthenticated" class="nav-menu" :class="{ 'show': showMobileMenu }">
          <router-link to="/dashboard" :class="{ active: isActive('/dashboard') }" @click="closeMobileMenu">
            <span class="nav-link-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <path d="M5 12l-2 0l9 -9l9 9l-2 0"></path>
                <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-7"></path>
                <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v6"></path>
              </svg>
            </span>
            <span class="nav-link-title">대시보드</span>
          </router-link>
          <router-link to="/watchlist" :class="{ active: isActive('/watchlist') }" @click="closeMobileMenu">
            <span class="nav-link-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <path d="M9 11l3 3l8 -8"></path>
                <path d="M20 12v6a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h9"></path>
              </svg>
            </span>
            <span class="nav-link-title">관심종목</span>
          </router-link>
          <router-link to="/portfolio" :class="{ active: isActive('/portfolio') }" @click="closeMobileMenu">
            <span class="nav-link-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <path d="M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2"></path>
                <path d="M9 3m0 2a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2v0a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2z"></path>
                <path d="M9 12l2 2l4 -4"></path>
              </svg>
            </span>
            <span class="nav-link-title">포트폴리오</span>
          </router-link>
        </nav>
        </div>
        
        <div class="header-actions">
          <button @click="toggleTheme" class="theme-toggle" title="테마 전환">
            <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
              <path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z"></path>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
              <path d="M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0 -8 0"></path>
              <path d="M3 12h1m8 -9v1m8 8h1m-9 8v1m-6.4 -15.4l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7"></path>
            </svg>
          </button>
          
          <div v-if="isAuthenticated" class="user-info">
            <span class="user-email">{{ userEmail }}</span>
            <button @click="handleLogout" class="btn-logout">로그아웃</button>
          </div>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const userEmail = computed(() => authStore.user?.email || '')
const isDark = computed(() => themeStore.isDark)

const showMobileMenu = ref(false)

function isActive(path: string): boolean {
  return route.path === path
}

function toggleTheme() {
  themeStore.toggleDarkMode()
}

function toggleMobileMenu() {
  showMobileMenu.value = !showMobileMenu.value
}

function closeMobileMenu() {
  showMobileMenu.value = false
}

async function handleLogout() {
  if (confirm('로그아웃 하시겠습니까?')) {
    await authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.base-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-header {
  background-color: var(--color-primary);
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

/* 다크모드에서도 헤더 색상 유지 */
.theme-dark .app-header {
  background-color: var(--color-primary);
  color: white;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo h1 {
  margin: 0;
  font-size: 1.5rem;
  color: white;
  padding: 1rem 0;
}

/* 다크모드에서도 로고 색상 유지 */
.theme-dark .logo h1 {
  color: white;
}

.nav-menu {
  display: flex;
  gap: 0;
  align-items: stretch;
}

.nav-menu a {
  color: white;
  text-decoration: none;
  padding: 1rem 1.5rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  border-bottom: 2px solid transparent;
}

.nav-link-icon {
  display: inline-flex;
  align-items: center;
}

.nav-link-title {
  display: inline;
}

.nav-menu a:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.nav-menu a.active {
  background-color: rgba(255, 255, 255, 0.1);
  font-weight: 600;
  border-bottom-color: white;
  border-bottom-width: 3px;
}

/* 다크모드에서도 메뉴 스타일 유지 */
.theme-dark .nav-menu a {
  color: white;
}

.theme-dark .nav-menu a:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.theme-dark .nav-menu a.active {
  background-color: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
}

.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
  display: inline-flex;
  align-items: center;
  color: white;
}

.theme-dark .theme-toggle {
  color: white;
}

.theme-toggle:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.theme-dark .theme-toggle:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-email {
  color: white;
  font-size: 0.9rem;
}

/* 다크모드에서도 사용자 정보 색상 유지 */
.theme-dark .user-email {
  color: white;
}

.btn-logout {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.theme-dark .btn-logout {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-logout:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.app-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem;
}

@media (max-width: 768px) {
  .header-container {
    padding: 0 1rem;
    position: relative;
  }

  .header-left {
    flex: 1;
    justify-content: flex-start;
    gap: 1rem;
  }
  
  .navbar-toggler {
    display: flex !important;
    order: -1;
  }
  
  .logo {
    order: 0;
  }
  
  .nav-menu {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: var(--color-primary);
    flex-direction: column;
    padding: 0.5rem 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 1000;
  }
  
  .nav-menu.show {
    display: flex !important;
  }
  
  .nav-menu a {
    padding: 0.75rem 1.5rem;
    border-bottom: none;
    border-left: 3px solid transparent;
  }
  
  .nav-menu a.active {
    border-bottom: none;
    border-left-color: white;
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .header-actions {
    gap: 0.5rem;
  }
  
  .user-email {
    display: none;
  }
  
  .btn-logout {
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
  }

  .app-main {
    padding: 1rem;
  }
}

/* Hamburger icon */
.navbar-toggler {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  color: white;
  align-items: center;
  justify-content: center;
}

.theme-dark .navbar-toggler {
  color: white;
}

.navbar-toggler-icon {
  display: block;
  width: 24px;
  height: 2px;
  background-color: currentColor;
  position: relative;
  transition: background-color 0.2s;
}

.navbar-toggler-icon::before,
.navbar-toggler-icon::after {
  content: '';
  display: block;
  width: 24px;
  height: 2px;
  background-color: currentColor;
  position: absolute;
  left: 0;
  transition: transform 0.2s;
}

.navbar-toggler-icon::before {
  top: -8px;
}

.navbar-toggler-icon::after {
  top: 8px;
}
</style>

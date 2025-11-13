<template>
  <div id="app" :class="{ 'theme-dark': isDark }">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
const isDark = computed(() => themeStore.isDark)
</script>

<style scoped>
#app {
  min-height: 100vh;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.theme-dark {
  background-color: #1a1a1a;
  color: #ffffff;
}
</style>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1>MyStock 로그인</h1>
      <form @submit.prevent="handleLogin">
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        <div class="form-group">
          <label for="email">이메일</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="이메일을 입력하세요"
          />
        </div>
        <div class="form-group">
          <label for="password">비밀번호</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="비밀번호를 입력하세요"
          />
        </div>
        <button type="submit" class="btn-primary" :disabled="isLoading">
          {{ isLoading ? '로그인 중...' : '로그인' }}
        </button>
        <p class="signup-link">
          계정이 없으신가요? <router-link to="/signup">회원가입</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true
  
  try {
    await authStore.login(email.value, password.value)
    router.push('/dashboard')
  } catch (error: any) {
    errorMessage.value = error.message || '로그인에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--color-bg);
}

.login-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.theme-dark .login-card {
  background: #2d2d2d;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: var(--color-text);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 1rem;
  background-color: var(--color-bg);
  color: var(--color-text);
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
}

.signup-link {
  text-align: center;
  margin-top: 1rem;
  color: var(--color-text);
}

.signup-link a {
  color: var(--color-primary);
  text-decoration: none;
}

.signup-link a:hover {
  text-decoration: underline;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border: 1px solid #f5c6cb;
}

.theme-dark .error-message {
  background-color: #5a1f1f;
  color: #f8d7da;
  border-color: #8b3a3a;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

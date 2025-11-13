<template>
  <div v-if="show" class="alert alert-warning alert-dismissible fade show" role="alert">
    <div class="d-flex align-items-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="icon alert-icon me-2" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
        <path d="M12 9v4" />
        <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z" />
        <path d="M12 16h.01" />
      </svg>
      <div>
        <h4 class="alert-title">API 한도 초과</h4>
        <div class="text-muted">
          {{ message }}
        </div>
      </div>
    </div>
    <button 
      type="button" 
      class="btn-close" 
      @click="dismiss"
      aria-label="Close"
    ></button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

interface Props {
  show?: boolean
  message?: string
  autoDismiss?: boolean
  dismissDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  message: '주식 데이터 API 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.',
  autoDismiss: true,
  dismissDelay: 10000, // 10 seconds
})

const emit = defineEmits<{
  (e: 'dismiss'): void
}>()

const show = ref(props.show)
let dismissTimer: ReturnType<typeof setTimeout> | null = null

watch(() => props.show, (newValue) => {
  show.value = newValue
  
  if (newValue && props.autoDismiss) {
    startDismissTimer()
  }
})

onMounted(() => {
  if (show.value && props.autoDismiss) {
    startDismissTimer()
  }
})

function startDismissTimer() {
  if (dismissTimer) {
    clearTimeout(dismissTimer)
  }
  
  dismissTimer = setTimeout(() => {
    dismiss()
  }, props.dismissDelay)
}

function dismiss() {
  show.value = false
  if (dismissTimer) {
    clearTimeout(dismissTimer)
    dismissTimer = null
  }
  emit('dismiss')
}
</script>

<style scoped>
.alert {
  margin-bottom: 1rem;
}

.alert-icon {
  flex-shrink: 0;
}

.alert-title {
  margin-bottom: 0.25rem;
  font-size: 1rem;
  font-weight: 600;
}

.btn-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
}
</style>

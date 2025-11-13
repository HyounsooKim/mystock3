<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-lg" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
        <path d="M3 3m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />
        <path d="M3 15m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />
        <path d="M15 15m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />
        <path d="M15 3m0 1a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1z" />
      </svg>
    </div>
    <h3 class="empty-state-title">포트폴리오가 비어 있습니다</h3>
    <p class="empty-state-subtitle text-muted">
      보유 종목을 추가하여 수익률을 추적하세요.
    </p>
    <div class="empty-state-action">
      <button class="btn btn-primary" @click="onAddClick">
        <svg xmlns="http://www.w3.org/2000/svg" class="icon me-1" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
          <path d="M12 5l0 14" />
          <path d="M5 12l14 0" />
        </svg>
        종목 추가
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  (e: 'add-click'): void
}>()

function onAddClick() {
  emit('add-click')
}
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  min-height: 400px;
}

.empty-state-icon {
  margin-bottom: 1.5rem;
}

.empty-state-icon .icon {
  width: 4rem;
  height: 4rem;
  color: var(--tblr-muted);
  stroke-width: 1.5;
}

.empty-state-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--tblr-body-color);
}

.empty-state-subtitle {
  font-size: 0.9375rem;
  margin-bottom: 1.5rem;
  max-width: 400px;
}

.empty-state-action {
  margin-top: 0.5rem;
}
</style>

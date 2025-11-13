<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-lg" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
        <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
        <path d="M9 10l.01 0" />
        <path d="M15 10l.01 0" />
        <path d="M9.5 15a3.5 3.5 0 0 0 5 0" />
      </svg>
    </div>
    <h3 class="empty-state-title">관심종목이 없습니다</h3>
    <p class="empty-state-subtitle text-muted">
      주식을 추가하여 관심종목을 관리하세요.
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

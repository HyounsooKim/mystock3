<template>
  <div class="category-selector">
    <div class="btn-group" role="group">
      <button
        type="button"
        class="btn"
        :class="{ 'btn-primary': selectedCategory === 'all', 'btn-outline-primary': selectedCategory !== 'all' }"
        @click="selectCategory('all')"
      >
        전체
      </button>
      <button
        type="button"
        class="btn"
        :class="{ 'btn-primary': selectedCategory === '장기', 'btn-outline-primary': selectedCategory !== '장기' }"
        @click="selectCategory('장기')"
      >
        장기
      </button>
      <button
        type="button"
        class="btn"
        :class="{ 'btn-primary': selectedCategory === '단기', 'btn-outline-primary': selectedCategory !== '단기' }"
        @click="selectCategory('단기')"
      >
        단기
      </button>
      <button
        type="button"
        class="btn"
        :class="{ 'btn-primary': selectedCategory === '정찰병', 'btn-outline-primary': selectedCategory !== '정찰병' }"
        @click="selectCategory('정찰병')"
      >
        정찰병
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioCategory } from '@/types'

interface Props {
  modelValue: PortfolioCategory | 'all'
}

interface Emits {
  (e: 'update:modelValue', value: PortfolioCategory | 'all'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const selectedCategory = computed(() => props.modelValue)

function selectCategory(category: PortfolioCategory | 'all') {
  emit('update:modelValue', category)
}
</script>

<style scoped>
.category-selector {
  margin-bottom: 1rem;
}

.btn-group {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--tblr-primary);
  color: white;
  border: 1px solid var(--tblr-primary);
}

.btn-outline-primary {
  background-color: transparent;
  color: var(--tblr-primary);
  border: 1px solid var(--tblr-primary);
}

.btn-outline-primary:hover {
  background-color: var(--tblr-primary);
  color: white;
}
</style>

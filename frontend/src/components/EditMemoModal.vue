<template>
  <div v-if="isOpen" class="modal fade show" style="display: block" @click="handleBackdropClick">
    <div class="modal-dialog modal-dialog-centered" @click.stop>
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">메모 수정</h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label">종목</label>
            <div class="form-control-plaintext">
              <strong>{{ item.symbol }}</strong> - {{ item.company_name }}
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">메모</label>
            <input
              v-model="memo"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': memoError }"
              placeholder="메모를 입력하세요"
              maxlength="50"
            />
            <div v-if="memoError" class="invalid-feedback">{{ memoError }}</div>
            <div class="form-text">{{ memo.length }}/50자</div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="close">
            취소
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="loading || !!memoError"
            @click="handleSubmit"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            저장
          </button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="isOpen" class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import type { WatchlistItemWithQuote } from '@/types'

interface Props {
  isOpen: boolean
  item: WatchlistItemWithQuote
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  success: []
}>()

const watchlistStore = useWatchlistStore()

const memo = ref('')
const loading = ref(false)

const memoError = computed(() => {
  if (memo.value.length > 50) {
    return '메모는 최대 50자까지 입력 가능합니다'
  }
  return null
})

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    memo.value = props.item.memo
  }
})

async function handleSubmit() {
  if (loading.value || memoError.value) return

  loading.value = true
  try {
    await watchlistStore.updateWatchlistItem(props.item.id, {
      memo: memo.value
    })
    emit('success')
    close()
  } catch (err) {
    // Error handled by store
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}

function handleBackdropClick() {
  close()
}
</script>

<style scoped>
.modal {
  background: rgba(0, 0, 0, 0.5);
}
</style>

<template>
  <div v-if="isOpen" class="modal fade show" style="display: block" @click="handleBackdropClick">
    <div class="modal-dialog modal-dialog-centered modal-sm" @click.stop>
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">종목 삭제</h5>
          <button type="button" class="btn-close" @click="cancel"></button>
        </div>
        <div class="modal-body">
          <p>
            <strong>{{ itemSymbol }}</strong> 종목을 관심종목에서 삭제하시겠습니까?
          </p>
          <p class="text-muted mb-0">이 작업은 되돌릴 수 없습니다.</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="cancel" :disabled="loading">
            취소
          </button>
          <button
            type="button"
            class="btn btn-danger"
            :disabled="loading"
            @click="confirm"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            삭제
          </button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="isOpen" class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
interface Props {
  isOpen: boolean
  itemSymbol: string
  loading: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

function confirm() {
  emit('confirm')
}

function cancel() {
  emit('cancel')
}

function handleBackdropClick() {
  if (!props.loading) {
    cancel()
  }
}
</script>

<style scoped>
.modal {
  background: rgba(0, 0, 0, 0.5);
}
</style>

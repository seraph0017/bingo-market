<template>
  <div class="settlements-page">
    <div class="settlements-header">
      <h1>{{ t('settlements.title') }}</h1>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        :class="['tab', activeTab === 'pending' ? 'active' : '']"
        @click="activeTab = 'pending'"
      >
        {{ t('settlements.pending') }}
      </button>
      <button
        :class="['tab', activeTab === 'completed' ? 'active' : '']"
        @click="activeTab = 'completed'"
      >
        {{ t('settlements.completed') }}
      </button>
      <button
        :class="['tab', activeTab === 'disputes' ? 'active' : '']"
        @click="activeTab = 'disputes'"
      >
        {{ t('settlements.disputes') }}
      </button>
    </div>

    <!-- Pending Settlements -->
    <div v-if="activeTab === 'pending'" class="tab-content">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="pendingSettlements.length === 0" class="empty-state">
        {{ t('settlements.noPending') }}
      </div>
      <div v-else class="settlements-list">
        <div
          v-for="settlement in pendingSettlements"
          :key="settlement.id"
          class="settlement-card"
        >
          <div class="settlement-header">
            <h3 class="market-title">{{ settlement.market_title }}</h3>
            <span class="expires-tag">{{ t('settlements.expiresIn') }}: {{ formatRelativeTime(settlement.expires_at) }}</span>
          </div>
          <p class="market-description">{{ settlement.description }}</p>

          <div class="settlement-info">
            <div class="info-item">
              <span class="label">{{ t('settlements.myPositions') }}</span>
              <span class="value">{{ settlement.my_positions }} {{ t('common.coins') }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ t('settlements.totalPool') }}</span>
              <span class="value">{{ formatNumber(settlement.total_pool) }} {{ t('common.coins') }}</span>
            </div>
          </div>

          <div class="settlement-actions">
            <button class="btn-secondary" @click="viewDetails(settlement.id)">
              {{ t('common.viewDetails') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Completed Settlements -->
    <div v-if="activeTab === 'completed'" class="tab-content">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="completedSettlements.length === 0" class="empty-state">
        {{ t('settlements.noCompleted') }}
      </div>
      <div v-else class="settlements-list">
        <div
          v-for="settlement in completedSettlements"
          :key="settlement.id"
          class="settlement-card"
        >
          <div class="settlement-header">
            <h3 class="market-title">{{ settlement.market_title }}</h3>
            <span :class="['result-tag', settlement.user_won ? 'win' : 'lose']">
              {{ settlement.user_won ? t('settlements.won') : t('settlements.lost') }}
            </span>
          </div>
          <p class="market-description">{{ settlement.description }}</p>

          <div class="settlement-result">
            <div class="result-info">
              <span class="result-label">{{ t('settlements.winningOutcome') }}:</span>
              <span class="result-value">{{ settlement.winning_outcome }}</span>
            </div>
            <div class="payout-info">
              <span class="payout-label">{{ t('settlements.payout') }}:</span>
              <span :class="['payout-value', settlement.user_won ? 'win' : 'lose']">
                {{ settlement.user_won ? '+' : '-' }}{{ formatNumber(settlement.payout) }} {{ t('common.coins') }}
              </span>
            </div>
          </div>

          <div class="settlement-actions">
            <button class="btn-secondary" @click="viewDetails(settlement.id)">
              {{ t('common.viewDetails') }}
            </button>
            <button
              v-if="settlement.can_dispute"
              class="btn-dispute"
              @click="openDisputeForm(settlement)"
            >
              {{ t('settlements.dispute') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Disputes -->
    <div v-if="activeTab === 'disputes'" class="tab-content">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="disputes.length === 0" class="empty-state">
        {{ t('settlements.noDisputes') }}
      </div>
      <div v-else class="disputes-list">
        <div
          v-for="dispute in disputes"
          :key="dispute.id"
          class="dispute-card"
        >
          <div class="dispute-header">
            <h3 class="market-title">{{ dispute.market_title }}</h3>
            <span :class="['status-tag', dispute.status]">
              {{ getDisputeStatusLabel(dispute.status) }}
            </span>
          </div>
          <p class="dispute-reason">{{ dispute.reason }}</p>
          <div class="dispute-meta">
            <span>{{ t('settlements.submittedAt') }}: {{ formatDate(dispute.created_at) }}</span>
            <span>{{ t('settlements.expectedResolution') }}: {{ formatDate(dispute.expected_resolution_at) }}</span>
          </div>
          <div v-if="dispute.resolution" class="dispute-resolution">
            <h4>{{ t('settlements.resolution') }}</h4>
            <p>{{ dispute.resolution }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Dispute Modal -->
    <div v-if="showDisputeModal" class="modal-overlay" @click="closeDisputeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ t('settlements.submitDispute') }}</h2>
          <button class="modal-close" @click="closeDisputeModal">×</button>
        </div>
        <form @submit.prevent="submitDispute" class="dispute-form">
          <div class="form-group">
            <label>{{ t('settlements.disputeReason') }}</label>
            <textarea
              v-model="disputeForm.reason"
              :placeholder="t('settlements.disputeReasonPlaceholder')"
              rows="4"
              required
            ></textarea>
          </div>
          <div class="form-group">
            <label>{{ t('settlements.evidence') }}</label>
            <div class="upload-area" @click="triggerUpload">
              <span v-if="disputeForm.evidence">✓ {{ disputeForm.evidence.name }}</span>
              <span v-else>{{ t('settlements.uploadEvidence') }}</span>
            </div>
          </div>
          <div v-if="disputeError" class="error-message">{{ disputeError }}</div>
          <div class="modal-actions">
            <button type="button" @click="closeDisputeModal" class="btn-cancel">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="disputeLoading">
              {{ disputeLoading ? t('common.loading') : t('settlements.submitDispute') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref<'pending' | 'completed' | 'disputes'>('pending')
const loading = ref(false)

const pendingSettlements = ref<any[]>([])
const completedSettlements = ref<any[]>([])
const disputes = ref<any[]>([])

const showDisputeModal = ref(false)
const disputeLoading = ref(false)
const disputeError = ref('')
const selectedSettlement = ref<any>(null)

const disputeForm = ref({
  reason: '',
  evidence: null as File | null,
})

const formatNumber = (num: number): string => {
  return num.toLocaleString('vi-VN')
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatRelativeTime = (dateStr: string): string => {
  const expires = new Date(dateStr)
  const now = new Date()
  const diff = expires.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 0) return t('settlements.expired')
  if (hours < 24) return `${hours} ${t('admin.hoursAgo')}`
  const days = Math.floor(hours / 24)
  return `${days} ${t('topic.days')}`
}

const getDisputeStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: t('wallet.statusPending'),
    under_review: t('settlements.underReview'),
    resolved: t('settlements.resolved'),
    rejected: t('wallet.statusFailed'),
  }
  return labels[status] || status
}

const loadSettlements = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'pending') {
      const response = await apiClient.get('/settlements/pending')
      pendingSettlements.value = response.data.settlements || []
    } else if (activeTab.value === 'completed') {
      const response = await apiClient.get('/settlements/completed')
      completedSettlements.value = response.data.settlements || []
    } else {
      const response = await apiClient.get('/settlements/disputes')
      disputes.value = response.data.disputes || []
    }
  } catch (e) {
    console.error('Failed to load settlements:', e)
  } finally {
    loading.value = false
  }
}

const viewDetails = (id: string) => {
  router.push(`/settlements/${id}`)
}

const openDisputeForm = (settlement: any) => {
  selectedSettlement.value = settlement
  showDisputeModal.value = true
  disputeForm.value = { reason: '', evidence: null }
  disputeError.value = ''
}

const closeDisputeModal = () => {
  showDisputeModal.value = false
  selectedSettlement.value = null
  disputeForm.value = { reason: '', evidence: null }
  disputeError.value = ''
}

const triggerUpload = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,application/pdf'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      disputeForm.value.evidence = file
    }
  }
  input.click()
}

const submitDispute = async () => {
  if (!selectedSettlement.value) return

  disputeLoading.value = true
  disputeError.value = ''

  try {
    const formData = new FormData()
    formData.append('reason', disputeForm.value.reason)
    if (disputeForm.value.evidence) {
      formData.append('evidence', disputeForm.value.evidence)
    }

    await apiClient.post(`/settlements/${selectedSettlement.value.id}/dispute`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    closeDisputeModal()
    await loadSettlements()
    alert(t('settlements.disputeSubmitted'))
  } catch (e: any) {
    disputeError.value = e.response?.data?.detail || t('settlements.disputeFailed')
  } finally {
    disputeLoading.value = false
  }
}

onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadSettlements()
})
</script>

<style scoped>
.settlements-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.settlements-header {
  margin-bottom: 24px;
}

.settlements-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
  padding-bottom: 12px;
}

.tab {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-500, #6b7280);
  transition: all 0.2s;
  border-radius: 8px;
}

.tab.active {
  background: var(--color-primary-50, #eff6ff);
  color: var(--color-primary-600, #2563eb);
}

.tab-content {
  min-height: 300px;
}

.loading, .empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-gray-500, #6b7280);
}

.settlements-list, .disputes-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settlement-card, .dispute-card {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  background: white;
}

.settlement-header, .dispute-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.market-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  flex: 1;
}

.expires-tag {
  font-size: 12px;
  color: var(--color-warning-500, #f59e0b);
  background: #fef3c7;
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.result-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
}

.result-tag.win {
  background: #dcfce7;
  color: #15803d;
}

.result-tag.lose {
  background: #fee2e2;
  color: #dc2626;
}

.market-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 16px;
  line-height: 1.5;
}

.settlement-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.info-item .value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.settlement-result {
  padding: 12px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
  margin-bottom: 16px;
}

.result-info {
  margin-bottom: 8px;
}

.result-label {
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}

.result-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.payout-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.payout-label {
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}

.payout-value {
  font-size: 16px;
  font-weight: 600;
}

.payout-value.win {
  color: var(--color-success-500, #10b981);
}

.payout-value.lose {
  color: var(--color-error-500, #ef4444);
}

.settlement-actions, .dispute-actions {
  display: flex;
  gap: 12px;
}

.btn-secondary {
  padding: 8px 16px;
  background: white;
  color: var(--color-gray-700, #374151);
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--color-gray-50, #f9fafb);
}

.btn-dispute {
  padding: 8px 16px;
  background: var(--color-warning-500, #f59e0b);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-dispute:hover {
  background: #d97706;
}

.dispute-reason {
  font-size: 14px;
  color: var(--color-gray-700, #374151);
  margin-bottom: 12px;
  line-height: 1.5;
}

.dispute-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.status-tag {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-tag.pending {
  background: #fef3c7;
  color: #b45309;
}

.status-tag.under_review {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-tag.resolved {
  background: #dcfce7;
  color: #15803d;
}

.status-tag.rejected {
  background: #fee2e2;
  color: #dc2626;
}

.dispute-resolution {
  margin-top: 16px;
  padding: 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.dispute-resolution h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-gray-700, #374151);
}

.dispute-resolution p {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  line-height: 1.5;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-gray-400, #9ca3af);
  cursor: pointer;
}

.dispute-form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
}

.form-group textarea {
  padding: 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.upload-area {
  padding: 16px;
  border: 2px dashed var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  color: var(--color-gray-400, #9ca3af);
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: var(--color-primary-500, #3b82f6);
  background: var(--color-primary-50, #eff6ff);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
}

.btn-cancel {
  padding: 10px 20px;
  background: white;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-submit {
  padding: 10px 24px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}
</style>

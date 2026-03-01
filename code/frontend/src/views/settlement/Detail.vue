<template>
  <div class="settlement-detail-page">
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadSettlement" class="btn-retry">{{ t('common.retry') }}</button>
    </div>
    <div v-else-if="settlement" class="settlement-content">
      <!-- Header -->
      <div class="settlement-header">
        <div class="market-info">
          <h1>{{ settlement.market_title }}</h1>
          <p class="market-description">{{ settlement.description }}</p>
        </div>
        <span :class="['status-tag', settlement.status]">
          {{ getStatusLabel(settlement.status) }}
        </span>
      </div>

      <!-- Settlement Result -->
      <div v-if="settlement.status === 'settled'" class="result-section">
        <h2>{{ t('settlements.settlementResult') }}</h2>
        <div class="result-info">
          <div class="result-badge">
            <span class="check-icon">✓</span>
            <span class="result-text">{{ settlement.winning_outcome }}</span>
          </div>
          <p class="result-description">{{ settlement.winning_outcome_description }}</p>
          <p class="settled-time">{{ t('settlements.settledAt') }}: {{ formatDate(settlement.settled_at) }}</p>
        </div>
      </div>

      <!-- User Position -->
      <div class="position-section">
        <h2>{{ t('settlements.yourPosition') }}</h2>
        <div class="position-card">
          <div class="position-row">
            <span class="label">{{ t('topic.selectOutcome') }}:</span>
            <span class="value">{{ settlement.user_outcome_option }}</span>
          </div>
          <div class="position-row">
            <span class="label">{{ t('positions.shares') }}:</span>
            <span class="value">{{ settlement.user_shares }}</span>
          </div>
          <div class="position-row">
            <span class="label">{{ t('topic.avgPrice') }}:</span>
            <span class="value">{{ settlement.user_avg_price?.toFixed(4) }}</span>
          </div>
        </div>
      </div>

      <!-- Payout -->
      <div v-if="settlement.status === 'settled'" class="payout-section">
        <h2>{{ t('settlements.payout') }}</h2>
        <div :class="['payout-card', settlement.user_won ? 'win' : 'lose']">
          <div class="pamount">
            <span class="payout-label">{{ settlement.user_won ? t('settlements.won') : t('settlements.lost') }}</span>
            <span class="payout-value">
              {{ settlement.user_won ? '+' : '-' }}{{ formatNumber(Math.abs(settlement.payout)) }} {{ t('common.coins') }}
            </span>
          </div>
          <p class="payout-description">
            {{ settlement.user_won ? t('settlements.wonDescription') : t('settlements.lostDescription') }}
          </p>
        </div>
      </div>

      <!-- Market Statistics -->
      <div class="stats-section">
        <h2>{{ t('settlements.marketStats') }}</h2>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">{{ t('settlements.totalPool') }}</span>
            <span class="stat-value">{{ formatNumber(settlement.total_pool) }} {{ t('common.coins') }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ t('settlements.participants') }}</span>
            <span class="stat-value">{{ settlement.participant_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ t('settlements.totalShares') }}</span>
            <span class="stat-value">{{ formatNumber(settlement.total_shares) }}</span>
          </div>
        </div>
      </div>

      <!-- Final Probabilities -->
      <div class="probabilities-section">
        <h2>{{ t('topic.marketProbability') }} ({{ t('topic.final') }})</h2>
        <div class="probability-bars">
          <div
            v-for="(outcome, index) in settlement.outcome_options"
            :key="index"
            :class="['probability-item', index === settlement.winning_outcome_index ? 'winner' : '']"
          >
            <div class="probability-label">
              <span class="outcome-name">{{ outcome }}</span>
              <span :class="['probability-value', index === settlement.winning_outcome_index ? 'winner' : '']">
                {{ settlement.final_probabilities?.[index] ? (settlement.final_probabilities[index] * 100).toFixed(1) : '0' }}%
              </span>
            </div>
            <div class="probability-bar">
              <div
                class="bar-fill"
                :class="{ winner: index === settlement.winning_outcome_index }"
                :style="{ width: `${(settlement.final_probabilities?.[index] || 0) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Dispute Section -->
      <div v-if="settlement.status === 'settled' && settlement.can_dispute && !settlement.has_dispute" class="dispute-section">
        <div class="dispute-info">
          <h3>{{ t('settlements.disagreeWithResult') }}</h3>
          <p>{{ t('settlements.disputeDeadline') }}: {{ formatRelativeTime(settlement.dispute_deadline) }}</p>
        </div>
        <button @click="submitDispute" class="btn-dispute">
          {{ t('settlements.submitDispute') }}
        </button>
      </div>

      <!-- Existing Dispute -->
      <div v-if="settlement.dispute" class="existing-dispute">
        <h2>{{ t('settlements.yourDispute') }}</h2>
        <div :class="['dispute-status', settlement.dispute.status]">
          <span class="status-label">{{ t('settlements.status') }}:</span>
          <span class="status-value">{{ getDisputeStatusLabel(settlement.dispute.status) }}</span>
        </div>
        <p class="dispute-reason">{{ settlement.dispute.reason }}</p>
        <div v-if="settlement.dispute.resolution" class="dispute-resolution">
          <h4>{{ t('settlements.resolution') }}</h4>
          <p>{{ settlement.dispute.resolution }}</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions-section">
        <button @click="goBack" class="btn-back">{{ t('common.back') }}</button>
        <router-link to="/settlements" class="btn-primary">
          {{ t('settlements.viewAll') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref<string | null>(null)
const settlement = ref<any>(null)

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
  const date = new Date(dateStr)
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 0) return t('settlements.expired')
  if (hours < 24) return `${hours} ${t('admin.hoursAgo')}`
  const days = Math.floor(hours / 24)
  return `${days} ${t('topic.days')}`
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: t('wallet.statusPending'),
    under_review: t('settlements.underReview'),
    settled: t('status.settled'),
    disputed: t('settlements.disputed'),
  }
  return labels[status] || status
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

const loadSettlement = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get(`/settlements/${route.params.id}`)
    settlement.value = response.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('settlements.loadFailed')
  } finally {
    loading.value = false
  }
}

const submitDispute = () => {
  router.push(`/settlements/${route.params.id}/dispute`)
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadSettlement()
})
</script>

<style scoped>
.settlement-detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.loading, .error {
  text-align: center;
  padding: 48px 16px;
}

.error {
  color: var(--color-error-500, #ef4444);
}

.btn-retry {
  margin-top: 16px;
  padding: 8px 24px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.settlement-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settlement-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.market-info h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 8px;
}

.market-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  line-height: 1.5;
}

.status-tag {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 16px;
  white-space: nowrap;
}

.status-tag.pending {
  background: #fef3c7;
  color: #b45309;
}

.status-tag.under_review {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-tag.settled {
  background: #dcfce7;
  color: #15803d;
}

.status-tag.disputed {
  background: #fed7aa;
  color: #c2410c;
}

.result-section,
.position-section,
.payout-section,
.stats-section,
.probabilities-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
}

.result-section h2,
.position-section h2,
.payout-section h2,
.stats-section h2,
.probabilities-section h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 16px;
}

.result-info {
  text-align: center;
}

.result-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  background: #dcfce7;
  border-radius: 12px;
  margin-bottom: 12px;
}

.check-icon {
  font-size: 24px;
  color: #15803d;
}

.result-text {
  font-size: 16px;
  font-weight: 600;
  color: #15803d;
}

.result-description {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  margin-bottom: 8px;
}

.settled-time {
  font-size: 13px;
  color: var(--color-gray-400, #9ca3af);
}

.position-card {
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
  padding: 16px;
}

.position-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
}

.position-row:last-child {
  border-bottom: none;
}

.position-row .label {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
}

.position-row .value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.payout-card {
  padding: 24px;
  border-radius: 12px;
  text-align: center;
}

.payout-card.win {
  background: #dcfce7;
}

.payout-card.lose {
  background: #fee2e2;
}

.pamount {
  margin-bottom: 8px;
}

.payout-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.payout-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.payout-card.win .payout-value {
  color: #15803d;
}

.payout-card.lose .payout-value {
  color: #dc2626;
}

.payout-description {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.probability-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.probability-item {
  margin-bottom: 16px;
}

.probability-item.winner {
  padding: 12px;
  background: #dcfce7;
  border-radius: 8px;
}

.probability-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.outcome-name {
  font-weight: 500;
  font-size: 14px;
}

.probability-value {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
}

.probability-value.winner {
  color: #15803d;
  font-weight: 600;
}

.probability-bar {
  height: 8px;
  background: var(--color-gray-200, #e5e7eb);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--color-primary-500, #3b82f6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-fill.winner {
  background: #10b981;
}

.dispute-section {
  background: #fef3c7;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dispute-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: #b45309;
  margin-bottom: 4px;
}

.dispute-info p {
  font-size: 13px;
  color: #92400e;
}

.btn-dispute {
  padding: 12px 24px;
  background: #b45309;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.btn-dispute:hover {
  background: #92400e;
}

.existing-dispute {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
}

.existing-dispute h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.dispute-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 16px;
  margin-bottom: 16px;
}

.dispute-status.pending {
  background: #fef3c7;
  color: #b45309;
}

.dispute-status.under_review {
  background: #dbeafe;
  color: #1d4ed8;
}

.dispute-status.resolved {
  background: #dcfce7;
  color: #15803d;
}

.dispute-status.rejected {
  background: #fee2e2;
  color: #dc2626;
}

.status-label {
  font-size: 13px;
  font-weight: 500;
}

.status-value {
  font-size: 13px;
}

.dispute-reason {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  line-height: 1.5;
  margin-bottom: 16px;
}

.dispute-resolution {
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

.actions-section {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-back,
.btn-primary {
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-back {
  background: white;
  color: var(--color-gray-700, #374151);
  border: 1px solid var(--color-gray-300, #d1d5db);
}

.btn-back:hover {
  background: var(--color-gray-50, #f9fafb);
}

.btn-primary {
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
}

.btn-primary:hover {
  background: var(--color-primary-600, #2563eb);
}

@media (max-width: 640px) {
  .settlement-header {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .dispute-section {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .actions-section {
    flex-direction: column;
  }

  .btn-back,
  .btn-primary {
    width: 100%;
  }
}
</style>

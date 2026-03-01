<template>
  <div class="positions-page">
    <div class="positions-header">
      <h1>{{ t('topic.positions') }}</h1>
      <div class="portfolio-summary" v-if="portfolio">
        <div class="summary-item">
          <span class="label">{{ t('positions.totalValue') }}</span>
          <span class="value">{{ formatNumber(portfolio.total_value) }} {{ t('common.coins') }}</span>
        </div>
        <div class="summary-item">
          <span class="label">{{ t('positions.totalCost') }}</span>
          <span class="value">{{ formatNumber(portfolio.total_cost) }} {{ t('common.coins') }}</span>
        </div>
        <div class="summary-item">
          <span class="label">{{ t('positions.totalPnL') }}</span>
          <span :class="['value', portfolio.total_pnl >= 0 ? 'positive' : 'negative']">
            {{ portfolio.total_pnl >= 0 ? '+' : '' }}{{ formatNumber(portfolio.total_pnl) }} {{ t('common.coins') }}
          </span>
        </div>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="filter-tabs">
      <button
        :class="['tab', filter === 'all' ? 'active' : '']"
        @click="filter = 'all'"
      >
        {{ t('positions.all') }}
      </button>
      <button
        :class="['tab', filter === 'active' ? 'active' : '']"
        @click="filter = 'active'"
      >
        {{ t('positions.active') }}
      </button>
      <button
        :class="['tab', filter === 'settled' ? 'active' : '']"
        @click="filter = 'settled'"
      >
        {{ t('positions.settled') }}
      </button>
    </div>

    <!-- Positions List -->
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="positions.length === 0" class="empty-state">
      <p>{{ t('positions.noPositions') }}</p>
      <router-link to="/topics" class="btn-primary">
        {{ t('positions.browseTopics') }}
      </router-link>
    </div>
    <div v-else class="positions-list">
      <div
        v-for="position in filteredPositions"
        :key="position.id"
        class="position-card"
        @click="goToTopic(position.topic_id)"
      >
        <div class="position-header">
          <div class="topic-info">
            <h3 class="topic-title">{{ position.topic_title }}</h3>
            <span :class="['status-tag', position.market_status]">
              {{ getStatusLabel(position.market_status) }}
            </span>
          </div>
          <div class="outcome-badge">
            {{ position.outcome_option }}
          </div>
        </div>

        <div class="position-details">
          <div class="detail-row">
            <span class="detail-label">{{ t('positions.shares') }}:</span>
            <span class="detail-value">{{ position.shares }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('topic.avgPrice') }}:</span>
            <span class="detail-value">{{ position.avg_price.toFixed(4) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('topic.currentValue') }}:</span>
            <span class="detail-value">{{ formatNumber(position.current_value) }} {{ t('common.coins') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('positions.pnl') }}:</span>
            <span :class="['detail-value', position.pnl >= 0 ? 'positive' : 'negative']">
              {{ position.pnl >= 0 ? '+' : '' }}{{ formatNumber(position.pnl) }} {{ t('common.coins') }}
            </span>
          </div>
        </div>

        <div class="position-actions">
          <router-link
            v-if="position.market_status === 'active'"
            :to="`/topics/${position.topic_id}`"
            class="btn-trade"
          >
            {{ t('topic.trade') }}
          </router-link>
          <span v-else class="market-closed">{{ t('positions.marketClosed') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

interface Position {
  id: string
  topic_id: string
  topic_title: string
  outcome_index: number
  outcome_option: string
  shares: number
  avg_price: number
  current_price: number
  current_value: number
  pnl: number
  market_status: string
  expires_at: string
}

interface Portfolio {
  total_value: number
  total_cost: number
  total_pnl: number
}

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const positions = ref<Position[]>([])
const portfolio = ref<Portfolio | null>(null)
const filter = ref<'all' | 'active' | 'settled'>('all')

const filteredPositions = computed(() => {
  if (filter.value === 'all') return positions.value
  if (filter.value === 'active') {
    return positions.value.filter(p => p.market_status === 'active')
  }
  return positions.value.filter(p => p.market_status === 'settled' || p.market_status === 'expired')
})

const formatNumber = (num: number): string => {
  return num.toLocaleString('vi-VN')
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: t('status.active'),
    expired: t('status.expired'),
    settled: t('status.settled'),
    pending_review: t('status.pendingReview'),
  }
  return labels[status] || status
}

const loadPositions = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/trading/positions')
    positions.value = response.data.positions || []

    // Calculate portfolio summary
    if (positions.value.length > 0) {
      const total_value = positions.value.reduce((sum, p) => sum + p.current_value, 0)
      const total_cost = positions.value.reduce((sum, p) => sum + (p.avg_price * p.shares), 0)
      portfolio.value = {
        total_value,
        total_cost,
        total_pnl: total_value - total_cost,
      }
    }
  } catch (e) {
    console.error('Failed to load positions:', e)
  } finally {
    loading.value = false
  }
}

const goToTopic = (id: string) => {
  router.push(`/topics/${id}`)
}

onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadPositions()
})
</script>

<style scoped>
.positions-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}

.positions-header {
  margin-bottom: 24px;
}

.positions-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 16px;
}

.portfolio-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 12px;
  opacity: 0.9;
}

.summary-item .value {
  font-size: 18px;
  font-weight: 600;
}

.summary-item .value.positive {
  color: #86efac;
}

.summary-item .value.negative {
  color: #fca5a5;
}

.filter-tabs {
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

.loading, .empty-state {
  text-align: center;
  padding: 48px 16px;
}

.empty-state p {
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 24px;
}

.btn-primary {
  display: inline-block;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--color-primary-600, #2563eb);
}

.positions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.position-card {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.position-card:hover {
  border-color: var(--color-primary-500, #3b82f6);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.position-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.topic-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.topic-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  flex: 1;
}

.status-tag {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.status-tag.active {
  background: #dcfce7;
  color: #15803d;
}

.status-tag.expired,
.status-tag.settled {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-500, #6b7280);
}

.outcome-badge {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary-600, #2563eb);
  background: var(--color-primary-50, #eff6ff);
  padding: 6px 12px;
  border-radius: 16px;
}

.position-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.detail-value.positive {
  color: var(--color-success-500, #10b981);
}

.detail-value.negative {
  color: var(--color-error-500, #ef4444);
}

.position-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-gray-100, #f3f4f6);
}

.btn-trade {
  padding: 8px 16px;
  background: var(--color-success-500, #10b981);
  color: white;
  border: none;
  border-radius: 8px;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-trade:hover {
  background: #059669;
}

.market-closed {
  font-size: 13px;
  color: var(--color-gray-400, #9ca3af);
}

@media (max-width: 640px) {
  .portfolio-summary {
    grid-template-columns: 1fr;
  }

  .position-details {
    grid-template-columns: 1fr;
  }
}
</style>

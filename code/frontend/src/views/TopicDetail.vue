<template>
  <div class="topic-detail">
    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <p>{{ t('common.loading') }}</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="loadTopic" class="btn-retry">{{ t('common.retry') }}</button>
    </div>

    <!-- Topic content -->
    <template v-else-if="topic">
      <!-- Header -->
      <div class="topic-header">
        <span :class="['category-tag', topic.category]">
          {{ getCategoryLabel(topic.category) }}
        </span>
        <span :class="['status-tag', topic.status]">
          {{ getStatusLabel(topic.status) }}
        </span>
      </div>

      <h1 class="topic-title">{{ topic.title }}</h1>
      <p class="topic-description">{{ topic.description }}</p>

      <!-- Market info -->
      <div class="market-info">
        <div class="info-item">
          <span class="label">{{ t('topic.participants') }}</span>
          <span class="value">{{ topic.participant_count }}</span>
        </div>
        <div class="info-item">
          <span class="label">{{ t('topic.volume') }}</span>
          <span class="value">{{ formatNumber(topic.trade_volume) }}</span>
        </div>
        <div class="info-item">
          <span class="label">{{ t('topic.expires') }}</span>
          <span class="value">{{ formatDate(topic.expires_at) }}</span>
        </div>
      </div>

      <!-- Market probabilities -->
      <div class="market-probabilities" v-if="topic.current_prices && topic.current_prices.length > 0">
        <h2>{{ t('topic.marketProbability') }}</h2>
        <div class="probability-bars">
          <div
            v-for="(price, index) in topic.current_prices"
            :key="index"
            class="probability-item"
          >
            <div class="probability-label">
              <span class="outcome-name">{{ topic.outcome_options[index] }}</span>
              <span class="probability-value">{{ (price * 100).toFixed(1) }}%</span>
            </div>
            <div class="probability-bar">
              <div
                class="bar-fill"
                :style="{ width: `${Math.min(100, price * 100 * 1.2)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trading section (only for active markets) -->
      <div v-if="topic.status === 'active' && !isExpired" class="trading-section">
        <div class="trading-tabs">
          <button
            :class="['tab', activeTab === 'buy' ? 'active' : '']"
            @click="activeTab = 'buy'"
          >
            {{ t('topic.buy') }}
          </button>
          <button
            :class="['tab', activeTab === 'sell' ? 'active' : '']"
            @click="activeTab = 'sell'"
          >
            {{ t('topic.sell') }}
          </button>
          <button
            :class="['tab', activeTab === 'positions' ? 'active' : '']"
            @click="activeTab = 'positions'"
          >
            {{ t('topic.positions') }}
          </button>
        </div>

        <!-- Buy form -->
        <div v-if="activeTab === 'buy'" class="trade-form">
          <div class="form-group">
            <label>{{ t('topic.selectOutcome') }}</label>
            <select v-model="selectedOutcome">
              <option
                v-for="(option, index) in topic.outcome_options"
                :key="index"
                :value="index"
              >
                {{ option }} - {{ getCurrentPrice(index) }}%
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ t('topic.shares') }}</label>
            <input
              type="number"
              v-model.number="sharesAmount"
              min="1"
              placeholder="100"
            />
          </div>
          <div class="estimated-cost">
            {{ t('topic.estimatedCost') }}: {{ estimatedCost }} {{ t('common.coins') }}
          </div>
          <button
            class="btn-trade btn-buy"
            @click="handleBuy"
            :disabled="!canTrade"
          >
            {{ t('topic.buy') }}
          </button>
        </div>

        <!-- Sell form -->
        <div v-if="activeTab === 'sell'" class="trade-form">
          <div class="form-group">
            <label>{{ t('topic.selectOutcome') }}</label>
            <select v-model="selectedOutcome">
              <option
                v-for="(pos, index) in userPositions"
                :key="index"
                :value="pos.outcome_index"
              >
                {{ pos.outcome_option }} - {{ pos.shares }} {{ t('topic.shares') }}
              </option>
            </select>
            <p v-if="userPositions.length === 0" class="no-positions">
              {{ t('topic.noPositions') }}
            </p>
          </div>
          <div class="form-group">
            <label>{{ t('topic.shares') }}</label>
            <input
              type="number"
              v-model.number="sharesAmount"
              min="1"
              :max="maxSellShares"
              placeholder="100"
            />
          </div>
          <div class="estimated-cost">
            {{ t('topic.estimatedPayout') }}: {{ estimatedPayout }} {{ t('common.coins') }}
          </div>
          <button
            class="btn-trade btn-sell"
            @click="handleSell"
            :disabled="!canTrade || userPositions.length === 0"
          >
            {{ t('topic.sell') }}
          </button>
        </div>

        <!-- User positions -->
        <div v-if="activeTab === 'positions'" class="positions-list">
          <div v-if="userPositions.length === 0" class="empty-state">
            {{ t('topic.noPositions') }}
          </div>
          <div v-else class="position-items">
            <div
              v-for="(pos, index) in userPositions"
              :key="index"
              class="position-item"
            >
              <div class="position-header">
                <span class="position-outcome">{{ pos.outcome_option }}</span>
                <span class="position-shares">{{ pos.shares }} {{ t('topic.shares') }}</span>
              </div>
              <div class="position-details">
                <span>{{ t('topic.avgPrice') }}: {{ pos.avg_price.toFixed(4) }}</span>
                <span>{{ t('topic.currentValue') }}: {{ getCurrentValue(pos) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Market closed notice -->
      <div v-else-if="topic.status !== 'active' || isExpired" class="market-closed">
        <p>{{ getMarketClosedReason() }}</p>
      </div>

      <!-- Settlement info -->
      <div v-if="topic.settled_outcome !== null" class="settlement-info">
        <h3>{{ t('topic.settlementResult') }}</h3>
        <p class="winner">
          {{ t('topic.winner') }}: {{ topic.outcome_options[topic.settled_outcome] }}
        </p>
        <p>{{ t('topic.settledAt') }}: {{ formatDate(topic.settled_at) }}</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

interface Topic {
  id: string
  title: string
  description: string
  category: string
  outcome_options: string[]
  creator_id: string
  status: string
  expires_at: string
  settled_at: string | null
  settled_outcome: number | null
  participant_count: number
  trade_volume: number
  view_count: number
  current_prices: number[] | null
  created_at: string
}

interface Position {
  topic_id: string
  topic_title: string
  outcome_index: number
  outcome_option: string
  shares: number
  avg_price: number
}

const { t } = useI18n()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref<string | null>(null)
const topic = ref<Topic | null>(null)
const userPositions = ref<Position[]>([])
const activeTab = ref<'buy' | 'sell' | 'positions'>('buy')
const selectedOutcome = ref<number>(0)
const sharesAmount = ref<number>(100)

const isExpired = computed(() => {
  if (!topic.value) return false
  return new Date(topic.value.expires_at) < new Date()
})

const canTrade = computed(() => {
  return authStore.isLoggedIn && sharesAmount.value > 0 && !isExpired.value
})

const maxSellShares = computed(() => {
  const pos = userPositions.value.find(p => p.outcome_index === selectedOutcome.value)
  return pos ? pos.shares : 0
})

const estimatedCost = computed(() => {
  // Simplified estimation - actual cost calculated by backend
  if (!topic.value?.current_prices) return '0'
  const price = topic.value.current_prices[selectedOutcome.value] || 0
  return (price * sharesAmount.value).toFixed(0)
})

const estimatedPayout = computed(() => {
  // Simplified estimation
  if (!topic.value?.current_prices) return '0'
  const price = topic.value.current_prices[selectedOutcome.value] || 0
  return (price * sharesAmount.value * 0.95).toFixed(0) // 5% slippage estimate
})

const getCurrentPrice = (index: number): string => {
  if (!topic.value?.current_prices) return '0'
  return (topic.value.current_prices[index] * 100).toFixed(1)
}

const getCurrentValue = (position: Position): string => {
  if (!topic.value?.current_prices) return '0'
  const currentPrice = topic.value.current_prices[position.outcome_index] || 0
  return (currentPrice * position.shares).toFixed(0)
}

const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    tech: t('category.tech'),
    business: t('category.business'),
    culture: t('category.culture'),
    academic: t('category.academic'),
  }
  return labels[category] || category
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: t('status.active'),
    expired: t('status.expired'),
    settled: t('status.settled'),
    pending_review: t('status.pendingReview'),
    rejected: t('status.rejected'),
    suspended: t('status.suspended'),
  }
  return labels[status] || status
}

const formatNumber = (num: number): string => {
  return num.toLocaleString('vi-VN')
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getMarketClosedReason = (): string => {
  if (topic.value?.status === 'expired') {
    return t('topic.marketExpired')
  }
  if (topic.value?.status === 'settled') {
    return t('topic.marketSettled')
  }
  if (topic.value?.status === 'suspended') {
    return t('topic.marketSuspended')
  }
  return t('topic.marketClosed')
}

const loadTopic = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get(`/topics/${route.params.id}`)
    topic.value = response.data

    // Load user positions if logged in
    if (authStore.isLoggedIn) {
      await loadPositions()
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('common.error.loadTopic')
  } finally {
    loading.value = false
  }
}

const loadPositions = async () => {
  try {
    const response = await apiClient.get(`/trading/${route.params.id}/positions`)
    const data = response.data
    userPositions.value = data.positions || []
  } catch (e) {
    // Ignore errors - positions are optional
  }
}

const handleBuy = async () => {
  if (!canTrade.value) return

  try {
    await apiClient.post(`/trading/${route.params.id}/buy`, {
      outcome_index: selectedOutcome.value,
      quantity: sharesAmount.value,
    })
    alert(t('topic.buySuccess'))
    await loadTopic()
    await loadPositions()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error.trade'))
  }
}

const handleSell = async () => {
  if (!canTrade.value || userPositions.value.length === 0) return

  try {
    await apiClient.post(`/trading/${route.params.id}/sell`, {
      outcome_index: selectedOutcome.value,
      quantity: sharesAmount.value,
    })
    alert(t('topic.sellSuccess'))
    await loadTopic()
    await loadPositions()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('common.error.trade'))
  }
}

onMounted(() => {
  loadTopic()
})
</script>

<style scoped>
.topic-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
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

.topic-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.category-tag, .status-tag {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.category-tag.tech { background: #dbeafe; color: #1d4ed8; }
.category-tag.business { background: #dcfce7; color: #15803d; }
.category-tag.culture { background: #fef3c7; color: #b45309; }
.category-tag.academic { background: #f3e8ff; color: #7c3aed; }

.status-tag.active { background: #dcfce7; color: #15803d; }
.status-tag.expired { background: #f3f4f6; color: #6b7280; }
.status-tag.settled { background: #dbeafe; color: #1d4ed8; }

.topic-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-gray-900, #111827);
}

.topic-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 24px;
  line-height: 1.6;
}

.market-info {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 12px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: var(--color-gray-500, #6b7280);
}

.info-item .value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.market-probabilities {
  margin-bottom: 24px;
}

.market-probabilities h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.probability-item {
  margin-bottom: 12px;
}

.probability-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.outcome-name {
  font-weight: 500;
}

.probability-value {
  color: var(--color-gray-500, #6b7280);
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

.trading-section {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
}

.trading-tabs {
  display: flex;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
}

.tab {
  flex: 1;
  padding: 12px;
  border: none;
  background: white;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.tab.active {
  background: var(--color-primary-500, #3b82f6);
  color: white;
}

.trade-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.no-positions {
  color: var(--color-gray-500, #6b7280);
  font-size: 14px;
  margin-top: 8px;
}

.estimated-cost {
  padding: 12px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
  margin-bottom: 16px;
  font-weight: 500;
}

.btn-trade {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-trade:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-buy {
  background: var(--color-success-500, #10b981);
  color: white;
}

.btn-sell {
  background: var(--color-error-500, #ef4444);
  color: white;
}

.positions-list {
  padding: 24px;
}

.empty-state {
  text-align: center;
  color: var(--color-gray-500, #6b7280);
  padding: 24px;
}

.position-item {
  padding: 16px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 8px;
  margin-bottom: 12px;
}

.position-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.position-outcome {
  font-weight: 600;
}

.position-shares {
  color: var(--color-primary-500, #3b82f6);
}

.position-details {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}

.market-closed {
  padding: 24px;
  text-align: center;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 12px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 24px;
}

.settlement-info {
  padding: 24px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
}

.settlement-info h3 {
  margin-bottom: 12px;
}

.winner {
  font-weight: 600;
  color: var(--color-success-500, #10b981);
}
</style>

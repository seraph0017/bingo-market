<template>
  <div class="wallet-page">
    <h1>{{ t('navigation.wallet') }}</h1>

    <!-- Wallet Balance Card -->
    <div class="balance-card">
      <div class="balance-info">
        <span class="balance-label">{{ t('wallet.balance') }}</span>
        <span class="balance-value">{{ formatNumber(wallet.balance) }} {{ t('common.coins') }}</span>
      </div>
      <div class="limit-info">
        <div class="limit-item">
          <span class="limit-label">{{ t('wallet.dailyLimit') }}</span>
          <span class="limit-value">{{ formatNumber(wallet.daily_limit_remaining) }} VND</span>
        </div>
        <div class="limit-item">
          <span class="limit-label">{{ t('wallet.monthlyLimit') }}</span>
          <span class="limit-value">{{ formatNumber(wallet.monthly_limit_remaining) }} VND</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <button class="action-btn recharge" @click="showRecharge = true">
        <span class="icon">💰</span>
        {{ t('wallet.recharge') }}
      </button>
      <button class="action-btn" @click="activeTab = 'transactions'">
        <span class="icon">📋</span>
        {{ t('wallet.transactions') }}
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        :class="['tab', activeTab === 'recharge' ? 'active' : '']"
        @click="activeTab = 'recharge'"
      >
        {{ t('wallet.rechargeRecords') }}
      </button>
      <button
        :class="['tab', activeTab === 'transactions' ? 'active' : '']"
        @click="activeTab = 'transactions'"
      >
        {{ t('wallet.transactions') }}
      </button>
    </div>

    <!-- Recharge Records -->
    <div v-if="activeTab === 'recharge'" class="tab-content">
      <div v-if="loadingRecharge" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="rechargeRecords.length === 0" class="empty-state">
        {{ t('wallet.noRechargeRecords') }}
      </div>
      <div v-else class="records-list">
        <div
          v-for="record in rechargeRecords"
          :key="record.order_id"
          class="record-item"
        >
          <div class="record-header">
            <span class="record-amount">+{{ formatNumber(record.amount_tokens) }} {{ t('common.coins') }}</span>
            <span :class="['status-tag', record.status]">
              {{ getRechargeStatusLabel(record.status) }}
            </span>
          </div>
          <div class="record-details">
            <span>{{ getPaymentMethodLabel(record.payment_method) }}</span>
            <span>{{ formatDate(record.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Transaction Records -->
    <div v-if="activeTab === 'transactions'" class="tab-content">
      <div v-if="loadingTransactions" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="transactions.length === 0" class="empty-state">
        {{ t('wallet.noTransactions') }}
      </div>
      <div v-else class="records-list">
        <div
          v-for="tx in transactions"
          :key="tx.id"
          class="record-item"
        >
          <div class="record-header">
            <span :class="['tx-amount', tx.amount >= 0 ? 'positive' : 'negative']">
              {{ tx.amount >= 0 ? '+' : '' }}{{ formatNumber(tx.amount) }} {{ t('common.coins') }}
            </span>
            <span class="tx-type">{{ getTransactionTypeLabel(tx.transaction_type) }}</span>
          </div>
          <div class="record-details">
            <span>{{ tx.description }}</span>
            <span>{{ formatDate(tx.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Recharge Modal -->
    <div v-if="showRecharge" class="modal-overlay" @click="showRecharge = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ t('wallet.recharge') }}</h2>
          <button class="close-btn" @click="showRecharge = false">×</button>
        </div>

        <div class="modal-body">
          <div class="amount-input-group">
            <label>{{ t('wallet.rechargeAmount') }}</label>
            <div class="amount-input">
              <input
                v-model.number="rechargeForm.amount"
                type="number"
                min="10000"
                step="1000"
                :placeholder="t('wallet.rechargeAmountPlaceholder')"
              />
              <span class="currency">VND</span>
            </div>
            <span class="hint">{{ t('wallet.rechargeHint') }}</span>
          </div>

          <div class="payment-methods">
            <label>{{ t('wallet.paymentMethod') }}</label>
            <div class="method-options">
              <label
                v-for="method in paymentMethods"
                :key="method.value"
                :class="['method-option', rechargeForm.payment_method === method.value ? 'selected' : '']"
              >
                <input
                  type="radio"
                  v-model="rechargeForm.payment_method"
                  :value="method.value"
                  hidden
                />
                <span class="method-icon">{{ method.icon }}</span>
                <span class="method-name">{{ method.label }}</span>
              </label>
            </div>
          </div>

          <div v-if="rechargeError" class="error-message">
            {{ rechargeError }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showRecharge = false">
            {{ t('common.cancel') }}
          </button>
          <button class="btn-confirm" @click="handleRecharge" :disabled="loadingRechargeSubmit">
            {{ loadingRechargeSubmit ? t('common.loading') : t('wallet.confirmRecharge') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'

const { t } = useI18n()

const wallet = ref({
  balance: 0,
  daily_limit_remaining: 0,
  monthly_limit_remaining: 0,
  status: 'active',
})

const activeTab = ref<'recharge' | 'transactions'>('recharge')
const showRecharge = ref(false)
const loadingRecharge = ref(false)
const loadingTransactions = ref(false)
const loadingRechargeSubmit = ref(false)
const rechargeError = ref<string | null>(null)

const rechargeRecords = ref<any[]>([])
const transactions = ref<any[]>([])

const rechargeForm = reactive({
  amount: 0,
  payment_method: 'momo',
})

const paymentMethods = [
  { value: 'momo', label: 'MoMo', icon: '🟠' },
  { value: 'zalopay', label: 'ZaloPay', icon: '🔵' },
]

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

const getRechargeStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: t('wallet.statusPending'),
    success: t('wallet.statusSuccess'),
    failed: t('wallet.statusFailed'),
    cancelled: t('wallet.statusCancelled'),
  }
  return labels[status] || status
}

const getPaymentMethodLabel = (method: string): string => {
  const labels: Record<string, string> = {
    momo: 'MoMo',
    zalopay: 'ZaloPay',
    manual: t('wallet.manualTransfer'),
  }
  return labels[method] || method
}

const getTransactionTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    recharge: t('wallet.typeRecharge'),
    prediction_purchase: t('wallet.typePrediction'),
    prediction_sale: t('wallet.typePredictionSale'),
    settlement: t('wallet.typeSettlement'),
    purchase: t('wallet.typePurchase'),
  }
  return labels[type] || type
}

const loadWallet = async () => {
  try {
    const response = await apiClient.get('/wallet')
    wallet.value = response.data
  } catch (e) {
    console.error('Failed to load wallet:', e)
  }
}

const loadRechargeRecords = async () => {
  loadingRecharge.value = true
  try {
    const response = await apiClient.get('/wallet/recharge/records')
    rechargeRecords.value = response.data.records || []
  } catch (e) {
    console.error('Failed to load recharge records:', e)
  } finally {
    loadingRecharge.value = false
  }
}

const loadTransactions = async () => {
  loadingTransactions.value = true
  try {
    const response = await apiClient.get('/wallet/transactions')
    transactions.value = response.data.transactions || []
  } catch (e) {
    console.error('Failed to load transactions:', e)
  } finally {
    loadingTransactions.value = false
  }
}

const handleRecharge = async () => {
  rechargeError.value = null

  if (rechargeForm.amount < 10000) {
    rechargeError.value = t('wallet.minRechargeAmount')
    return
  }

  if (rechargeForm.amount % 1000 !== 0) {
    rechargeError.value = t('wallet.rechargeMultiple')
    return
  }

  loadingRechargeSubmit.value = true

  try {
    const response = await apiClient.post('/wallet/recharge/orders', rechargeForm)

    // Redirect to payment gateway
    if (response.data.redirect_url) {
      window.location.href = response.data.redirect_url
    } else {
      alert(t('wallet.rechargeOrderCreated'))
      showRecharge.value = false
      await loadWallet()
      await loadRechargeRecords()
    }
  } catch (e: any) {
    rechargeError.value = e.response?.data?.detail || t('wallet.rechargeFailed')
  } finally {
    loadingRechargeSubmit.value = false
  }
}

onMounted(() => {
  loadWallet()
  loadRechargeRecords()
})
</script>

<style scoped>
.wallet-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.wallet-page h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-gray-900, #111827);
}

.balance-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  margin-bottom: 20px;
}

.balance-info {
  margin-bottom: 20px;
}

.balance-label {
  display: block;
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.balance-value {
  display: block;
  font-size: 36px;
  font-weight: 700;
}

.limit-info {
  display: flex;
  gap: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.limit-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.limit-label {
  font-size: 12px;
  opacity: 0.8;
}

.limit-value {
  font-size: 14px;
  font-weight: 600;
}

.quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.action-btn.recharge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.action-btn:not(.recharge) {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-700, #374151);
}

.icon {
  font-size: 20px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
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
}

.tab.active {
  color: var(--color-primary-600, #2563eb);
  border-bottom: 2px solid var(--color-primary-600, #2563eb);
}

.tab-content {
  min-height: 200px;
}

.loading, .empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-gray-500, #6b7280);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  background: white;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-amount, .tx-amount {
  font-size: 18px;
  font-weight: 600;
}

.tx-amount.positive {
  color: var(--color-success-500, #10b981);
}

.tx-amount.negative {
  color: var(--color-error-500, #ef4444);
}

.status-tag {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.pending {
  background: #fef3c7;
  color: #b45309;
}

.status-tag.success {
  background: #dcfce7;
  color: #15803d;
}

.status-tag.failed {
  background: #fee2e2;
  color: #dc2626;
}

.status-tag.cancelled {
  background: #f3f4f6;
  color: #6b7280;
}

.tx-type {
  font-size: 12px;
  color: var(--color-gray-500, #6b7280);
  background: var(--color-gray-100, #f3f4f6);
  padding: 4px 8px;
  border-radius: 4px;
}

.record-details {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
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
  z-index: 9999;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
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
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-gray-500, #6b7280);
}

.modal-body {
  padding: 20px;
}

.amount-input-group {
  margin-bottom: 20px;
}

.amount-input-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.amount-input {
  position: relative;
  display: flex;
  align-items: center;
}

.amount-input input {
  flex: 1;
  padding: 12px 16px;
  padding-right: 60px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 16px;
}

.amount-input .currency {
  position: absolute;
  right: 12px;
  font-weight: 600;
  color: var(--color-gray-500, #6b7280);
}

.hint {
  display: block;
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
  margin-top: 4px;
}

.payment-methods {
  margin-bottom: 20px;
}

.payment-methods label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.method-options {
  display: flex;
  gap: 12px;
}

.method-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border: 2px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.method-option.selected {
  border-color: var(--color-primary-500, #3b82f6);
  background: #eff6ff;
}

.method-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.method-name {
  font-size: 14px;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--color-gray-200, #e5e7eb);
}

.btn-cancel, .btn-confirm {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-cancel {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-700, #374151);
}

.btn-confirm {
  background: var(--color-primary-500, #3b82f6);
  color: white;
}

.btn-confirm:disabled {
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

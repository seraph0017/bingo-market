<template>
  <div class="mall-page">
    <!-- Header -->
    <div class="mall-header">
      <h1>{{ t('navigation.mall') }}</h1>
      <div class="wallet-info">
        <span class="balance-label">{{ t('wallet.balance') }}:</span>
        <span class="balance-value">{{ balance }} {{ t('common.coins') }}</span>
        <button class="btn-recharge" @click="goToWallet">{{ t('wallet.recharge') }}</button>
      </div>
    </div>

    <!-- Product Categories -->
    <div class="product-categories">
      <button
        :class="['tab', selectedCategory === '' ? 'active' : '']"
        @click="selectCategory('')"
      >
        {{ t('mall.allProducts') }}
      </button>
      <button
        v-for="cat in categories"
        :key="cat"
        :class="['tab', selectedCategory === cat ? 'active' : '']"
        @click="selectCategory(cat)"
      >
        {{ getCategoryLabel(cat) }}
      </button>
    </div>

    <!-- Products Grid -->
    <div v-if="loading" class="loading">
      <p>{{ t('common.loading') }}</p>
    </div>

    <div v-else-if="products.length === 0" class="empty-state">
      <p>{{ t('mall.noProducts') }}</p>
    </div>

    <div v-else class="products-grid">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-card"
      >
        <div class="product-image">
          <img :src="product.image_url || '/placeholder-product.png'" :alt="product.name" />
        </div>

        <div class="product-info">
          <h3 class="product-name">{{ product.name }}</h3>
          <p class="product-description">{{ product.description }}</p>

          <div class="product-meta">
            <span :class="['stock-tag', product.stock > 0 ? 'in-stock' : 'out-of-stock']">
              {{ product.stock > 0 ? t('mall.inStock') : t('mall.outOfStock') }}
            </span>
            <span class="category-tag">{{ getCategoryLabel(product.category) }}</span>
          </div>

          <div class="product-price">
            <span class="price-label">{{ t('mall.price') }}:</span>
            <span class="price-value">{{ formatNumber(product.price_coins) }} {{ t('common.coins') }}</span>
          </div>

          <button
            class="btn-exchange"
            :class="{ disabled: !canExchange(product) }"
            :disabled="!canExchange(product)"
            @click="exchangeProduct(product)"
          >
            {{ t('mall.exchange') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Exchange History -->
    <div class="exchange-history">
      <h2>{{ t('mall.exchangeHistory') }}</h2>
      <div v-if="exchangeRecords.length === 0" class="no-records">
        <p>{{ t('mall.noExchangeHistory') }}</p>
      </div>
      <div v-else class="records-list">
        <div
          v-for="record in exchangeRecords"
          :key="record.id"
          class="record-item"
        >
          <div class="record-header">
            <span class="product-name">{{ record.product_name }}</span>
            <span :class="['status-tag', record.status]">
              {{ getStatusLabel(record.status) }}
            </span>
          </div>
          <div class="record-details">
            <span>{{ t('mall.coinsSpent') }}: {{ record.coins_spent }}</span>
            <span>{{ t('mall.exchangeTime') }}: {{ formatDate(record.created_at) }}</span>
          </div>
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

interface Product {
  id: string
  name: string
  description: string
  category: string
  price_coins: number
  stock: number
  image_url: string | null
  delivery_method: string
  created_at: string
}

interface ExchangeRecord {
  id: string
  product_id: string
  product_name: string
  coins_spent: number
  status: string
  created_at: string
}

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const products = ref<Product[]>([])
const exchangeRecords = ref<ExchangeRecord[]>([])
const balance = ref(0)
const selectedCategory = ref('')

const categories = ['digital', 'voucher', 'service', 'physical']

const canExchange = (product: Product): boolean => {
  return product.stock > 0 && balance.value >= product.price_coins
}

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

const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    digital: t('mall.categoryDigital'),
    voucher: t('mall.categoryVoucher'),
    service: t('mall.categoryService'),
    physical: t('mall.categoryPhysical'),
    tech: t('category.tech'),
    business: t('category.business'),
    culture: t('category.culture'),
    academic: t('category.academic'),
  }
  return labels[category] || category
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: t('mall.statusPending'),
    processing: t('mall.statusProcessing'),
    completed: t('mall.statusCompleted'),
    failed: t('mall.statusFailed'),
  }
  return labels[status] || status
}

const loadProducts = async () => {
  loading.value = true

  try {
    const params: Record<string, string> = {}
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }

    const response = await apiClient.get('/products', { params })
    products.value = response.data.products || []
  } catch (e: any) {
    console.error('Failed to load products:', e)
  } finally {
    loading.value = false
  }
}

const loadWallet = async () => {
  try {
    const response = await apiClient.get('/wallet')
    balance.value = response.data.balance || 0
  } catch (e) {
    // Ignore error
  }
}

const loadExchangeHistory = async () => {
  try {
    const response = await apiClient.get('/exchange/orders')
    exchangeRecords.value = response.data.orders || []
  } catch (e) {
    // Ignore error
  }
}

const selectCategory = (category: string) => {
  selectedCategory.value = category
  loadProducts()
}

const exchangeProduct = async (product: Product) => {
  if (!canExchange(product)) return

  const confirmed = confirm(t('mall.confirmExchange').replace('{name}', product.name).replace('{price}', String(product.price_coins)))
  if (!confirmed) return

  try {
    await apiClient.post(`/products/${product.id}/exchange`)
    alert(t('mall.exchangeSuccess'))
    await loadWallet()
    await loadExchangeHistory()
    await loadProducts()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('mall.exchangeFailed'))
  }
}

const goToWallet = () => {
  router.push('/wallet')
}

onMounted(() => {
  loadWallet()
  loadProducts()
  loadExchangeHistory()
})
</script>

<style scoped>
.mall-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}

.mall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.mall-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.wallet-info {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--color-gray-50, #f9fafb);
  padding: 12px 16px;
  border-radius: 12px;
}

.balance-label {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
}

.balance-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary-600, #2563eb);
}

.btn-recharge {
  padding: 8px 16px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.product-categories {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.product-categories .tab {
  padding: 8px 16px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  background: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.product-categories .tab.active {
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border-color: var(--color-primary-500, #3b82f6);
}

.loading, .empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-gray-500, #6b7280);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.product-card {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.2s;
}

.product-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
}

.product-image {
  width: 100%;
  height: 160px;
  background: var(--color-gray-100, #f3f4f6);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 16px;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-gray-900, #111827);
}

.product-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.stock-tag, .category-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.stock-tag.in-stock {
  background: #dcfce7;
  color: #15803d;
}

.stock-tag.out-of-stock {
  background: #fee2e2;
  color: #dc2626;
}

.category-tag {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-600, #4b5563);
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 16px;
}

.price-label {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
}

.price-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary-600, #2563eb);
}

.btn-exchange {
  width: 100%;
  padding: 12px;
  background: var(--color-success-500, #10b981);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: opacity 0.2s;
}

.btn-exchange.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-gray-400, #9ca3af);
}

.exchange-history {
  border-top: 1px solid var(--color-gray-200, #e5e7eb);
  padding-top: 24px;
}

.exchange-history h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-gray-900, #111827);
}

.no-records {
  text-align: center;
  padding: 24px;
  color: var(--color-gray-500, #6b7280);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 8px;
  padding: 12px 16px;
  background: white;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-header .product-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-900, #111827);
}

.status-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.pending {
  background: #fef3c7;
  color: #b45309;
}

.status-tag.processing {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-tag.completed {
  background: #dcfce7;
  color: #15803d;
}

.status-tag.failed {
  background: #fee2e2;
  color: #dc2626;
}

.record-details {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}
</style>

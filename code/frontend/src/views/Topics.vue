<template>
  <div class="topics-page">
    <!-- Header -->
    <div class="topics-header">
      <h1>{{ t('navigation.topics') }}</h1>

      <div class="header-actions">
        <!-- Search -->
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="t('topic.searchPlaceholder')"
            @keyup.enter="handleSearch"
          />
          <button @click="handleSearch">{{ t('topic.search') }}</button>
        </div>

        <!-- Create Topic Button -->
        <button
          v-if="isLoggedIn && isCreator"
          @click="showCreateModal = true"
          class="btn-create"
        >
          <span>+</span> {{ t('topic.create') }}
        </button>
        <button
          v-if="isLoggedIn && !isCreator"
          @click="applyCreator"
          class="btn-apply-creator"
        >
          {{ t('topic.applyCreator') }}
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="topics-filters">
      <!-- Category filter -->
      <div class="filter-group">
        <label>{{ t('topic.category') }}:</label>
        <div class="category-tabs">
          <button
            :class="['tab', selectedCategory === '' ? 'active' : '']"
            @click="selectCategory('')"
          >
            {{ t('topic.allCategories') }}
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
      </div>

      <!-- Sort filter -->
      <div class="filter-group">
        <label>{{ t('topic.sortBy') }}:</label>
        <select v-model="selectedSort" @change="handleSort">
          <option value="hot">{{ t('topic.sortHot') }}</option>
          <option value="newest">{{ t('topic.sortNewest') }}</option>
          <option value="expiring">{{ t('topic.sortExpiring') }}</option>
          <option value="volume">{{ t('topic.sortVolume') }}</option>
        </select>
      </div>
    </div>

    <!-- Topics Grid -->
    <div v-if="loading" class="loading">
      <p>{{ t('common.loading') }}</p>
    </div>

    <div v-else-if="topics.length === 0" class="empty-state">
      <p>{{ t('topic.noTopics') }}</p>
    </div>

    <div v-else class="topics-grid">
      <div
        v-for="topic in topics"
        :key="topic.id"
        class="topic-card"
        @click="goToTopic(topic.id)"
      >
        <div class="topic-card-header">
          <span :class="['category-tag', topic.category]">
            {{ getCategoryLabel(topic.category) }}
          </span>
          <span :class="['status-tag', topic.status]">
            {{ getStatusLabel(topic.status) }}
          </span>
        </div>

        <h3 class="topic-card-title">{{ topic.title }}</h3>
        <p class="topic-card-description">{{ topic.description }}</p>

        <div class="topic-card-stats">
          <div class="stat-item">
            <span class="stat-label">{{ t('topic.participants') }}</span>
            <span class="stat-value">{{ topic.participant_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ t('topic.volume') }}</span>
            <span class="stat-value">{{ formatNumber(topic.trade_volume) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">{{ t('topic.expires') }}</span>
            <span class="stat-value">{{ formatRelativeTime(topic.expires_at) }}</span>
          </div>
        </div>

        <!-- Market probabilities preview -->
        <div v-if="topic.current_prices && topic.current_prices.length > 0" class="probability-preview">
          <div
            v-for="(price, index) in topic.current_prices.slice(0, 2)"
            :key="index"
            class="probability-item"
          >
            <span class="outcome-name">{{ topic.outcome_options[index] }}</span>
            <span class="probability-value">{{ (price * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        {{ t('common.previous') }}
      </button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        {{ t('common.next') }}
      </button>
    </div>

    <!-- Create Topic Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ t('topic.create') }}</h2>
          <button class="modal-close" @click="closeModal">&times;</button>
        </div>

        <form @submit.prevent="handleCreateTopic" class="create-form">
          <div class="form-group">
            <label>{{ t('topic.title') }}</label>
            <input
              v-model="form.title"
              type="text"
              :placeholder="t('topic.titlePlaceholder')"
              required
              maxlength="200"
            />
          </div>

          <div class="form-group">
            <label>{{ t('topic.description') }}</label>
            <textarea
              v-model="form.description"
              :placeholder="t('topic.descriptionPlaceholder')"
              required
              maxlength="500"
              rows="4"
            ></textarea>
          </div>

          <div class="form-group">
            <label>{{ t('topic.category') }}</label>
            <select v-model="form.category" required>
              <option value="">{{ t('topic.selectCategory') }}</option>
              <option value="tech">{{ t('category.tech') }}</option>
              <option value="business">{{ t('category.business') }}</option>
              <option value="culture">{{ t('category.culture') }}</option>
              <option value="academic">{{ t('category.academic') }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>{{ t('topic.outcomeOptions') }}</label>
            <div class="outcomes-input">
              <input
                v-for="(option, index) in form.outcomes"
                :key="index"
                v-model="form.outcomes[index]"
                type="text"
                :placeholder="t('topic.outcomePlaceholder')"
                maxlength="100"
              />
              <button type="button" @click="addOutcome" class="btn-add-outcome">
                + {{ t('topic.addOutcome') }}
              </button>
            </div>
            <p class="form-hint">{{ t('topic.outcomeHint') }}</p>
          </div>

          <div class="form-group">
            <label>{{ t('topic.expiresAt') }}</label>
            <input
              v-model="form.expiresAt"
              type="datetime-local"
              required
              :min="minDate"
            />
          </div>

          <div v-if="formError" class="error-message">{{ formError }}</div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn-cancel">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="submitting">
              {{ submitting ? t('common.loading') : t('common.submit') }}
            </button>
          </div>
        </form>
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

interface Topic {
  id: string
  title: string
  description: string
  category: string
  outcome_options: string[]
  creator_id: string
  status: string
  expires_at: string
  participant_count: number
  trade_volume: number
  current_prices: number[] | null
  created_at: string
}

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const isLoggedIn = computed(() => authStore.isLoggedIn)

const loading = ref(true)
const topics = ref<Topic[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const total = ref(0)

const searchQuery = ref('')
const selectedCategory = ref('')
const selectedSort = ref('hot')

const categories = ['tech', 'business', 'culture', 'academic']

// Creator status
const isCreator = ref(false)
const creatorStatus = ref<string | null>(null)

const checkCreatorStatus = async () => {
  if (!isLoggedIn.value) {
    isCreator.value = false
    return
  }
  try {
    const response = await apiClient.get('/topics/creator/profile')
    creatorStatus.value = response.data.status
    isCreator.value = response.data.status === 'approved'
  } catch (e) {
    console.error('Failed to check creator status:', e)
    isCreator.value = false
  }
}

const applyCreator = () => {
  // TODO: Navigate to creator application page
  alert(t('topic.creatorRequired'))
}

// Create topic modal
const showCreateModal = ref(false)
const submitting = ref(false)
const formError = ref('')

const minDate = new Date().toISOString().slice(0, 16)

const form = ref({
  title: '',
  description: '',
  category: '',
  outcomes: ['', ''],
  expiresAt: '',
})

const addOutcome = () => {
  if (form.value.outcomes.length < 10) {
    form.value.outcomes.push('')
  }
}

const removeOutcome = (index: number) => {
  if (form.value.outcomes.length > 2) {
    form.value.outcomes.splice(index, 1)
  }
}

const closeModal = () => {
  showCreateModal.value = false
  form.value = {
    title: '',
    description: '',
    category: '',
    outcomes: ['', ''],
    expiresAt: '',
  }
  formError.value = ''
}

const handleCreateTopic = async () => {
  formError.value = ''

  // Validate form
  if (!form.value.title.trim()) {
    formError.value = t('topic.error.titleRequired')
    return
  }
  if (form.value.title.trim().length < 10) {
    formError.value = t('topic.error.titleMinLength')
    return
  }
  if (form.value.title.trim().length > 50) {
    formError.value = t('topic.error.titleMaxLength')
    return
  }
  if (!form.value.description.trim()) {
    formError.value = t('topic.error.descriptionRequired')
    return
  }
  if (form.value.description.trim().length < 50) {
    formError.value = t('topic.error.descriptionMinLength')
    return
  }
  if (form.value.description.trim().length > 500) {
    formError.value = t('topic.error.descriptionMaxLength')
    return
  }
  if (!form.value.category) {
    formError.value = t('topic.error.categoryRequired')
    return
  }

  // Filter empty outcomes and validate
  const outcomes = form.value.outcomes.filter(o => o.trim())
  if (outcomes.length < 2) {
    formError.value = t('topic.error.minOutcomes')
    return
  }
  if (outcomes.length > 10) {
    formError.value = t('topic.error.maxOutcomes')
    return
  }
  if (new Set(outcomes).size !== outcomes.length) {
    formError.value = t('topic.error.duplicateOutcomes')
    return
  }

  if (!form.value.expiresAt) {
    formError.value = t('topic.error.expiresAtRequired')
    return
  }

  const expiresDate = new Date(form.value.expiresAt)
  const oneDayFromNow = Date.now() + (24 * 60 * 60 * 1000)
  if (expiresDate.getTime() < oneDayFromNow) {
    formError.value = t('topic.error.expiresAtMinDays')
    return
  }

  const oneYearFromNow = Date.now() + (365 * 24 * 60 * 60 * 1000)
  if (expiresDate.getTime() > oneYearFromNow) {
    formError.value = t('topic.error.expiresAtMaxDays')
    return
  }

  submitting.value = true

  try {
    const response = await apiClient.post('/topics', {
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      category: form.value.category,
      outcome_options: outcomes,
      expires_at: expiresDate.toISOString(),
    })

    console.log('Topic created:', response.data)
    closeModal()
    loadTopics() // Reload topics list

    // Show success message
    alert(t('topic.createSuccess'))

    // Navigate to the new topic
    if (response.data.topic_id) {
      router.push(`/topics/${response.data.topic_id}`)
    }
  } catch (e: any) {
    console.error('Failed to create topic:', e)
    formError.value = e.response?.data?.detail || t('topic.error.createFailed')
  } finally {
    submitting.value = false
  }
}

const loadTopics = async () => {
  loading.value = true

  try {
    const params: Record<string, string | number> = {
      page: currentPage.value,
      limit: 20,
      sort: selectedSort.value,
    }

    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }

    const response = await apiClient.get('/topics', { params })
    const data = response.data

    topics.value = data.topics || []
    total.value = data.total || 0
    totalPages.value = Math.ceil(total.value / 20)
  } catch (e: any) {
    console.error('Failed to load topics:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadTopics()
}

const selectCategory = (category: string) => {
  selectedCategory.value = category
  currentPage.value = 1
  loadTopics()
}

const handleSort = () => {
  currentPage.value = 1
  loadTopics()
}

const goToTopic = (id: string) => {
  router.push(`/topics/${id}`)
}

const goToPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadTopics()
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

const formatRelativeTime = (dateStr: string): string => {
  const expires = new Date(dateStr)
  const now = new Date()
  const diff = expires.getTime() - now.getTime()

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days < 0) {
    return t('topic.expired')
  } else if (days === 0) {
    return t('topic.today')
  } else if (days === 1) {
    return t('topic.tomorrow')
  } else if (days <= 7) {
    return `${days} ${t('topic.days')}`
  } else {
    return expires.toLocaleDateString('vi-VN')
  }
}

onMounted(() => {
  loadTopics()
  checkCreatorStatus()
})
</script>

<style scoped>
.topics-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}

.topics-header {
  margin-bottom: 24px;
}

.topics-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-gray-900, #111827);
}

.search-box {
  display: flex;
  gap: 8px;
  max-width: 400px;
}

.search-box input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
}

.search-box input:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.search-box button {
  padding: 10px 20px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.topics-filters {
  margin-bottom: 24px;
}

.filter-group {
  margin-bottom: 16px;
}

.filter-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
}

.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-tabs .tab {
  padding: 8px 16px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  background: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.category-tabs .tab.active {
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border-color: var(--color-primary-500, #3b82f6);
}

.filter-group select {
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  min-width: 150px;
}

.loading, .empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--color-gray-500, #6b7280);
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.topic-card {
  border: 1px solid var(--color-gray-200, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.topic-card:hover {
  border-color: var(--color-primary-500, #3b82f6);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.topic-card-header {
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

.topic-card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-gray-900, #111827);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.topic-card-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 16px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.topic-card-stats {
  display: flex;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--color-gray-100, #f3f4f6);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
}

.probability-preview {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-gray-100, #f3f4f6);
}

.probability-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}

.outcome-name {
  color: var(--color-gray-600, #4b5563);
}

.probability-value {
  font-weight: 500;
  color: var(--color-primary-600, #2563eb);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding-top: 24px;
}

.pagination button {
  padding: 10px 20px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:not(:disabled):hover {
  background: var(--color-gray-50, #f9fafb);
}

.page-info {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-create:hover {
  background: var(--color-primary-600, #2563eb);
  transform: translateY(-1px);
}

.btn-create span {
  font-size: 18px;
  font-weight: 700;
}

.btn-apply-creator {
  padding: 10px 20px;
  background: var(--color-gray-200, #e5e7eb);
  color: var(--color-gray-700, #374151);
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-apply-creator:hover {
  background: var(--color-gray-300, #d1d5db);
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
  overflow-y: auto;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--color-gray-400, #9ca3af);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-600, #4b5563);
}

.create-form {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.outcomes-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-add-outcome {
  padding: 8px 16px;
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-700, #374151);
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  align-self: flex-start;
}

.btn-add-outcome:hover {
  background: var(--color-gray-200, #e5e7eb);
  border-color: var(--color-gray-400, #9ca3af);
}

.form-hint {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
  margin-top: 4px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-gray-200, #e5e7eb);
  margin-top: 8px;
}

.btn-cancel {
  padding: 10px 20px;
  background: white;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: var(--color-gray-50, #f9fafb);
  border-color: var(--color-gray-400, #9ca3af);
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
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-600, #2563eb);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  padding: 12px 16px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: none;
  }

  .btn-create {
    justify-content: center;
  }

  .modal {
    max-height: 100vh;
    border-radius: 0;
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .btn-cancel,
  .btn-submit {
    width: 100%;
  }
}
</style>

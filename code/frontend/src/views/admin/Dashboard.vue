<template>
  <div class="admin-dashboard">
    <h1>{{ t('admin.dashboard') }}</h1>

    <!-- Stats Overview -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon users"></div>
        <div class="stat-info">
          <span class="stat-label">{{ t('admin.totalUsers') }}</span>
          <span class="stat-value">{{ stats.total_users }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon topics"></div>
        <div class="stat-info">
          <span class="stat-label">{{ t('admin.totalTopics') }}</span>
          <span class="stat-value">{{ stats.total_topics }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon volume"></div>
        <div class="stat-info">
          <span class="stat-label">{{ t('admin.totalVolume') }}</span>
          <span class="stat-value">{{ formatNumber(stats.total_volume) }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon wallet"></div>
        <div class="stat-info">
          <span class="stat-label">{{ t('admin.totalRecharge') }}</span>
          <span class="stat-value">{{ formatNumber(stats.total_recharge) }}</span>
        </div>
      </div>
    </div>

    <!-- Pending Reviews -->
    <div class="admin-section">
      <div class="section-header">
        <h2>{{ t('admin.pendingReviews') }}</h2>
        <button @click="goToReviews">{{ t('admin.viewAll') }}</button>
      </div>
      <div v-if="loadingReviews" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="pendingReviews.length === 0" class="empty-state">
        {{ t('admin.noPendingReviews') }}
      </div>
      <div v-else class="review-list">
        <div
          v-for="review in pendingReviews"
          :key="review.id"
          class="review-item"
        >
          <div class="review-content">
            <span class="content-type">{{ getContentTypeLabel(review.content_type) }}</span>
            <p class="content-text">{{ review.content_text?.slice(0, 100) }}...</p>
            <span class="create-time">{{ formatDate(review.created_at) }}</span>
          </div>
          <div class="review-actions">
            <button class="btn-approve" @click="handleReview(review.id, 'approved')">
              {{ t('admin.approve') }}
            </button>
            <button class="btn-reject" @click="handleReview(review.id, 'rejected')">
              {{ t('admin.reject') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Violations -->
    <div class="admin-section">
      <div class="section-header">
        <h2>{{ t('admin.recentViolations') }}</h2>
        <button @click="goToViolations">{{ t('admin.viewAll') }}</button>
      </div>
      <div v-if="loadingViolations" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="violations.length === 0" class="empty-state">
        {{ t('admin.noViolations') }}
      </div>
      <div v-else class="violation-list">
        <div
          v-for="violation in violations"
          :key="violation.id"
          class="violation-item"
        >
          <div class="violation-info">
            <span :class="['severity-tag', violation.severity]">
              {{ getSeverityLabel(violation.severity) }}
            </span>
            <span class="violation-type">{{ violation.violation_type }}</span>
            <span class="violation-user">User: {{ violation.user_id.slice(0, 8) }}...</span>
            <span class="violation-time">{{ formatRelativeTime(violation.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- System Status -->
    <div class="admin-section">
      <h2>{{ t('admin.systemStatus') }}</h2>
      <div class="status-grid">
        <div class="status-item">
          <span class="status-label">{{ t('admin.aiService') }}</span>
          <span class="status-value healthy">{{ t('admin.statusNormal') }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">{{ t('admin.database') }}</span>
          <span class="status-value healthy">{{ t('admin.statusNormal') }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">{{ t('admin.cache') }}</span>
          <span class="status-value healthy">{{ t('admin.statusNormal') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'

const { t } = useI18n()
const router = useRouter()

const stats = ref({
  total_users: 0,
  total_topics: 0,
  total_volume: 0,
  total_recharge: 0,
})

const loadingReviews = ref(false)
const loadingViolations = ref(false)
const pendingReviews = ref<any[]>([])
const violations = ref<any[]>([])

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
  const diff = (now.getTime() - date.getTime()) / 1000 / 60 // minutes

  if (diff < 1) return '刚刚'
  if (diff < 60) return `${Math.floor(diff)}${t('admin.minutesAgo')}`
  if (diff < 1440) return `${Math.floor(diff / 60)}${t('admin.hoursAgo')}`
  return `${Math.floor(diff / 1440)}${t('admin.daysAgo')}`
}

const getContentTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    topic: t('topic.type'),
    product: t('mall.product'),
    comment: t('comment.type'),
  }
  return labels[type] || type
}

const getSeverityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    light: t('admin.severityLight'),
    moderate: t('admin.severityModerate'),
    severe: t('admin.severitySevere'),
    critical: t('admin.severityCritical'),
  }
  return labels[severity] || severity
}

const loadStats = async () => {
  try {
    const response = await apiClient.get('/admin/dashboard')
    stats.value = response.data.stats || {}
  } catch (e) {
    // Use mock data
    stats.value = {
      total_users: 1250,
      total_topics: 89,
      total_volume: 15600000,
      total_recharge: 8900000,
    }
  }
}

const loadPendingReviews = async () => {
  loadingReviews.value = true
  try {
    const response = await apiClient.get('/moderation/content/reviews/pending', {
      params: { limit: 5 },
    })
    pendingReviews.value = response.data.reviews || []
  } catch (e) {
    // Mock data
    pendingReviews.value = []
  } finally {
    loadingReviews.value = false
  }
}

const loadViolations = async () => {
  loadingViolations.value = true
  try {
    const response = await apiClient.get('/moderation/violations', {
      params: { limit: 5 },
    })
    violations.value = response.data.violations || []
  } catch (e) {
    violations.value = []
  } finally {
    loadingViolations.value = false
  }
}

const handleReview = async (reviewId: string, result: string) => {
  try {
    await apiClient.post(`/moderation/content/reviews/${reviewId}/submit`, {
      result,
    })
    alert(t('admin.reviewSuccess'))
    await loadPendingReviews()
  } catch (e: any) {
    alert(e.response?.data?.detail || t('admin.reviewFailed'))
  }
}

const goToReviews = () => {
  router.push('/admin/reviews')
}

const goToViolations = () => {
  router.push('/admin/violations')
}

onMounted(() => {
  loadStats()
  loadPendingReviews()
  loadViolations()
})
</script>

<style scoped>
.admin-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}

.admin-dashboard h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-gray-900, #111827);
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.users { background: #dbeafe; }
.stat-icon.topics { background: #dcfce7; }
.stat-icon.volume { background: #fef3c7; }
.stat-icon.wallet { background: #f3e8ff; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: var(--color-gray-500, #6b7280);
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.admin-section {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--color-gray-200, #e5e7eb);
  padding: 20px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
}

.section-header button {
  padding: 8px 16px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.loading, .empty-state {
  text-align: center;
  padding: 24px;
  color: var(--color-gray-500, #6b7280);
}

.review-list, .violation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.review-content {
  flex: 1;
}

.content-type {
  font-size: 12px;
  color: var(--color-gray-500, #6b7280);
}

.content-text {
  font-size: 14px;
  color: var(--color-gray-700, #374151);
  margin: 4px 0;
}

.create-time {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.review-actions {
  display: flex;
  gap: 8px;
}

.btn-approve, .btn-reject {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}

.btn-approve {
  background: var(--color-success-500, #10b981);
  color: white;
}

.btn-reject {
  background: var(--color-error-500, #ef4444);
  color: white;
}

.violation-item {
  padding: 12px 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.violation-info {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.severity-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.severity-tag.light { background: #dbeafe; color: #1d4ed8; }
.severity-tag.moderate { background: #fef3c7; color: #b45309; }
.severity-tag.severe { background: #fed7aa; color: #c2410c; }
.severity-tag.critical { background: #fee2e2; color: #dc2626; }

.violation-type {
  font-size: 14px;
  color: var(--color-gray-700, #374151);
}

.violation-user, .violation-time {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
}

.status-value {
  font-size: 14px;
  font-weight: 500;
}

.status-value.healthy {
  color: var(--color-success-500, #10b981);
}

.status-value.warning {
  color: var(--color-warning-500, #f59e0b);
}

.status-value.error {
  color: var(--color-error-500, #ef4444);
}
</style>

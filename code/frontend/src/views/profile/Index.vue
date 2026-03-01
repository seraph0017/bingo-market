<template>
  <div class="profile-page">
    <div class="profile-container">
      <h1>{{ t('profile.title') }}</h1>

      <div class="profile-content">
        <!-- Profile Avatar -->
        <div class="profile-avatar-section">
          <div class="avatar-placeholder">
            <span>{{ userAvatar }}</span>
          </div>
          <button class="btn-change-avatar">{{ t('profile.changeAvatar') }}</button>
        </div>

        <!-- Profile Form -->
        <form @submit.prevent="handleUpdateProfile" class="profile-form">
          <div class="form-section">
            <h2>{{ t('profile.basicInfo') }}</h2>

            <div class="form-group">
              <label>{{ t('profile.email') }}</label>
              <div class="input-with-status">
                <input
                  v-model="form.email"
                  type="email"
                  :disabled="!canEditEmail"
                />
                <span v-if="user?.email_verified" class="verified-badge">✓ {{ t('profile.verified') }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>{{ t('profile.phone') }}</label>
              <div class="input-with-status">
                <input
                  v-model="form.phone"
                  type="tel"
                  :disabled="!canEditPhone"
                />
                <span v-if="user?.phone_verified" class="verified-badge">✓ {{ t('profile.verified') }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>{{ t('profile.fullName') }}</label>
              <input
                v-model="form.full_name"
                type="text"
                :placeholder="t('profile.fullNamePlaceholder')"
              />
            </div>

            <div class="form-group">
              <label>{{ t('profile.dateOfBirth') }}</label>
              <input
                v-model="form.date_of_birth"
                type="date"
              />
            </div>

            <div class="form-group">
              <label>{{ t('profile.gender') }}</label>
              <select v-model="form.gender">
                <option value="">{{ t('profile.selectGender') }}</option>
                <option value="male">{{ t('profile.genderMale') }}</option>
                <option value="female">{{ t('profile.genderFemale') }}</option>
                <option value="other">{{ t('profile.genderOther') }}</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h2>{{ t('profile.security') }}</h2>

            <div class="security-item">
              <div class="security-info">
                <span class="security-label">{{ t('profile.password') }}</span>
                <span class="security-status">{{ t('profile.lastChanged') }}: {{ formatDate(lastPasswordChange) }}</span>
              </div>
              <button type="button" @click="showChangePassword = true" class="btn-secondary">
                {{ t('profile.changePassword') }}
              </button>
            </div>

            <div class="security-item">
              <div class="security-info">
                <span class="security-label">{{ t('profile.twoFactor') }}</span>
                <span :class="['security-status', twoFactorEnabled ? 'enabled' : 'disabled']">
                  {{ twoFactorEnabled ? t('profile.enabled') : t('profile.disabled') }}
                </span>
              </div>
              <button type="button" @click="toggleTwoFactor" class="btn-secondary">
                {{ twoFactorEnabled ? t('profile.disable') : t('profile.enable') }}
              </button>
            </div>
          </div>

          <div class="form-section">
            <h2>{{ t('profile.kycStatus') }}</h2>
            <div class="kyc-status">
              <div class="kyc-info">
                <span :class="['kyc-badge', kycStatusClass]">
                  {{ kycStatusLabel }}
                </span>
                <span v-if="kycVerifiedAt" class="kyc-time">
                  {{ t('profile.verifiedAt') }}: {{ formatDate(kycVerifiedAt) }}
                </span>
              </div>
              <router-link v-if="!isKycVerified" to="/kyc/verify" class="btn-primary">
                {{ t('profile.verifyNow') }}
              </router-link>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="form-actions">
            <button type="button" @click="handleCancel" class="btn-cancel">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="loading">
              {{ loading ? t('common.loading') : t('common.save') }}
            </button>
          </div>

          <!-- Message -->
          <div v-if="message" :class="['message', messageType]">
            {{ message }}
          </div>
        </form>
      </div>
    </div>

    <!-- Change Password Modal -->
    <div v-if="showChangePassword" class="modal-overlay" @click="showChangePassword = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>{{ t('profile.changePassword') }}</h2>
          <button class="modal-close" @click="showChangePassword = false">×</button>
        </div>
        <form @submit.prevent="handleChangePassword" class="password-form">
          <div class="form-group">
            <label>{{ t('profile.currentPassword') }}</label>
            <input
              v-model="passwordForm.currentPassword"
              type="password"
              required
            />
          </div>
          <div class="form-group">
            <label>{{ t('profile.newPassword') }}</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              required
              minlength="8"
            />
          </div>
          <div class="form-group">
            <label>{{ t('profile.confirmNewPassword') }}</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              required
            />
          </div>
          <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
          <div class="modal-actions">
            <button type="button" @click="showChangePassword = false" class="btn-cancel">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="passwordLoading">
              {{ passwordLoading ? t('common.loading') : t('common.confirm') }}
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

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const user = ref<any>(null)
const canEditEmail = ref(false)
const canEditPhone = ref(false)
const lastPasswordChange = ref<string | null>(null)
const twoFactorEnabled = ref(false)
const kycStatus = ref('unverified')
const kycVerifiedAt = ref<string | null>(null)

const form = ref({
  email: '',
  phone: '',
  full_name: '',
  date_of_birth: '',
  gender: '',
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordLoading = ref(false)
const passwordError = ref('')
const showChangePassword = ref(false)

const userAvatar = computed(() => {
  const name = form.value.full_name || user.value?.full_name || 'U'
  return name.charAt(0).toUpperCase()
})

const kycStatusClass = computed(() => {
  const classes: Record<string, string> = {
    unverified: 'unverified',
    pending: 'pending',
    verified: 'verified',
    rejected: 'rejected',
  }
  return classes[kycStatus.value] || 'unverified'
})

const kycStatusLabel = computed(() => {
  const labels: Record<string, string> = {
    unverified: t('profile.kycUnverified'),
    pending: t('profile.kycPending'),
    verified: t('profile.kycVerified'),
    rejected: t('profile.kycRejected'),
  }
  return labels[kycStatus.value] || t('profile.kycUnverified')
})

const isKycVerified = computed(() => kycStatus.value === 'verified')

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

const loadUserProfile = async () => {
  try {
    const response = await apiClient.get('/auth/me')
    user.value = response.data
    form.value.email = response.data.email || ''
    form.value.phone = response.data.phone || ''
    form.value.full_name = response.data.full_name || ''
    form.value.date_of_birth = response.data.date_of_birth || ''
    form.value.gender = response.data.gender || ''
    canEditEmail.value = !response.data.email_verified
    canEditPhone.value = !response.data.phone_verified
    lastPasswordChange.value = response.data.last_password_change
    twoFactorEnabled.value = response.data.two_factor_enabled || false
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

const loadKycStatus = async () => {
  try {
    const response = await apiClient.get('/auth/kyc/status')
    kycStatus.value = response.data.status || 'unverified'
    kycVerifiedAt.value = response.data.verified_at
  } catch (e) {
    // KYC status not available
  }
}

const handleUpdateProfile = async () => {
  loading.value = true
  message.value = ''

  try {
    await apiClient.put('/auth/me', {
      full_name: form.value.full_name,
      date_of_birth: form.value.date_of_birth,
      gender: form.value.gender,
    })

    message.value = t('profile.updateSuccess')
    messageType.value = 'success'
  } catch (e: any) {
    message.value = e.response?.data?.detail || t('profile.updateFailed')
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  router.back()
}

const handleChangePassword = async () => {
  passwordError.value = ''

  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = t('profile.passwordMismatch')
    return
  }

  if (passwordForm.value.newPassword.length < 8) {
    passwordError.value = t('profile.passwordTooShort')
    return
  }

  passwordLoading.value = true

  try {
    await apiClient.post('/auth/change-password', {
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword,
    })

    showChangePassword.value = false
    message.value = t('profile.passwordChanged')
    messageType.value = 'success'
    passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail || t('profile.passwordChangeFailed')
  } finally {
    passwordLoading.value = false
  }
}

const toggleTwoFactor = async () => {
  try {
    await apiClient.post('/auth/toggle-2fa', {
      enable: !twoFactorEnabled.value,
    })
    twoFactorEnabled.value = !twoFactorEnabled.value
  } catch (e) {
    alert(t('profile.twoFactorFailed'))
  }
}

onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadUserProfile()
  loadKycStatus()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--color-gray-50, #f9fafb);
  padding: 24px 16px;
}

.profile-container {
  max-width: 700px;
  margin: 0 auto;
}

.profile-container h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 24px;
}

.profile-content {
  background: white;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.profile-avatar-section {
  text-align: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
}

.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 40px;
  font-weight: 600;
  color: white;
}

.btn-change-avatar {
  padding: 8px 16px;
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-700, #374151);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-gray-100, #f3f4f6);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
  margin-bottom: 6px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.form-group input:disabled {
  background: var(--color-gray-100, #f3f4f6);
  cursor: not-allowed;
}

.input-with-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-with-status input {
  flex: 1;
}

.verified-badge {
  font-size: 12px;
  color: var(--color-success-500, #10b981);
  font-weight: 500;
  white-space: nowrap;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-gray-100, #f3f4f6);
}

.security-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.security-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
}

.security-status {
  font-size: 13px;
  color: var(--color-gray-400, #9ca3af);
}

.security-status.enabled {
  color: var(--color-success-500, #10b981);
}

.security-status.disabled {
  color: var(--color-gray-400, #9ca3af);
}

.kyc-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kyc-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kyc-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

.kyc-badge.unverified {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-gray-600, #4b5563);
}

.kyc-badge.pending {
  background: #fef3c7;
  color: #b45309;
}

.kyc-badge.verified {
  background: #dcfce7;
  color: #15803d;
}

.kyc-badge.rejected {
  background: #fee2e2;
  color: #dc2626;
}

.kyc-time {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.btn-primary {
  padding: 8px 16px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--color-primary-600, #2563eb);
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
  border-color: var(--color-gray-400, #9ca3af);
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--color-gray-200, #e5e7eb);
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

.message {
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.message.success {
  background: #dcfce7;
  border: 1px solid #bbf7d0;
  color: #15803d;
}

.message.error {
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #dc2626;
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
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-gray-400, #9ca3af);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

@media (max-width: 640px) {
  .profile-content {
    padding: 24px 16px;
  }

  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn-cancel,
  .btn-submit {
    width: 100%;
  }
}
</style>

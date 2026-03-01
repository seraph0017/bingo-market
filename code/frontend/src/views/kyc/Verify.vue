<template>
  <div class="kyc-verify-page">
    <div class="kyc-container">
      <div class="kyc-header">
        <h1>{{ t('kyc.title') }}</h1>
        <p class="kyc-description">{{ t('kyc.description') }}</p>
      </div>

      <!-- Already verified -->
      <div v-if="isVerified" class="verified-state">
        <div class="success-icon">✓</div>
        <h2>{{ t('kyc.verified') }}</h2>
        <p>{{ t('kyc.verifiedDescription') }}</p>
        <router-link to="/wallet" class="btn-primary">
          {{ t('kyc.goToWallet') }}
        </router-link>
      </div>

      <!-- Verification form -->
      <div v-else-if="!submitted" class="verification-form">
        <form @submit.prevent="handleSubmit" class="kyc-form">
          <!-- Full Name -->
          <div class="form-group">
            <label>{{ t('kyc.fullName') }} <span class="required">*</span></label>
            <input
              v-model="form.full_name"
              type="text"
              :placeholder="t('kyc.fullNamePlaceholder')"
              required
              :disabled="loading"
            />
            <span class="hint">{{ t('kyc.fullNameHint') }}</span>
          </div>

          <!-- ID Type -->
          <div class="form-group">
            <label>{{ t('kyc.idType') }} <span class="required">*</span></label>
            <select v-model="form.id_type" required :disabled="loading">
              <option value="">{{ t('kyc.selectIdType') }}</option>
              <option value="citizen_id">{{ t('kyc.idTypeCitizen') }}</option>
              <option value="passport">{{ t('kyc.idTypePassport') }}</option>
              <option value="residence_card">{{ t('kyc.idTypeResidence') }}</option>
            </select>
          </div>

          <!-- ID Number -->
          <div class="form-group">
            <label>{{ t('kyc.idNumber') }} <span class="required">*</span></label>
            <input
              v-model="form.id_number"
              type="text"
              :placeholder="t('kyc.idNumberPlaceholder')"
              required
              :disabled="loading"
              maxlength="20"
            />
          </div>

          <!-- Date of Birth -->
          <div class="form-group">
            <label>{{ t('kyc.dateOfBirth') }} <span class="required">*</span></label>
            <input
              v-model="form.date_of_birth"
              type="date"
              required
              :max="maxDate"
              :disabled="loading"
            />
            <span class="hint">{{ t('kyc.ageRequirement') }}</span>
          </div>

          <!-- Phone Number -->
          <div class="form-group">
            <label>{{ t('kyc.phoneNumber') }} <span class="required">*</span></label>
            <input
              v-model="form.phone"
              type="tel"
              :placeholder="t('kyc.phoneNumberPlaceholder')"
              required
              :disabled="loading"
            />
          </div>

          <!-- Address -->
          <div class="form-group">
            <label>{{ t('kyc.address') }}</label>
            <textarea
              v-model="form.address"
              :placeholder="t('kyc.addressPlaceholder')"
              rows="3"
              :disabled="loading"
            ></textarea>
          </div>

          <!-- Upload ID Front -->
          <div class="form-group">
            <label>{{ t('kyc.idFront') }} <span class="required">*</span></label>
            <div class="upload-area" @click="triggerUpload('front')" @drop.prevent="handleDrop('front', $event)" @dragover.prevent>
              <div v-if="uploads.front" class="upload-preview">
                <img :src="uploads.front.preview" alt="ID Front" />
                <button type="button" @click.stop="removeUpload('front')" class="remove-btn">×</button>
              </div>
              <div v-else class="upload-placeholder">
                <span class="upload-icon">📷</span>
                <span>{{ t('kyc.uploadIdFront') }}</span>
              </div>
            </div>
            <span class="hint">{{ t('kyc.uploadHint') }}</span>
          </div>

          <!-- Upload ID Back -->
          <div class="form-group">
            <label>{{ t('kyc.idBack') }} <span class="required">*</span></label>
            <div class="upload-area" @click="triggerUpload('back')" @drop.prevent="handleDrop('back', $event)" @dragover.prevent>
              <div v-if="uploads.back" class="upload-preview">
                <img :src="uploads.back.preview" alt="ID Back" />
                <button type="button" @click.stop="removeUpload('back')" class="remove-btn">×</button>
              </div>
              <div v-else class="upload-placeholder">
                <span class="upload-icon">📷</span>
                <span>{{ t('kyc.uploadIdBack') }}</span>
              </div>
            </div>
            <span class="hint">{{ t('kyc.uploadHint') }}</span>
          </div>

          <!-- Selfie with ID -->
          <div class="form-group">
            <label>{{ t('kyc.selfieWithId') }} <span class="required">*</span></label>
            <div class="upload-area" @click="triggerUpload('selfie')" @drop.prevent="handleDrop('selfie', $event)" @dragover.prevent>
              <div v-if="uploads.selfie" class="upload-preview">
                <img :src="uploads.selfie.preview" alt="Selfie with ID" />
                <button type="button" @click.stop="removeUpload('selfie')" class="remove-btn">×</button>
              </div>
              <div v-else class="upload-placeholder">
                <span class="upload-icon">📷</span>
                <span>{{ t('kyc.uploadSelfie') }}</span>
              </div>
            </div>
            <span class="hint">{{ t('kyc.selfieHint') }}</span>
          </div>

          <!-- Terms Agreement -->
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.agree_privacy" required />
              <span>{{ t('kyc.agreePrivacy') }}</span>
            </label>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button type="submit" class="btn-submit" :disabled="loading || !canSubmit">
            {{ loading ? t('common.loading') : t('kyc.submit') }}
          </button>
        </form>
      </div>

      <!-- Submitted, pending review -->
      <div v-else-if="isPending" class="pending-state">
        <div class="pending-icon">⏳</div>
        <h2>{{ t('kyc.pendingReview') }}</h2>
        <p>{{ t('kyc.pendingDescription') }}</p>
        <p class="pending-time">{{ t('kyc.reviewTimeframe') }}</p>
      </div>

      <!-- Rejected -->
      <div v-else-if="isRejected" class="rejected-state">
        <div class="error-icon">✗</div>
        <h2>{{ t('kyc.rejected') }}</h2>
        <p class="rejection-reason">{{ t('kyc.rejectionReason') }}: {{ rejectionReason }}</p>
        <button @click="handleResubmit" class="btn-primary">
          {{ t('kyc.resubmit') }}
        </button>
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
const submitted = ref(false)
const error = ref<string | null>(null)

const isVerified = ref(false)
const isPending = ref(false)
const isRejected = ref(false)
const rejectionReason = ref('')

const maxDate = new Date()
maxDate.setFullYear(maxDate.getFullYear() - 18)

const form = ref({
  full_name: '',
  id_type: '',
  id_number: '',
  date_of_birth: '',
  phone: '',
  address: '',
  agree_privacy: false,
})

const uploads = ref<{
  front: { file: File; preview: string } | null
  back: { file: File; preview: string } | null
  selfie: { file: File; preview: string } | null
}>({
  front: null,
  back: null,
  selfie: null,
})

const canSubmit = computed(() => {
  return (
    form.value.full_name.trim() &&
    form.value.id_type &&
    form.value.id_number.trim() &&
    form.value.date_of_birth &&
    form.value.phone.trim() &&
    form.value.agree_privacy &&
    uploads.value.front &&
    uploads.value.back &&
    uploads.value.selfie
  )
})

const triggerUpload = (type: 'front' | 'back' | 'selfie') => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      handleFileSelect(type, file)
    }
  }
  input.click()
}

const handleFileSelect = (type: 'front' | 'back' | 'selfie', file: File) => {
  if (file.size > 5 * 1024 * 1024) {
    error.value = t('kyc.fileSizeLimit')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    uploads.value[type] = {
      file,
      preview: e.target?.result as string,
    }
    error.value = null
  }
  reader.readAsDataURL(file)
}

const handleDrop = (type: 'front' | 'back' | 'selfie', event: DragEvent) => {
  const file = event.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) {
    handleFileSelect(type, file)
  }
}

const removeUpload = (type: 'front' | 'back' | 'selfie') => {
  uploads.value[type] = null
}

const handleSubmit = async () => {
  if (!canSubmit.value) {
    error.value = t('kyc.fillAllRequired')
    return
  }

  loading.value = true
  error.value = null

  try {
    // Create FormData for file upload
    const formData = new FormData()
    formData.append('full_name', form.value.full_name.trim())
    formData.append('id_type', form.value.id_type)
    formData.append('id_number', form.value.id_number.trim())
    formData.append('date_of_birth', form.value.date_of_birth)
    formData.append('phone', form.value.phone.trim())
    formData.append('address', form.value.address.trim())
    formData.append('agree_privacy', String(form.value.agree_privacy))

    if (uploads.value.front) formData.append('id_front', uploads.value.front.file)
    if (uploads.value.back) formData.append('id_back', uploads.value.back.file)
    if (uploads.value.selfie) formData.append('selfie', uploads.value.selfie.file)

    await apiClient.post('/auth/kyc/submit', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    submitted.value = true
    isPending.value = true
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('kyc.submitFailed')
  } finally {
    loading.value = false
  }
}

const handleResubmit = () => {
  isRejected.value = false
  submitted.value = false
}

const loadKycStatus = async () => {
  try {
    const response = await apiClient.get('/auth/kyc/status')
    const status = response.data.status

    if (status === 'verified' || status === 'verified_18plus') {
      isVerified.value = true
    } else if (status === 'pending' || status === 'under_review') {
      submitted.value = true
      isPending.value = true
    } else if (status === 'rejected') {
      submitted.value = true
      isRejected.value = true
      rejectionReason.value = response.data.rejection_reason || t('kyc.unspecified')
    }
  } catch (e) {
    // KYC not submitted yet or error loading status
  }
}

onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadKycStatus()
})
</script>

<style scoped>
.kyc-verify-page {
  min-height: 100vh;
  background: var(--color-gray-50, #f9fafb);
  padding: 24px 16px;
}

.kyc-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.kyc-header {
  text-align: center;
  margin-bottom: 32px;
}

.kyc-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gray-900, #111827);
  margin-bottom: 8px;
}

.kyc-description {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
}

.verified-state,
.pending-state,
.rejected-state {
  text-align: center;
  padding: 48px 24px;
}

.success-icon,
.pending-icon,
.error-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.success-icon {
  color: var(--color-success-500, #10b981);
}

.pending-icon {
  color: var(--color-warning-500, #f59e0b);
}

.error-icon {
  color: var(--color-error-500, #ef4444);
}

.verified-state h2,
.pending-state h2,
.rejected-state h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-gray-900, #111827);
}

.verified-state p,
.pending-state p {
  font-size: 14px;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 24px;
}

.pending-time {
  font-size: 13px;
  color: var(--color-gray-400, #9ca3af);
}

.rejection-reason {
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  margin-bottom: 24px;
  padding: 12px;
  background: var(--color-gray-50, #f9fafb);
  border-radius: 8px;
}

.btn-primary {
  display: inline-block;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--color-primary-600, #2563eb);
}

.kyc-form {
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

.required {
  color: var(--color-error-500, #ef4444);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.hint {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.upload-area {
  border: 2px dashed var(--color-gray-300, #d1d5db);
  border-radius: 12px;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: var(--color-primary-500, #3b82f6);
  background: var(--color-primary-50, #eff6ff);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--color-gray-400, #9ca3af);
}

.upload-icon {
  font-size: 32px;
}

.upload-preview {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 8px;
}

.upload-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  cursor: pointer;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

.btn-submit {
  padding: 14px;
  background: var(--color-primary-500, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-600, #2563eb);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .kyc-container {
    padding: 24px 16px;
  }

  .kyc-header h1 {
    font-size: 20px;
  }

  .upload-area {
    min-height: 100px;
  }
}
</style>

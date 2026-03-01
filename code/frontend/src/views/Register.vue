<template>
  <div class="register-page">
    <div class="register-container">
      <h1>{{ t('navigation.register') }}</h1>
      <p class="subtitle">{{ t('register.subtitle') }}</p>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label>{{ t('register.phoneOrEmail') }}</label>
          <select v-model="registerType" class="register-type">
            <option value="phone">{{ t('register.phone') }}</option>
            <option value="email">{{ t('register.email') }}</option>
          </select>
          <input
            v-model="form.identifier"
            :type="registerType === 'phone' ? 'tel' : 'email'"
            :placeholder="registerType === 'phone' ? t('register.phonePlaceholder') : t('register.emailPlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label>{{ t('register.password') }}</label>
          <input
            v-model="form.password"
            type="password"
            :placeholder="t('register.passwordPlaceholder')"
            required
            minlength="8"
          />
          <span class="hint">{{ t('register.passwordHint') }}</span>
        </div>

        <div class="form-group">
          <label>{{ t('register.confirmPassword') }}</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            :placeholder="t('register.confirmPasswordPlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label>{{ t('register.fullName') }}</label>
          <input
            v-model="form.fullName"
            type="text"
            :placeholder="t('register.fullNamePlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.agreeTerms" required />
            <span>{{ t('register.agreeTerms') }} <a href="#">{{ t('register.termsLink') }}</a></span>
          </label>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.confirmAge" required />
            <span>{{ t('register.confirmAge') }}</span>
          </label>
        </div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? t('common.loading') : t('navigation.register') }}
        </button>

        <div class="form-footer">
          <p>{{ t('register.haveAccount') }} <router-link to="/login">{{ t('navigation.login') }}</router-link></p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const registerType = ref<'phone' | 'email'>('phone')

const form = ref({
  identifier: '',
  password: '',
  confirmPassword: '',
  fullName: '',
  agreeTerms: false,
  confirmAge: false,
})

const handleRegister = async () => {
  loading.value = true
  error.value = null
  success.value = null

  // Validate passwords match
  if (form.value.password !== form.value.confirmPassword) {
    error.value = t('register.passwordMismatch')
    loading.value = false
    return
  }

  // Validate password length
  if (form.value.password.length < 8) {
    error.value = t('register.passwordTooShort')
    loading.value = false
    return
  }

  try {
    const registerData: Record<string, string> = {
      password: form.value.password,
      full_name: form.value.fullName,
    }

    if (registerType.value === 'phone') {
      registerData.phone = form.value.identifier
    } else {
      registerData.email = form.value.identifier
    }

    const response = await apiClient.post('/auth/register', registerData)

    success.value = t('register.success')

    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('register.error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.register-container h1 {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 8px;
  color: var(--color-gray-900, #111827);
}

.subtitle {
  text-align: center;
  color: var(--color-gray-500, #6b7280);
  margin-bottom: 32px;
}

.register-form {
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
  color: var(--color-gray-700, #374151);
}

.register-type {
  padding: 10px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 8px;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}

.hint {
  font-size: 12px;
  color: var(--color-gray-400, #9ca3af);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--color-gray-600, #4b5563);
  cursor: pointer;
  font-size: 14px;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  cursor: pointer;
}

.checkbox-label a {
  color: var(--color-primary-500, #3b82f6);
  text-decoration: none;
}

.btn-submit {
  margin-top: 8px;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-submit:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: var(--color-gray-600, #4b5563);
  margin-top: 8px;
}

.form-footer a {
  color: var(--color-primary-500, #3b82f6);
  text-decoration: none;
  font-weight: 500;
}

.form-footer a:hover {
  text-decoration: underline;
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

.success-message {
  padding: 12px;
  background: #dcfce7;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #15803d;
  font-size: 14px;
  text-align: center;
}
</style>

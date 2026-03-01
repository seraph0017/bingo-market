<template>
  <div class="login-page">
    <div class="login-container">
      <h1>{{ t('navigation.login') }}</h1>
      <p class="subtitle">{{ t('login.subtitle') }}</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>{{ t('login.phoneOrEmail') }}</label>
          <input
            v-model="form.identifier"
            type="text"
            :placeholder="t('login.phoneOrEmailPlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label>{{ t('login.password') }}</label>
          <input
            v-model="form.password"
            type="password"
            :placeholder="t('login.passwordPlaceholder')"
            required
          />
        </div>

        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.rememberMe" />
            {{ t('login.rememberMe') }}
          </label>
          <a href="#" class="forgot-link">{{ t('login.forgotPassword') }}</a>
        </div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? t('common.loading') : t('navigation.login') }}
        </button>

        <div class="form-footer">
          <p>{{ t('login.noAccount') }} <router-link to="/register">{{ t('navigation.register') }}</router-link></p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)

const form = ref({
  identifier: '',
  password: '',
  rememberMe: false,
})

const handleLogin = async () => {
  loading.value = true
  error.value = null

  try {
    // Determine if identifier is phone or email
    const isPhone = /^\d+$/.test(form.value.identifier)
    const loginData: Record<string, string> = {
      password: form.value.password,
    }

    if (isPhone) {
      loginData.phone = form.value.identifier
    } else {
      loginData.email = form.value.identifier
    }

    const response = await apiClient.post('/auth/login', loginData)

    // Store token
    authStore.setToken(response.data.token)

    // Get user info and store it
    try {
      const userResponse = await apiClient.get('/auth/me')
      authStore.setUser(userResponse.data)
      console.log('Login successful:', userResponse.data.email)
    } catch (e) {
      console.error('Failed to get user info:', e)
      // Clear token if we can't get user info
      authStore.logout()
      error.value = 'Failed to retrieve user information'
      loading.value = false
      return
    }

    // Redirect to home or intended page
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('login.error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-container h1 {
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-gray-600, #4b5563);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.forgot-link {
  color: var(--color-primary-500, #3b82f6);
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.btn-submit {
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
</style>

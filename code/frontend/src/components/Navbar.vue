<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/" class="nav-logo">
        <span class="logo-icon">🎯</span>
        <span class="logo-text">Bingo Market</span>
      </router-link>

      <div class="nav-links">
        <router-link to="/topics" class="nav-link">
          <span class="link-icon">📊</span>
          <span class="link-text">{{ t('navigation.topics') }}</span>
        </router-link>
        <router-link to="/mall" class="nav-link">
          <span class="link-icon">🎁</span>
          <span class="link-text">{{ t('navigation.mall') }}</span>
        </router-link>
        <router-link to="/wallet" class="nav-link" v-if="isLoggedIn">
          <span class="link-icon">👛</span>
          <span class="link-text">{{ t('navigation.wallet') }}</span>
        </router-link>
        <router-link to="/admin" class="nav-link" v-if="isAdmin">
          <span class="link-icon">⚙️</span>
          <span class="link-text">{{ t('navigation.admin') }}</span>
        </router-link>
      </div>

      <div class="nav-actions">
        <template v-if="isLoggedIn">
          <span class="user-balance">{{ balance }} {{ t('common.coins') }}</span>
          <button @click="logout" class="btn-logout">{{ t('navigation.logout') }}</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-login">{{ t('navigation.login') }}</router-link>
          <router-link to="/register" class="btn-register">{{ t('navigation.register') }}</router-link>
        </template>
      </div>
    </div>
  </nav>
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

const balance = ref(0)

const isLoggedIn = computed(() => authStore.isLoggedIn)
const isAdmin = computed(() => authStore.user?.role === 'admin')

const loadWallet = async () => {
  if (isLoggedIn.value && authStore.token) {
    try {
      const response = await apiClient.get('/wallet')
      balance.value = response.data.balance || 0
    } catch (e) {
      // Ignore error - wallet info is not critical
      console.log('Wallet info not loaded')
    }
  }
}

const logout = () => {
  authStore.logout()
  router.push({ name: 'home' })
}

onMounted(() => {
  loadWallet()
})
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--color-gray-900, #111827);
  font-weight: 700;
  font-size: 18px;
}

.logo-icon {
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: 8px;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--color-gray-600, #4b5563);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--color-gray-100, #f3f4f6);
  color: var(--color-primary-600, #2563eb);
}

.nav-link.router-link-active {
  background: var(--color-primary-50, #eff6ff);
  color: var(--color-primary-600, #2563eb);
}

.link-icon {
  font-size: 16px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-balance {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary-600, #2563eb);
  padding: 8px 12px;
  background: var(--color-primary-50, #eff6ff);
  border-radius: 8px;
}

.btn-login, .btn-register {
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-login {
  color: var(--color-gray-700, #374151);
}

.btn-login:hover {
  color: var(--color-primary-600, #2563eb);
}

.btn-register {
  background: var(--color-primary-500, #3b82f6);
  color: white;
}

.btn-register:hover {
  background: var(--color-primary-600, #2563eb);
}

.btn-logout {
  padding: 8px 16px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gray-700, #374151);
  transition: all 0.2s;
}

.btn-logout:hover {
  border-color: var(--color-gray-400, #9ca3af);
  background: var(--color-gray-50, #f9fafb);
}

@media (max-width: 768px) {
  .nav-container {
    flex-wrap: wrap;
  }

  .nav-links {
    order: 3;
    width: 100%;
    justify-content: center;
    padding-top: 12px;
    border-top: 1px solid var(--color-gray-200, #e5e7eb);
  }

  .nav-link .link-text {
    display: none;
  }

  .nav-actions {
    margin-left: auto;
  }

  .user-balance {
    display: none;
  }
}
</style>

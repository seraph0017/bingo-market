<template>
  <div class="app">
    <Navbar />
    <LanguageSwitcher />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/api'

const authStore = useAuthStore()

// Restore user info on app mount if token exists but user is missing
onMounted(async () => {
  if (authStore.isLoggedIn) {
    if (!authStore.user) {
      // Token exists but user info is missing, try to restore
      try {
        const userResponse = await apiClient.get('/auth/me')
        authStore.setUser(userResponse.data)
        console.log('User info restored:', userResponse.data.email)
      } catch (e) {
        console.error('Failed to restore user info, token may be invalid')
        // Token might be invalid, clear it
        authStore.logout()
      }
    } else {
      // User info exists, verify token is still valid
      console.log('User already logged in:', authStore.user?.email)
      try {
        await apiClient.get('/auth/me')
        console.log('Token verified')
      } catch (e) {
        console.error('Token expired, clearing auth state')
        authStore.logout()
      }
    }
  }
})
</script>

<style lang="scss">
.app {
  min-height: 100vh;
  background: var(--color-gray-50, #f9fafb);
}

.main-content {
  padding-bottom: 40px;
}
</style>

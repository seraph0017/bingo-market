import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // Initialize from localStorage
  const storedToken = localStorage.getItem('token')
  const storedUser = localStorage.getItem('user')

  // Parse user safely
  let parsedUser: any = null
  if (storedUser) {
    try {
      parsedUser = JSON.parse(storedUser)
    } catch (e) {
      console.error('Failed to parse user from localStorage:', e)
      localStorage.removeItem('user')
    }
  }

  console.log('[Auth Store] Initializing...', {
    hasToken: !!storedToken,
    hasUser: !!parsedUser,
    tokenPreview: storedToken ? storedToken.substring(0, 20) + '...' : null,
  })

  const token = ref<string | null>(storedToken)
  const user = ref<any | null>(parsedUser)

  const isLoggedIn = computed(() => !!token.value)

  const setToken = (newToken: string) => {
    console.log('[Auth Store] Setting token')
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (userData: any) => {
    console.log('[Auth Store] Setting user:', userData.email)
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = () => {
    console.log('[Auth Store] Logging out')
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // Watch for token changes and clear user if token is removed
  watch(token, (newToken) => {
    if (!newToken) {
      console.log('[Auth Store] Token cleared, removing user')
      user.value = null
      localStorage.removeItem('user')
    }
  })

  return {
    token,
    user,
    isLoggedIn,
    setToken,
    setUser,
    logout,
  }
})

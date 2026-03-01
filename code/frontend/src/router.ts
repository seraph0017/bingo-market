import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue'),
  },
  {
    path: '/wallet',
    name: 'wallet',
    component: () => import('@/views/Wallet.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/topics',
    name: 'topics',
    component: () => import('@/views/Topics.vue'),
  },
  {
    path: '/topics/:id',
    name: 'topic-detail',
    component: () => import('@/views/TopicDetail.vue'),
  },
  {
    path: '/mall',
    name: 'mall',
    component: () => import('@/views/Mall.vue'),
  },
  {
    path: '/settlements',
    name: 'settlements',
    component: () => import('@/views/settlement/List.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settlements/:id',
    name: 'settlement-detail',
    component: () => import('@/views/settlement/Detail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/profile/Index.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/kyc/verify',
    name: 'kyc-verify',
    component: () => import('@/views/kyc/Verify.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/trading/positions',
    name: 'trading-positions',
    component: () => import('@/views/trading/Positions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  let user: any = null
  if (userStr) {
    try {
      user = JSON.parse(userStr)
    } catch (e) {
      console.error('Failed to parse user from localStorage:', e)
      localStorage.removeItem('user')
    }
  }

  if (to.meta.requiresAuth && !token) {
    next({ name: 'login' })
  } else if (to.meta.requiresAdmin && (!token || user?.role !== 'admin')) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router

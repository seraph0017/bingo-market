<template>
  <div class="home">
    <main class="main">
      <section class="hero">
        <h2>{{ t('home.welcome') }}</h2>
        <p>{{ t('home.description') }}</p>
        <router-link to="/topics" class="btn-primary">
          {{ t('home.explore_topics') }}
        </router-link>
      </section>

      <section class="features">
        <div class="feature-card">
          <h3>{{ t('home.features.predict.title') }}</h3>
          <p>{{ t('home.features.predict.description') }}</p>
        </div>
        <div class="feature-card">
          <h3>{{ t('home.features.earn.title') }}</h3>
          <p>{{ t('home.features.earn.description') }}</p>
        </div>
        <div class="feature-card">
          <h3>{{ t('home.features.redeem.title') }}</h3>
          <p>{{ t('home.features.redeem.description') }}</p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const isLoggedIn = computed(() => authStore.isLoggedIn)

const logout = () => {
  authStore.logout()
  router.push({ name: 'home' })
}
</script>

<style scoped lang="scss">
.home {
  min-height: 100vh;
}

.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 16px;
}

.hero {
  text-align: center;
  padding: 80px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 24px;
  color: white;
  margin-bottom: 48px;

  h2 {
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 16px;
    letter-spacing: -0.5px;
  }

  p {
    font-size: 18px;
    opacity: 0.95;
    margin-bottom: 32px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }
}

.btn-primary {
  display: inline-block;
  background: white;
  color: #667eea;
  padding: 14px 32px;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.feature-card {
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    border-color: #667eea;
  }

  h3 {
    margin-bottom: 12px;
    color: #667eea;
    font-size: 20px;
    font-weight: 600;
  }

  p {
    color: #6b7280;
    font-size: 15px;
    line-height: 1.6;
  }
}

@media (max-width: 768px) {
  .main {
    padding: 24px 16px;
  }

  .hero {
    padding: 48px 20px;
    margin-bottom: 32px;

    h2 {
      font-size: 28px;
    }

    p {
      font-size: 16px;
    }
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>

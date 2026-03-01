<template>
  <div class="language-switcher">
    <select v-model="currentLocale" @change="changeLanguage">
      <option value="vi">🇻🇳 Tiếng Việt</option>
      <option value="en">🇬🇧 English</option>
      <option value="zh">🇨🇳 中文</option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const currentLocale = ref(locale.value)

const changeLanguage = () => {
  locale.value = currentLocale.value
  localStorage.setItem('locale', currentLocale.value)
}

onMounted(() => {
  const savedLocale = localStorage.getItem('locale')
  if (savedLocale && ['vi', 'en', 'zh'].includes(savedLocale)) {
    currentLocale.value = savedLocale
    locale.value = savedLocale
  }
})
</script>

<style scoped>
.language-switcher {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
}

.language-switcher select {
  padding: 8px 12px;
  border: 1px solid var(--color-gray-300, #d1d5db);
  border-radius: 8px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.language-switcher select:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
}
</style>

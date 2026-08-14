<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { tandaiMasuk } from '@/router'

const router = useRouter()

function sesiHabis() {
  tandaiMasuk(false)
  if (router.currentRoute.value.name !== 'masuk') router.push({ name: 'masuk' })
}

onMounted(() => window.addEventListener('sesi-habis', sesiHabis))
onUnmounted(() => window.removeEventListener('sesi-habis', sesiHabis))
</script>

<template>
  <router-view />
</template>

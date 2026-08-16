<script setup>
import { ref } from 'vue'

// 10 kepingan, ukuran dan bentuk berbeda, jatuh 3.2–4.5 detik sambil berputar
const WARNA = ['#2BA8A2', '#FFD23F', '#EF6C4A', '#5DADE2', '#3CC4BD', '#FFE47A']
const keping = ref([])

function rayakan() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  keping.value = Array.from({ length: 10 }, (_, i) => ({
    id: Date.now() + i,
    kiri: Math.random() * 100,
    lebar: 6 + Math.random() * 8,
    tinggi: 6 + Math.random() * 14,
    warna: WARNA[i % WARNA.length],
    bulat: Math.random() > 0.5,
    lama: 3.2 + Math.random() * 1.3,
    tunda: Math.random() * 0.4
  }))
  setTimeout(() => (keping.value = []), 5200)
}

defineExpose({ rayakan })
</script>

<template>
  <div class="konfeti" aria-hidden="true">
    <span v-for="k in keping" :key="k.id" class="konfeti__keping"
          :style="{
            left: k.kiri + '%',
            width: k.lebar + 'px',
            height: k.tinggi + 'px',
            background: k.warna,
            borderRadius: k.bulat ? '50%' : '2px',
            animationDuration: k.lama + 's',
            animationDelay: k.tunda + 's'
          }" />
  </div>
</template>

<style scoped>
.konfeti { position: fixed; inset: 0; pointer-events: none; z-index: 3000; overflow: hidden; }
.konfeti__keping { position: absolute; top: -20px; animation: konfeti-jatuh linear forwards; }
</style>

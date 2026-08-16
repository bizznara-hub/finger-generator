<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, jalankan } from '@/api'
import { tandaiMasuk } from '@/router'

const route = useRoute(); const router = useRouter()
const form = ref({ username: '', sandi: '' })
const sibuk = ref(false)

async function kirim() {
  sibuk.value = true
  try {
    await jalankan(() => api.post('/masuk', form.value), { sukses: 'Selamat datang.' })
    tandaiMasuk(true)
    router.push(route.query.lanjut || '/')
  } finally { sibuk.value = false }
}
</script>

<template>
  <div class="masuk">
    <form class="masuk__kotak" @submit.prevent="kirim">
      <span class="masuk__logo"><iconify-icon icon="lucide:fingerprint" width="22" /></span>
      <h1>Absensi FK</h1>
      <p class="masuk__sub">Fakultas Kedokteran Universitas Hasanuddin</p>

      <el-input v-model="form.username" placeholder="Username" size="large" autofocus class="mb">
        <template #prefix><iconify-icon icon="lucide:user" width="16" /></template>
      </el-input>
      <el-input v-model="form.sandi" type="password" placeholder="Sandi" size="large" show-password class="mb">
        <template #prefix><iconify-icon icon="lucide:lock" width="16" /></template>
      </el-input>

      <el-button type="primary" size="large" native-type="submit" :loading="sibuk" style="width:100%">
        Masuk
      </el-button>
    </form>
  </div>
</template>

<style scoped>
.masuk { display: grid; place-items: center; min-height: 100vh; padding: 16px; }
.masuk { background: var(--surface-base); }
.masuk__kotak {
  width: 100%; max-width: 340px; padding: 32px;
  background: var(--surface-card); border-radius: var(--r-xl); box-shadow: var(--shadow-lg);
}
.masuk__logo {
  width: 48px; height: 48px; border-radius: var(--r-md); display: grid; place-items: center;
  background: linear-gradient(180deg, var(--primary-light), var(--primary)); color: #fff;
  margin-bottom: 16px; box-shadow: var(--glow-teal);
}
h1 { font-size: var(--text-h1); font-weight: 800; letter-spacing: 3px; color: var(--ink); }
.masuk__sub {
  margin: 4px 0 24px; font-size: var(--text-sm); color: var(--ink-muted); font-weight: 600;
  padding-bottom: 12px; border-bottom: 3px dashed var(--primary-bg);
}
.mb { margin-bottom: 12px; }
</style>

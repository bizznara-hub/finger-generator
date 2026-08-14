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
.masuk__kotak {
  width: 100%; max-width: 340px; padding: 32px;
  background: var(--color-surface); border: 1px solid var(--color-rule); border-radius: 12px;
}
.masuk__logo {
  width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center;
  background: var(--color-accent); color: #fff; margin-bottom: 16px;
}
h1 { font-size: 20px; font-weight: 700; }
.masuk__sub { margin: 4px 0 24px; font-size: 13px; color: var(--color-muted); }
.mb { margin-bottom: 12px; }
</style>

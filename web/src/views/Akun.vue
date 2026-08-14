<script setup>
import { onMounted, ref } from 'vue'
import { api, jalankan } from '@/api'

const form = ref({ nama: '', username: '', sandi_lama: '', sandi_baru: '', sandi_ulang: '' })
const sibuk = ref(false)

onMounted(async () => {
  const d = await api.get('/akun')
  form.value.nama = d.pengguna.nama
  form.value.username = d.pengguna.username
})

async function simpan() {
  sibuk.value = true
  try {
    await jalankan(() => api.put('/akun', form.value))
    form.value.sandi_lama = form.value.sandi_baru = form.value.sandi_ulang = ''
  } finally { sibuk.value = false }
}
</script>

<template>
  <div>
    <h1 class="tajuk">Akun</h1>

    <section class="kartu mb kotak">
      <div class="kartu__kepala"><h2 class="kartu__judul">Identitas</h2></div>
      <div class="kartu__isi">
        <el-form label-position="top">
          <el-form-item label="Nama"><el-input v-model="form.nama" /></el-form-item>
          <el-form-item label="Username"><el-input v-model="form.username" /></el-form-item>
        </el-form>
      </div>
    </section>

    <section class="kartu mb kotak">
      <div class="kartu__kepala"><h2 class="kartu__judul">Ganti sandi</h2></div>
      <div class="kartu__isi">
        <p class="petunjuk">Kosongkan bila tidak ingin mengganti sandi. Minimal 6 karakter.</p>
        <el-form label-position="top">
          <el-form-item label="Sandi lama"><el-input v-model="form.sandi_lama" type="password" show-password /></el-form-item>
          <el-form-item label="Sandi baru"><el-input v-model="form.sandi_baru" type="password" show-password /></el-form-item>
          <el-form-item label="Ulangi sandi baru"><el-input v-model="form.sandi_ulang" type="password" show-password /></el-form-item>
        </el-form>
      </div>
    </section>

    <el-button type="primary" :loading="sibuk" @click="simpan">Simpan</el-button>
  </div>
</template>

<style scoped>
.tajuk { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.kotak { max-width: 520px; }
</style>

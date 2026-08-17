<script setup>
import { onMounted, ref } from 'vue'
import { api, jalankan } from '@/api'

const p = ref(null); const sibuk = ref(false)

onMounted(async () => { p.value = (await api.get('/pengaturan')).pengaturan })

async function simpan() {
  sibuk.value = true
  try { await jalankan(() => api.put('/pengaturan', p.value)) } finally { sibuk.value = false }
}
</script>

<template>
  <div v-loading="!p">
    <template v-if="p">
      <h1 class="tajuk">Pengaturan</h1>

      <section class="kartu mb">
        <div class="kartu__kepala"><h2 class="kartu__judul">Perhitungan jam sesi</h2></div>
        <div class="kartu__isi">
          <p class="petunjuk">
            jam selesai = jam masuk + (jumlah jam × menit per jam) + ((jumlah jam − 1) × menit pergantian)
          </p>
          <el-form label-position="top" class="kisi">
            <el-form-item label="Menit per jam"><el-input-number v-model="p.menit_perjam" :min="1" :max="180" style="width:100%" /></el-form-item>
            <el-form-item label="Menit pergantian"><el-input-number v-model="p.menit_pergantian" :min="0" :max="120" style="width:100%" /></el-form-item>
            <el-form-item label="Toleransi datang awal"><el-input-number v-model="p.toleransi_awal" :min="0" :max="180" style="width:100%" /></el-form-item>
            <el-form-item label="Toleransi terlambat"><el-input-number v-model="p.toleransi_akhir" :min="0" :max="180" style="width:100%" /></el-form-item>
            <el-form-item label="Jam masuk perkuliahan"><el-input v-model="p.jam_kuliah" placeholder="07:30" /></el-form-item>
            <el-form-item label="Istirahat mulai"><el-input v-model="p.istirahat_mulai" placeholder="12:00" /></el-form-item>
            <el-form-item label="Istirahat selesai"><el-input v-model="p.istirahat_selesai" placeholder="13:00" /></el-form-item>
          </el-form>
        </div>
      </section>

      <section class="kartu mb">
        <div class="kartu__kepala"><h2 class="kartu__judul">Kop laporan</h2></div>
        <div class="kartu__isi">
          <p class="petunjuk">Baris pertama disusun otomatis dari semester dan tahun ajaran blok.</p>
          <el-form label-position="top" class="kisi2">
            <el-form-item label="Baris kedua"><el-input v-model="p.nama_institusi" /></el-form-item>
            <el-form-item label="Baris ketiga"><el-input v-model="p.nama_universitas" /></el-form-item>
          </el-form>
        </div>
      </section>

      <section class="kartu mb">
        <div class="kartu__kepala"><h2 class="kartu__judul">Koneksi att_log (Fingerspot)</h2></div>
        <div class="kartu__isi">
          <p class="petunjuk">
            Gunakan kredensial <b>baca-saja</b>. Aplikasi hanya membaca tabel <code>att_log</code>.
          </p>
          <el-form label-position="top" class="kisi">
            <el-form-item label="Host"><el-input v-model="p.attlog_host" placeholder="localhost" /></el-form-item>
            <el-form-item label="Port"><el-input-number v-model="p.attlog_port" :min="1" :max="65535" style="width:100%" /></el-form-item>
            <el-form-item label="Nama basis data"><el-input v-model="p.attlog_nama_db" placeholder="db_fingerfk" /></el-form-item>
            <el-form-item label="Pengguna"><el-input v-model="p.attlog_user" /></el-form-item>
            <el-form-item label="Sandi">
              <el-input v-model="p.attlog_sandi" type="password" show-password
                        :placeholder="p.attlog_sandi_tersimpan ? 'tersimpan — kosongkan bila tidak diubah' : ''" />
            </el-form-item>
          </el-form>
        </div>
      </section>

      <el-button type="primary" :loading="sibuk" @click="simpan">Simpan pengaturan</el-button>
    </template>
  </div>
</template>

<style scoped>
.tajuk { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.kisi { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,200px),1fr)); gap: 0 16px; }
.kisi2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,260px),1fr)); gap: 0 16px; }
</style>

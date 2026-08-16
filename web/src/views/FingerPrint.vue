<script setup>
import { onMounted, ref } from 'vue'
import { api, jalankan } from '@/api'

const d = ref(null); const rentang = ref([]); const berkas = ref(null); const sibuk = ref('')

async function muat() { d.value = await api.get('/mentah/ringkasan') }

async function tarik() {
  if (!rentang.value?.length) return
  sibuk.value = 'tarik'
  try {
    await jalankan(() => api.post('/mentah/tarik',
      { tanggal_awal: rentang.value[0], tanggal_akhir: rentang.value[1] }))
    await muat()
  } finally { sibuk.value = '' }
}

async function uji() {
  sibuk.value = 'uji'
  try { await jalankan(() => api.post('/mentah/uji-koneksi')) } finally { sibuk.value = '' }
}

async function impor(e) {
  const f = e.target.files
  if (!f?.length) return
  const fd = new FormData()
  for (const x of f) fd.append('berkas', x)
  sibuk.value = 'impor'
  try {
    await jalankan(() => api.unggah('/mentah/impor', fd))
    await muat()
  } finally { sibuk.value = ''; e.target.value = '' }
}

onMounted(muat)
</script>

<template>
  <div v-loading="!d">
    <template v-if="d">
      <h1 class="tajuk">Finger Print</h1>

      <div class="angka">
        <div class="stat"><b class="num">{{ d.jumlah }}</b><span>scan tersimpan</span></div>
        <div v-for="s in d.per_sumber" :key="s.sumber" class="stat">
          <b class="num">{{ s.jumlah }}</b><span>dari {{ s.sumber }}</span>
        </div>
        <div class="stat"><b class="num">{{ d.terakhir || '—' }}</b><span>scan terakhir</span></div>
      </div>

      <div class="baris">
        <section class="kartu">
          <div class="kartu__kepala">
            <h2 class="kartu__judul">Jalur A — tarik dari att_log</h2>
            <el-tag :type="d.attlog_siap ? 'success' : 'warning'" size="small">
              {{ d.attlog_siap ? 'siap' : 'belum diatur' }}
            </el-tag>
          </div>
          <div class="kartu__isi">
            <p class="petunjuk" v-if="d.attlog_siap">
              Tersambung ke <span class="num">{{ d.attlog_nama_db }}</span> di
              <span class="num">{{ d.attlog_host }}</span>.
            </p>
            <p class="petunjuk" v-else>
              Koneksi belum diatur. Isi dulu di <router-link to="/pengaturan">Pengaturan</router-link>.
            </p>
            <el-date-picker v-model="rentang" type="daterange" value-format="YYYY-MM-DD"
                            start-placeholder="Dari" end-placeholder="Sampai" style="width:100%" />
            <div class="tombol">
              <el-button type="primary" :disabled="!d.attlog_siap" :loading="sibuk === 'tarik'" @click="tarik">
                Tarik data
              </el-button>
              <el-button :loading="sibuk === 'uji'" @click="uji">Uji koneksi</el-button>
            </div>
          </div>
        </section>

        <section class="kartu">
          <div class="kartu__kepala"><h2 class="kartu__judul">Jalur B — impor berkas mesin</h2></div>
          <div class="kartu__isi">
            <p class="petunjuk">
              Tiga format dikenali. Paling lengkap: <b>Catatan Kehadiran Karyawan</b>.
              Scan kembar otomatis dilewati.
            </p>
            <input ref="berkas" type="file" accept=".xls,.xlsx" multiple hidden @change="impor">
            <el-button type="primary" :loading="sibuk === 'impor'" @click="$refs.berkas.click()">
              <iconify-icon icon="lucide:upload" width="15" style="margin-right:6px" /> Pilih berkas
            </el-button>
          </div>
        </section>
      </div>

      <section class="kartu">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">Mesin terdaftar</h2>
          <router-link to="/master/mesin"><el-button size="small">Kelola mesin</el-button></router-link>
          <router-link to="/finger-print/log"><el-button size="small" type="primary" plain>Log scan</el-button></router-link>
        </div>
        <el-table :data="d.mesin" empty-text="Belum ada mesin terdaftar.">
          <el-table-column prop="serial" label="Serial" min-width="150">
            <template #default="{ row }"><span class="num">{{ row.serial }}</span></template>
          </el-table-column>
          <el-table-column prop="nama" label="Nama" min-width="120" />
          <el-table-column label="Ruangan" min-width="140">
            <template #default="{ row }">
              <span v-if="row.ruangan">{{ row.ruangan }}</span>
              <el-tag v-else type="warning" size="small">belum dipetakan</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP" min-width="120">
            <template #default="{ row }"><span class="num redup">{{ row.ip_address || '—' }}</span></template>
          </el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>

<style scoped>
.tajuk { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.angka { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,180px),1fr)); gap: 12px; margin-bottom: 16px; }
.stat { padding: 16px; background: var(--surface-card); border: 1px solid var(--primary-bg); border-radius: var(--r-lg); }
.stat b { display: block; font-size: 22px; font-weight: 600; color: var(--ink); }
.stat span { font-size: 12.5px; color: var(--ink-muted); }
.baris { display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 16px; }
@media (min-width: 62rem) { .baris { grid-template-columns: 1fr 1fr; } }
.tombol { display: flex; gap: 8px; margin-top: 12px; }
</style>

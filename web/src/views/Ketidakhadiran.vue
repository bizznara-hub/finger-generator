<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const route = useRoute()
const jenis = computed(() => route.params.jenis)
const judul = ref(''); const baris = ref([]); const memuat = ref(false)
const hal = ref(1); const PER_HAL = 30
const halaman = computed(() => baris.value.slice((hal.value - 1) * PER_HAL, hal.value * PER_HAL))
const kata = ref(''); const pilihan = ref({}); const sesi = ref([])
const dialog = ref(false)
const form = ref({ mahasiswa_id: null, tanggal: '', jadwal_jam_id: null, keterangan: '' })

async function muat() {
  memuat.value = true
  try {
    const d = await api.get(`/ketidakhadiran/${jenis.value}?cari=${encodeURIComponent(kata.value)}`)
    judul.value = d.judul; baris.value = d.baris; hal.value = 1
  } finally { memuat.value = false }
}

async function muatSesi() {
  if (!form.value.tanggal) { sesi.value = []; return }
  const q = new URLSearchParams({ tanggal: form.value.tanggal })
  if (form.value.mahasiswa_id) q.set('mahasiswa_id', form.value.mahasiswa_id)
  sesi.value = (await api.get(`/ketidakhadiran/sesi?${q}`)).sesi
}

function buka() {
  form.value = { mahasiswa_id: null, tanggal: '', jadwal_jam_id: null, keterangan: '' }
  sesi.value = []; dialog.value = true
}

async function simpan() {
  await jalankan(() => api.post(`/ketidakhadiran/${jenis.value}`, form.value))
  dialog.value = false; await muat()
}

async function hapus(b) {
  await ElMessageBox.confirm('Hapus catatan ini?', 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/ketidakhadiran/${b.id}`)); await muat()
}

watch(jenis, () => { kata.value = ''; muat() }, { immediate: true })
watch(() => [form.value.tanggal, form.value.mahasiswa_id], muatSesi)
api.get('/pilihan').then((d) => (pilihan.value = d))
</script>

<template>
  <div>
    <div class="alat">
      <h1 class="tajuk">{{ judul }}</h1>
      <el-input v-model="kata" placeholder="Cari NIM atau nama…" clearable style="width:220px"
                @keyup.enter="muat" @clear="muat" />
      <el-button type="primary" @click="buka">
        <iconify-icon icon="lucide:plus" width="15" style="margin-right:5px" /> Catat {{ judul.toLowerCase() }}
      </el-button>
    </div>

    <div class="kartu">
      <el-table :data="halaman" v-loading="memuat" stripe empty-text="Belum ada catatan.">
        <el-table-column type="index" label="#" width="60" :index="(i) => (hal - 1) * PER_HAL + i + 1" />
        <el-table-column label="NIM" width="140">
          <template #default="{ row }"><span class="nim">{{ row.nim }}</span></template>
        </el-table-column>
        <el-table-column prop="nama" label="Nama" min-width="180" />
        <el-table-column label="Tanggal" width="120">
          <template #default="{ row }"><span class="num">{{ row.tanggal }}</span></template>
        </el-table-column>
        <el-table-column prop="sesi" label="Sesi" min-width="150" />
        <el-table-column prop="keterangan" label="Keterangan" min-width="160">
          <template #default="{ row }"><span class="redup">{{ row.keterangan || '—' }}</span></template>
        </el-table-column>
        <el-table-column label="" width="100" align="right">
          <template #default="{ row }"><el-button link type="danger" @click="hapus(row)">Hapus</el-button></template>
        </el-table-column>
      </el-table>

      <div v-if="baris.length > PER_HAL" class="hal">
        <el-pagination layout="prev, pager, next, total" :total="baris.length"
                       :page-size="PER_HAL" :current-page="hal" @current-change="hal = $event" />
      </div>
    </div>

    <el-dialog v-model="dialog" :title="`Catat ${judul.toLowerCase()}`" width="440">
      <p class="petunjuk">
        Kosongkan pilihan sesi bila berlaku untuk <b>seluruh sesi</b> pada tanggal itu.
        Catatan ini menimpa hasil pembacaan mesin.
      </p>
      <el-form label-position="top">
        <el-form-item label="Mahasiswa" required>
          <el-select v-model="form.mahasiswa_id" filterable placeholder="— pilih —" style="width:100%">
            <el-option v-for="o in pilihan.mahasiswa || []" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Tanggal" required>
          <el-date-picker v-model="form.tanggal" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="Sesi">
          <el-select v-model="form.jadwal_jam_id" clearable placeholder="seluruh sesi hari itu" style="width:100%">
            <el-option v-for="s in sesi" :key="s.id" :label="s.label" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Keterangan"><el-input v-model="form.keterangan" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Batal</el-button>
        <el-button type="primary" @click="simpan">Simpan</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.alat { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.tajuk { flex: 1; min-width: 140px; font-size: 20px; font-weight: 700; }
.hal { display: flex; justify-content: center; padding: 12px; }
</style>

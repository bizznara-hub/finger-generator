<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const router = useRouter()
const baris = ref([]); const pilihan = ref({}); const memuat = ref(false)
const dialog = ref(false); const form = ref({}); const sunting = ref(null)
const dialogKelas = ref(false); const kelasBaru = ref({ jadwal_id: null, kelas_id: null })

async function muat() {
  memuat.value = true
  try { baris.value = (await api.get('/jadwal')).baris } finally { memuat.value = false }
}

function buka(b) {
  sunting.value = b
  form.value = b
    ? { mata_kuliah_id: b.mata_kuliah_id, semester: b.semester, tahun_ajaran: b.tahun_ajaran }
    : { mata_kuliah_id: null, semester: '', tahun_ajaran: '' }
  dialog.value = true
}

async function simpan() {
  if (sunting.value) await jalankan(() => api.put(`/jadwal/${sunting.value.id}`, form.value))
  else await jalankan(() => api.post('/jadwal', form.value))
  dialog.value = false; await muat()
}

async function hapus(b) {
  await ElMessageBox.confirm('Hapus blok ini beserta seluruh tanggal dan sesinya?', 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/jadwal/${b.id}`)); await muat()
}

function bukaKelas(b) { kelasBaru.value = { jadwal_id: b.id, kelas_id: null }; dialogKelas.value = true }

async function tambahKelas() {
  await jalankan(() => api.post(`/jadwal/${kelasBaru.value.jadwal_id}/kelas`,
    { kelas_id: kelasBaru.value.kelas_id }))
  dialogKelas.value = false; await muat()
}

async function hapusKelas(jk) {
  await ElMessageBox.confirm('Keluarkan kelas ini beserta tanggal dan sesinya?', 'Konfirmasi',
    { confirmButtonText: 'Keluarkan', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/jadwal/kelas/${jk.id}`)); await muat()
}

onMounted(async () => { await muat(); pilihan.value = await api.get('/pilihan') })
</script>

<template>
  <div>
    <div class="alat">
      <h1 class="tajuk">Jadwal Kuliah</h1>
      <el-button type="primary" @click="buka(null)">
        <iconify-icon icon="lucide:plus" width="15" style="margin-right:5px" /> Tambah blok
      </el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon class="info"
      title="Susun dari atas ke bawah: blok → kelas peserta → tanggal → sesi. Sesi dibuat manual dan bisa diubah kapan saja." />

    <div v-loading="memuat" class="daftar">
      <section v-for="b in baris" :key="b.id" class="kartu">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">{{ b.mata_kuliah || '—' }}</h2>
          <span class="redup kecil">{{ b.semester || '—' }} · {{ b.tahun_ajaran || '—' }}</span>
          <el-button size="small" @click="bukaKelas(b)">+ Kelas</el-button>
          <el-button size="small" @click="buka(b)">Ubah</el-button>
          <el-button size="small" type="danger" plain @click="hapus(b)">Hapus</el-button>
        </div>
        <div class="kartu__isi">
          <div v-if="b.kelas.length" class="kelas">
            <div v-for="k in b.kelas" :key="k.id" class="kelas__item">
              <div>
                <b>{{ k.label }}</b>
                <span class="redup kecil"> · {{ k.jumlah_peserta }} peserta · {{ k.jumlah_hari }} tanggal</span>
              </div>
              <div class="aksi">
                <el-button type="primary" plain
                           @click="router.push(`/jadwal/kelas/${k.id}`)">Atur sesi</el-button>
                <el-button type="danger" link @click="hapusKelas(k)">Keluarkan</el-button>
              </div>
            </div>
          </div>
          <p v-else class="petunjuk">Belum ada kelas pada blok ini.</p>
        </div>
      </section>
      <el-empty v-if="!memuat && !baris.length" description="Belum ada blok terjadwal." />
    </div>

    <el-dialog v-model="dialog" :title="sunting ? 'Ubah blok' : 'Tambah blok'" width="420">
      <el-form label-position="top">
        <el-form-item label="Mata kuliah / blok" required>
          <el-select v-model="form.mata_kuliah_id" placeholder="— pilih —" style="width:100%">
            <el-option v-for="o in pilihan.mata_kuliah || []" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Semester"><el-input v-model="form.semester" placeholder="Akhir" /></el-form-item>
        <el-form-item label="Tahun ajaran"><el-input v-model="form.tahun_ajaran" placeholder="2025/2026" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Batal</el-button>
        <el-button type="primary" @click="simpan">Simpan</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogKelas" title="Tambah kelas peserta" width="420">
      <p class="petunjuk">Seluruh mahasiswa kelas itu otomatis terdaftar sebagai peserta.</p>
      <el-select v-model="kelasBaru.kelas_id" placeholder="— pilih kelas —" style="width:100%">
        <el-option v-for="o in pilihan.kelas || []" :key="o.id" :label="o.label" :value="o.id" />
      </el-select>
      <template #footer>
        <el-button @click="dialogKelas = false">Batal</el-button>
        <el-button type="primary" @click="tambahKelas">Tambahkan</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.alat { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.tajuk { flex: 1; font-size: 20px; font-weight: 700; }
.info { margin-bottom: 16px; }
.daftar { display: grid; gap: 16px; }
.kelas__item {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid var(--primary-bg);
}
.kelas__item:last-child { border-bottom: 0; }
</style>

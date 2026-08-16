<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const route = useRoute(); const router = useRouter()
const id = route.params.id
const d = ref(null); const pilihan = ref({})
const rentang = ref([]); const pesertaBaru = ref([])
const dialogSesi = ref(false); const sesiForm = ref({}); const hariAktif = ref(null)
const hal = ref(1); const PER_HAL = 30
const peserta = computed(() =>
  (d.value?.peserta || []).slice((hal.value - 1) * PER_HAL, hal.value * PER_HAL))

async function muat() {
  d.value = await api.get(`/jadwal/kelas/${id}`)
}

async function tambahHari() {
  if (!rentang.value?.length) return
  await jalankan(() => api.post(`/jadwal/kelas/${id}/hari`,
    { tanggal: rentang.value[0], tanggal_akhir: rentang.value[1] }))
  rentang.value = []; await muat()
}

async function hapusHari(h) {
  await ElMessageBox.confirm('Hapus tanggal ini beserta seluruh sesinya?', 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/jadwal/hari/${h.id}`)); await muat()
}

function bukaSesi(h, s) {
  hariAktif.value = h
  sesiForm.value = s
    ? { ...s }
    : { id: null, kegiatan: '', jam_masuk: '07:30', jml_jam: 2, jam_selesai_manual: '', ruangan_id: null, dosen_id: [] }
  dialogSesi.value = true
}

async function simpanSesi() {
  const f = sesiForm.value
  if (f.id) await jalankan(() => api.put(`/jadwal/sesi/${f.id}`, f))
  else await jalankan(() => api.post(`/jadwal/hari/${hariAktif.value.id}/sesi`, f))
  dialogSesi.value = false; await muat()
}

async function hapusSesi(s) {
  await ElMessageBox.confirm('Hapus sesi ini?', 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/jadwal/sesi/${s.id}`)); await muat()
}

async function tambahPeserta() {
  if (!pesertaBaru.value.length) return
  await jalankan(() => api.post(`/jadwal/kelas/${id}/peserta`, { mahasiswa_id: pesertaBaru.value }))
  pesertaBaru.value = []; await muat()
}

async function hapusPeserta(p) {
  await jalankan(() => api.del(`/jadwal/peserta/${p.id}`)); await muat()
}

onMounted(async () => { await muat(); pilihan.value = await api.get('/pilihan') })
</script>

<template>
  <div v-loading="!d">
    <template v-if="d">
      <div class="alat">
        <h1 class="tajuk">{{ d.blok }} <span class="redup">— Kelas {{ d.kelas }}</span></h1>
        <el-button @click="router.push('/jadwal')">Kembali</el-button>
        <el-button type="primary" @click="router.push(`/laporan?kelas=${id}`)">Lihat laporan</el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon class="info"
        :title="`Jam selesai = jam masuk + (jumlah jam × ${d.pengaturan.menit_perjam} menit) + ((jumlah jam − 1) × ${d.pengaturan.menit_pergantian} menit), kecuali diisi manual. Toleransi ${d.pengaturan.toleransi_awal} menit awal dan ${d.pengaturan.toleransi_akhir} menit terlambat.`" />

      <section class="kartu mb">
        <div class="kartu__kepala"><h2 class="kartu__judul">Tambah tanggal</h2></div>
        <div class="kartu__isi">
          <p class="petunjuk">Pilih satu tanggal, atau rentang untuk membuat beberapa sekaligus.</p>
          <div class="sebaris">
            <el-date-picker v-model="rentang" type="daterange" value-format="YYYY-MM-DD"
                            start-placeholder="Dari" end-placeholder="Sampai" />
            <el-button type="primary" @click="tambahHari">Tambahkan</el-button>
          </div>
        </div>
      </section>

      <section v-for="h in d.hari" :key="h.id" class="kartu mb">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">{{ h.label }}</h2>
          <el-tag size="small" type="info">{{ h.sesi.length }} sesi</el-tag>
          <el-button size="small" type="primary" plain @click="bukaSesi(h, null)">+ Sesi</el-button>
          <el-button size="small" type="danger" link @click="hapusHari(h)">Hapus tanggal</el-button>
        </div>
        <el-table :data="h.sesi" empty-text="Belum ada sesi pada tanggal ini.">
          <el-table-column prop="kegiatan" label="Kegiatan" min-width="170" />
          <el-table-column label="Jam masuk" width="110">
            <template #default="{ row }"><span class="num">{{ row.jam_masuk }}</span></template>
          </el-table-column>
          <el-table-column prop="jml_jam" label="Jml jam" width="90" />
          <el-table-column label="Selesai" width="110">
            <template #default="{ row }">
              <span class="num">{{ row.jam_selesai_manual || row.jam_selesai_hitung }}</span>
              <span v-if="!row.jam_selesai_manual" class="redup kecil"> otomatis</span>
            </template>
          </el-table-column>
          <el-table-column label="Aksi" width="176" align="left">
            <template #default="{ row }">
              <div class="aksi">
                <el-button link @click="bukaSesi(h, row)">Ubah</el-button>
                <el-button link type="danger" @click="hapusSesi(row)">Hapus</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <el-empty v-if="!d.hari.length" description="Belum ada tanggal. Tambahkan lewat formulir di atas." />

      <section class="kartu">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">Peserta</h2>
          <el-tag size="small" round>{{ d.peserta.length }} mahasiswa</el-tag>
        </div>
        <div class="kartu__isi">
          <div class="sebaris">
            <el-select v-model="pesertaBaru" multiple filterable collapse-tags collapse-tags-tooltip
                       placeholder="Tambah mahasiswa…" style="flex:1;min-width:240px">
              <el-option v-for="o in d.belum_terdaftar" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
            <el-button type="primary" @click="tambahPeserta">Tambahkan</el-button>
          </div>
        </div>
        <el-table :data="peserta" empty-text="Belum ada peserta.">
          <el-table-column type="index" label="No" width="70" :index="(i) => (hal - 1) * PER_HAL + i + 1" />
          <el-table-column label="NIM" width="140">
            <template #default="{ row }"><span class="nim">{{ row.nim }}</span></template>
          </el-table-column>
          <el-table-column prop="nama" label="Nama" min-width="180" />
          <el-table-column label="ID Finger" width="120">
            <template #default="{ row }">
              <span v-if="row.id_finger" class="num">{{ row.id_finger }}</span>
              <el-tag v-else type="warning" size="small">belum diisi</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Aksi" width="120" align="left">
            <template #default="{ row }">
              <el-button link type="danger" @click="hapusPeserta(row)">Keluarkan</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="d.peserta.length > PER_HAL" class="hal">
          <el-pagination layout="prev, pager, next, total" :total="d.peserta.length"
                         :page-size="PER_HAL" :current-page="hal" @current-change="hal = $event" />
        </div>
      </section>

      <el-dialog v-model="dialogSesi" :title="sesiForm.id ? 'Ubah sesi' : 'Tambah sesi'" width="460">
        <el-form label-position="top">
          <el-form-item label="Nama kegiatan" required>
            <el-input v-model="sesiForm.kegiatan" placeholder="PBL 1 (MODUL 1)" />
          </el-form-item>
          <div class="kisi">
            <el-form-item label="Jam masuk" required>
              <el-input v-model="sesiForm.jam_masuk" placeholder="07:30" />
            </el-form-item>
            <el-form-item label="Jumlah jam">
              <el-input-number v-model="sesiForm.jml_jam" :min="1" :max="12" style="width:100%" />
            </el-form-item>
            <el-form-item label="Jam selesai manual">
              <el-input v-model="sesiForm.jam_selesai_manual" placeholder="otomatis" />
            </el-form-item>
          </div>
          <el-form-item label="Ruangan">
            <el-select v-model="sesiForm.ruangan_id" clearable placeholder="—" style="width:100%">
              <el-option v-for="o in pilihan.ruangan || []" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Pengajar">
            <el-select v-model="sesiForm.dosen_id" multiple filterable placeholder="—" style="width:100%">
              <el-option v-for="o in pilihan.dosen || []" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogSesi = false">Batal</el-button>
          <el-button type="primary" @click="simpanSesi">Simpan</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.alat { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.tajuk { flex: 1; min-width: 200px; font-size: 20px; font-weight: 700; }
.info { margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.sebaris { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.hal { display: flex; justify-content: center; padding: 12px; }
.kisi { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0 12px; }
</style>

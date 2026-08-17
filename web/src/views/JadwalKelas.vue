<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const route = useRoute(); const router = useRouter()
const id = computed(() => route.params.id)
// Tab disimpan di query supaya pindah kelas tidak melemparkan admin
// kembali ke tab jadwal saat sedang melihat daftar mahasiswa.
const tab = computed({
  get: () => route.query.tab || 'jadwal',
  set: (v) => router.replace({ query: { ...route.query, tab: v } })
})

function pindahKelas(idJk) {
  router.push({ path: `/jadwal/kelas/${idJk}`, query: { ...route.query } })
}
const d = ref(null); const pilihan = ref({})
const tanggalBaru = ref(''); const pesertaBaru = ref([])
const dialogSesi = ref(false); const sesiForm = ref({}); const hariAktif = ref(null)
const hal = ref(1); const PER_HAL = 30
const peserta = computed(() =>
  (d.value?.peserta || []).slice((hal.value - 1) * PER_HAL, hal.value * PER_HAL))

// Satu tabel untuk seluruh tanggal, seperti Jadwal Perkelas di aplikasi PHP.
// Tiap sesi memakan satu baris per jam, sedangkan kolom tanggal dan kolom
// kegiatan digabung ke bawah dengan rowspan. Tanggal tanpa sesi tetap muncul
// sebagai baris kosong supaya terlihat hari mana yang belum terisi.
const barisJadwal = computed(() => {
  const keluar = []
  for (const h of d.value?.hari || []) {
    const baris = []
    for (const s of h.sesi) {
      const waktu = s.jam_selesai_manual ? [`${s.jam_masuk}-${s.jam_selesai_manual}`] : s.slot
      waktu.forEach((w, i) => baris.push({ sesi: s, waktu: w, awalSesi: i === 0, tinggiSesi: waktu.length }))
    }
    if (!baris.length) keluar.push({ hari: h, awalHari: true, tinggiHari: 1, kosong: true })
    else baris.forEach((r, i) => keluar.push({ ...r, hari: h, awalHari: i === 0, tinggiHari: baris.length }))
  }
  return keluar
})

async function muat() {
  d.value = await api.get(`/jadwal/kelas/${id.value}`)
}

async function tambahHari() {
  if (!tanggalBaru.value) return
  // Satu tanggal saja, seperti add-hari.php. Rentang hanya dipakai sekali
  // ketika blok dibuat.
  await jalankan(() => api.post(`/jadwal/kelas/${id.value}/hari`,
    { tanggal: tanggalBaru.value }))
  tanggalBaru.value = ''; await muat()
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
    : { id: null, kegiatan: '', jam_masuk: d.value?.pengaturan?.jam_kuliah || '07:30',
        jml_jam: 2, jam_selesai_manual: '', ruangan_id: null, departemen_id: null, dosen_id: [] }
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
  await jalankan(() => api.post(`/jadwal/kelas/${id.value}/peserta`, { mahasiswa_id: pesertaBaru.value }))
  pesertaBaru.value = []; await muat()
}

async function hapusPeserta(p) {
  await jalankan(() => api.del(`/jadwal/peserta/${p.id}`)); await muat()
}

watch(id, async () => { hal.value = 1; await muat() })
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

      <section class="kartu mb">
        <div class="kartu__isi profil">
          <div><span class="profil__nama">Semester</span> {{ d.semester || '—' }} · {{ d.tahun_ajaran || '—' }}</div>
          <div><span class="profil__nama">Koordinator</span> {{ d.koordinator || '—' }}</div>
          <div><span class="profil__nama">Sekretaris</span> {{ d.sekretaris || '—' }}</div>
          <div><span class="profil__nama">Pengaturan</span> {{ d.profil_jam }}</div>
          <div class="profil__kelas">
            <span class="profil__nama">Kelas</span>
            <el-select :model-value="Number(id)" style="width:230px" @change="pindahKelas">
              <el-option v-for="o in d.daftar_kelas" :key="o.id"
                         :label="`${o.nama} — ${o.jumlah_peserta} peserta, ${o.jumlah_hari} tanggal`"
                         :value="o.id" />
            </el-select>
          </div>
        </div>
      </section>

      <el-tabs v-model="tab" class="tab">
        <el-tab-pane label="Jadwal kelas" name="jadwal" />
        <el-tab-pane label="Mahasiswa kelas" name="mahasiswa" />
      </el-tabs>

      <template v-if="tab === 'jadwal'">
      <el-alert type="info" :closable="false" show-icon class="info"
        :title="`${d.pengaturan.profil_jam}. Toleransi ${d.pengaturan.toleransi_awal} menit datang awal dan ${d.pengaturan.toleransi_akhir} menit terlambat.`" />

      <section class="kartu mb">
        <div class="kartu__kepala"><h2 class="kartu__judul">Tambah tanggal</h2></div>
        <div class="kartu__isi">
          <p class="petunjuk">
            Seluruh tanggal blok sudah dibuat saat blok didaftarkan. Ini hanya untuk
            menyisipkan satu tanggal tambahan.
          </p>
          <div class="sebaris">
            <el-date-picker v-model="tanggalBaru" type="date" value-format="YYYY-MM-DD"
                            placeholder="Pilih tanggal" style="width:220px" />
            <el-button type="primary" @click="tambahHari">Tambahkan</el-button>
          </div>
        </div>
      </section>

      <section class="kartu mb">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">Daftar Jadwal Kelas {{ d.kelas }}</h2>
          <el-tag size="small" type="info">{{ d.hari.length }} tanggal</el-tag>
        </div>
        <div class="gulir">
          <table class="jadwal">
            <thead>
              <tr>
                <th class="kol-tgl">Hari / Tanggal</th>
                <th class="kol-waktu">Waktu</th>
                <th>Kegiatan</th>
                <th>Dosen</th>
                <th>Departemen</th>
                <th>Ruangan</th>
                <th class="kol-aksi">Pilihan</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in barisJadwal" :key="i" :class="{ 'awal-hari': r.awalHari }">
                <td v-if="r.awalHari" :rowspan="r.tinggiHari" class="kol-tgl">
                  <div class="tgl">{{ r.hari.label }}</div>
                  <div class="tgl__aksi">
                    <el-button link type="primary" @click="bukaSesi(r.hari, null)">+ Sesi</el-button>
                    <el-button link type="danger" @click="hapusHari(r.hari)">Hapus</el-button>
                  </div>
                </td>
                <td v-if="r.kosong" colspan="6" class="kosong">Belum ada sesi pada tanggal ini.</td>
                <td v-if="!r.kosong" class="kol-waktu num">{{ r.waktu }}</td>
                <td v-if="!r.kosong && r.awalSesi" :rowspan="r.tinggiSesi">
                  {{ r.sesi.kegiatan }}
                  <span v-if="r.sesi.jam_selesai_manual" class="redup kecil">manual</span>
                </td>
                <td v-if="!r.kosong && r.awalSesi" :rowspan="r.tinggiSesi">
                  <span v-if="!r.sesi.dosen.length" class="redup">—</span>
                  <div v-for="(n, j) in r.sesi.dosen" :key="j" class="kecil">{{ n }}</div>
                </td>
                <td v-if="!r.kosong && r.awalSesi" :rowspan="r.tinggiSesi">
                  <span :class="{ redup: !r.sesi.departemen }">{{ r.sesi.departemen || '—' }}</span>
                </td>
                <td v-if="!r.kosong && r.awalSesi" :rowspan="r.tinggiSesi">
                  <span :class="{ redup: !r.sesi.ruangan }">{{ r.sesi.ruangan || '—' }}</span>
                </td>
                <td v-if="!r.kosong && r.awalSesi" :rowspan="r.tinggiSesi" class="kol-aksi">
                  <div class="aksi">
                    <el-button link @click="bukaSesi(r.hari, r.sesi)">Ubah</el-button>
                    <el-button link type="danger" @click="hapusSesi(r.sesi)">Hapus</el-button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <el-empty v-if="!d.hari.length" description="Belum ada tanggal. Tambahkan lewat formulir di atas." />
      </template>

      <section v-else class="kartu">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">Mahasiswa kelas {{ d.kelas }}</h2>
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
          <el-table-column label="Masuk" width="90" align="center">
            <template #default="{ row }"><span class="num">{{ row.masuk }}</span></template>
          </el-table-column>
          <el-table-column label="Tidak Masuk" width="120" align="center">
            <template #default="{ row }">
              <span class="num" :class="{ merah: row.tidak_masuk }">{{ row.tidak_masuk }}</span>
            </template>
          </el-table-column>
          <el-table-column label="Aksi" width="150" align="right">
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
          <el-form-item label="Ruangan" required>
            <el-select v-model="sesiForm.ruangan_id" placeholder="— pilih —" style="width:100%">
              <el-option v-for="o in pilihan.ruangan || []" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Departemen">
            <el-select v-model="sesiForm.departemen_id" clearable filterable placeholder="—" style="width:100%">
              <el-option v-for="o in pilihan.departemen || []" :key="o.id" :label="o.label" :value="o.id" />
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
.profil { display: grid; gap: 10px; font-size: var(--text-sm); }
.profil__nama { display: inline-block; min-width: 108px; font-weight: 700; color: var(--ink-2); }
.profil__kelas { display: flex; align-items: center; }
.tab { margin-bottom: 4px; }
.merah { color: var(--danger, #d9534f); font-weight: 700; }
.gulir { overflow-x: auto; }
.jadwal { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.jadwal th {
  text-align: left; padding: 12px 14px; white-space: nowrap;
  font-size: var(--text-xs); font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  color: var(--primary-dark); background: var(--primary-bg);
}
.jadwal td { padding: 10px 14px; vertical-align: top; border-bottom: 1px solid var(--primary-bg); }
.jadwal tr.awal-hari > td { border-top: 2px solid var(--primary-bg); }
.kol-tgl { width: 210px; }
.kol-waktu { width: 120px; white-space: nowrap; }
.kol-aksi { width: 170px; }
.tgl { font-weight: 700; color: var(--ink); }
.tgl__aksi { display: flex; gap: 10px; margin-top: 2px; }
.kosong { color: var(--ink-muted); font-style: italic; }
.kisi { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0 12px; }
</style>

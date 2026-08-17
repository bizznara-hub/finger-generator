<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const p = ref(null); const sibuk = ref(false)

// Beberapa aturan pembagian waktu; tiap blok menunjuk salah satunya.
const profil = ref([]); const dialogProfil = ref(false)
const formProfil = ref({}); const suntingProfil = ref(null); const sibukProfil = ref(false)

async function muatProfil() { profil.value = (await api.get('/profil-jam')).baris }

function bukaProfil(x) {
  suntingProfil.value = x
  formProfil.value = x
    ? { ...x }
    : { menit_perjam: 50, menit_pergantian: 5, jam_kuliah: '07:00',
        istirahat_mulai: '12:00', istirahat_selesai: '13:00', jam_perhari: 8 }
  dialogProfil.value = true
}

async function simpanProfil() {
  sibukProfil.value = true
  try {
    if (suntingProfil.value) await jalankan(() => api.put(`/profil-jam/${suntingProfil.value.id}`, formProfil.value))
    else await jalankan(() => api.post('/profil-jam', formProfil.value))
    dialogProfil.value = false
    await muatProfil()
  } finally { sibukProfil.value = false }
}

async function hapusProfil(x) {
  await ElMessageBox.confirm(`Hapus "${x.label}"?`, 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/profil-jam/${x.id}`)); await muatProfil()
}

async function jadikanBawaan(x) {
  await jalankan(() => api.post(`/profil-jam/${x.id}/bawaan`)); await muatProfil()
}

onMounted(async () => {
  p.value = (await api.get('/pengaturan')).pengaturan
  await muatProfil()
})

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
            <el-form-item label="Toleransi datang awal"><el-input-number v-model="p.toleransi_awal" :min="0" :max="180" style="width:100%" /></el-form-item>
            <el-form-item label="Toleransi terlambat"><el-input-number v-model="p.toleransi_akhir" :min="0" :max="180" style="width:100%" /></el-form-item>
          </el-form>
        </div>
      </section>

      <section class="kartu mb">
        <div class="kartu__kepala">
          <h2 class="kartu__judul">Data Pengaturan</h2>
          <el-tag size="small" type="info">{{ profil.length }} aturan</el-tag>
          <el-button size="small" type="primary" @click="bukaProfil(null)">+ Tambah</el-button>
        </div>
        <div class="kartu__isi">
          <p class="petunjuk">
            Tiap blok memilih salah satu aturan ini. Yang bertanda <b>bawaan</b> terpilih
            lebih dulu saat membuat blok baru.
          </p>
        </div>
        <el-table :data="profil" empty-text="Belum ada pengaturan jam.">
          <el-table-column type="index" label="No." width="80" />
          <el-table-column label="Jumlah Menit" min-width="210">
            <template #default="{ row }">
              Perjam = {{ row.menit_perjam }} | Pergantian = {{ row.menit_pergantian }}
            </template>
          </el-table-column>
          <el-table-column label="Jam Masuk Perkuliahan" width="200" align="center">
            <template #default="{ row }"><span class="num">{{ row.jam_kuliah || '—' }}</span></template>
          </el-table-column>
          <el-table-column label="Jam Istirahat" width="160" align="center">
            <template #default="{ row }">
              <span v-if="row.istirahat_mulai" class="num">{{ row.istirahat_mulai }} - {{ row.istirahat_selesai }}</span>
              <span v-else class="redup">—</span>
            </template>
          </el-table-column>
          <el-table-column label="Jumlah Jam Perhari" width="170" align="center">
            <template #default="{ row }"><span class="num">{{ row.jam_perhari ?? '—' }}</span></template>
          </el-table-column>
          <!-- 340px: tiga tombol sekaligus, dan "Jadikan bawaan" tidak boleh
               terpotong karena .aksi memang sengaja tidak membungkus baris. -->
          <el-table-column label="Pilihan" width="340" align="right">
            <template #default="{ row }">
              <div class="aksi">
                <el-tag v-if="row.bawaan" size="small" type="success">bawaan</el-tag>
                <el-button v-else link @click="jadikanBawaan(row)">Jadikan bawaan</el-button>
                <el-button link @click="bukaProfil(row)">Ubah</el-button>
                <el-button link type="danger" @click="hapusProfil(row)">Hapus</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
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
      <el-dialog v-model="dialogProfil" :title="suntingProfil ? 'Ubah pengaturan jam' : 'Tambah pengaturan jam'" width="480">
        <el-form label-position="top">
          <div class="kisi2">
            <el-form-item label="Menit per jam" required>
              <el-input-number v-model="formProfil.menit_perjam" :min="1" :max="180" style="width:100%" />
            </el-form-item>
            <el-form-item label="Menit pergantian">
              <el-input-number v-model="formProfil.menit_pergantian" :min="0" :max="120" style="width:100%" />
            </el-form-item>
          </div>
          <div class="kisi2">
            <el-form-item label="Jam masuk perkuliahan">
              <el-input v-model="formProfil.jam_kuliah" placeholder="07:00" />
            </el-form-item>
            <el-form-item label="Jumlah jam per hari">
              <el-input-number v-model="formProfil.jam_perhari" :min="1" :max="24" style="width:100%" />
            </el-form-item>
          </div>
          <div class="kisi2">
            <el-form-item label="Istirahat mulai">
              <el-input v-model="formProfil.istirahat_mulai" placeholder="12:00" />
            </el-form-item>
            <el-form-item label="Istirahat selesai">
              <el-input v-model="formProfil.istirahat_selesai" placeholder="13:00" />
            </el-form-item>
          </div>
          <p class="petunjuk">Kosongkan kedua jam istirahat bila aturan ini tidak memakainya.</p>
        </el-form>
        <template #footer>
          <el-button @click="dialogProfil = false">Batal</el-button>
          <el-button type="primary" :loading="sibukProfil" @click="simpanProfil">Simpan</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.tajuk { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.kisi { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,200px),1fr)); gap: 0 16px; }
.kisi2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,260px),1fr)); gap: 0 16px; }
</style>

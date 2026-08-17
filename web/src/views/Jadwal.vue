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

// Membuat blok baru sekaligus menetapkan kelas peserta dan seluruh tanggalnya,
// mengikuti alur aplikasi PHP. Saat mengubah, kelas dan tanggal tidak ikut
// disentuh karena keduanya sudah punya halaman pengaturannya sendiri.
function buka(b) {
  sunting.value = b
  form.value = b
    ? { mata_kuliah_id: b.mata_kuliah_id, semester: b.semester, tahun_ajaran: b.tahun_ajaran,
        koordinator_id: b.koordinator_id, sekretaris_id: b.sekretaris_id,
        profil_jam_id: b.profil_jam_id }
    : { mata_kuliah_id: null, semester: '', tahun_ajaran: '', koordinator_id: null,
        sekretaris_id: null, kelas_id: [], tanggal_mulai: '', tanggal_selesai: '',
        profil_jam_id: (pilihan.value.profil_jam || []).find((x) => x.bawaan)?.id ?? null }
  dialog.value = true
}

async function simpan() {
  if (sunting.value) {
    await jalankan(() => api.put(`/jadwal/${sunting.value.id}`, form.value))
  } else {
    await jalankan(() => api.post('/jadwal', form.value))
  }
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
        <!-- Judul dan tombol di baris sendiri; keterangan blok turun ke bawah
             sebagai pasangan label-nilai. Sebelumnya semuanya dijejalkan dalam
             satu baris flex sehingga nama dosen dan label pengaturan yang
             panjang saling menempel tanpa jarak. -->
        <div class="kartu__kepala">
          <h2 class="kartu__judul">{{ b.mata_kuliah || '—' }}</h2>
          <el-tag size="small" type="info" round>
            Semester {{ b.semester || '—' }} · {{ b.tahun_ajaran || '—' }}
          </el-tag>
          <el-button size="small" @click="bukaKelas(b)">+ Kelas</el-button>
          <el-button size="small" @click="buka(b)">Ubah</el-button>
          <el-button size="small" type="danger" plain @click="hapus(b)">Hapus</el-button>
        </div>
        <div class="kartu__isi">
          <dl class="ket">
            <div><dt>Koordinator</dt><dd>{{ b.koordinator || '—' }}</dd></div>
            <div><dt>Sekretaris</dt><dd>{{ b.sekretaris || '—' }}</dd></div>
            <div class="ket__lebar"><dt>Pengaturan jam</dt><dd>{{ b.profil_jam || '—' }}</dd></div>
          </dl>
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

    <el-dialog v-model="dialog" :title="sunting ? 'Ubah blok' : 'Tambah blok'" width="520">
      <el-form label-position="top">
        <div class="kisi2">
          <el-form-item label="Semester" required>
            <el-select v-model="form.semester" placeholder="— pilih —" style="width:100%">
              <el-option label="Awal" value="Awal" />
              <el-option label="Akhir" value="Akhir" />
            </el-select>
          </el-form-item>
          <el-form-item label="Tahun ajaran" required>
            <el-input v-model="form.tahun_ajaran" placeholder="2025/2026" />
          </el-form-item>
        </div>

        <!-- Dua pemilih terpisah, bukan rentang. Mode rentang Element Plus selalu
             membentangkan dua bulan sekaligus; menyembunyikan panel kanan lewat CSS
             mematikan tombol maju, jadi bulan berikutnya tak terjangkau. Dua pemilih
             tanggal biasa masing-masing membuka satu kalender yang tetap bisa dinavigasi. -->
        <div v-if="!sunting" class="kisi2">
          <el-form-item label="Tanggal mulai" required>
            <el-date-picker v-model="form.tanggal_mulai" type="date" value-format="YYYY-MM-DD"
                            placeholder="Pilih tanggal" style="width:100%" />
          </el-form-item>
          <el-form-item label="Tanggal selesai" required>
            <el-date-picker v-model="form.tanggal_selesai" type="date" value-format="YYYY-MM-DD"
                            placeholder="Pilih tanggal" style="width:100%" />
          </el-form-item>
        </div>

        <el-form-item label="Blok" required>
          <el-select v-model="form.mata_kuliah_id" filterable placeholder="— pilih —" style="width:100%">
            <el-option v-for="o in pilihan.mata_kuliah || []" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
        </el-form-item>

        <div class="kisi2">
          <el-form-item label="Koordinator" required>
            <el-select v-model="form.koordinator_id" filterable placeholder="— pilih dosen —" style="width:100%">
              <el-option v-for="o in pilihan.dosen || []" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Sekretaris" required>
            <el-select v-model="form.sekretaris_id" filterable placeholder="— pilih dosen —" style="width:100%">
              <el-option v-for="o in pilihan.dosen || []" :key="o.id" :label="o.label" :value="o.id" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item v-if="!sunting" label="Kelas" required>
          <el-select v-model="form.kelas_id" multiple filterable placeholder="— pilih satu atau lebih —" style="width:100%">
            <el-option v-for="o in pilihan.kelas || []" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="Pengaturan" required>
          <el-select v-model="form.profil_jam_id" placeholder="— pilih —" style="width:100%">
            <el-option v-for="o in pilihan.profil_jam || []" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
        </el-form-item>

        <p v-if="!sunting" class="petunjuk">
          Seluruh mahasiswa kelas terpilih otomatis jadi peserta, dan tanggal kuliah
          dibuat sepanjang rentang itu. Sabtu dan Minggu dilewati.
        </p>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Batal</el-button>
        <el-button type="primary" @click="simpan">Simpan</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogKelas" title="Tambah kelas peserta" width="420">
      <p class="petunjuk">
        Tanggalnya disalin dari kelas yang sudah ada pada blok ini. Pesertanya kosong,
        daftarkan mahasiswa lewat tab Mahasiswa kelas.
      </p>
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
.kisi2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
.ket {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px 24px; margin: 0 0 14px;
  padding-bottom: 14px; border-bottom: 1px solid var(--primary-bg);
}
.ket__lebar { grid-column: 1 / -1; }
.ket dt {
  font-size: var(--text-xs); font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: var(--ink-muted); margin-bottom: 2px;
}
.ket dd { margin: 0; font-size: var(--text-sm); color: var(--ink); overflow-wrap: anywhere; }
</style>

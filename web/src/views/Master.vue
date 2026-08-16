<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const route = useRoute()
const kunci = computed(() => route.params.kunci)

const SPEK = {
  departemen: { kolom: [['kode','Kode'],['nama','Nama']],
    bidang: [['kode','Kode','teks'],['nama','Nama departemen','teks',true]] },
  kelas: { kolom: [['nama','Nama'],['angkatan','Angkatan'],['departemen','Departemen'],['jumlah_mahasiswa','Mahasiswa']],
    bidang: [['nama','Nama kelas','teks',true],['angkatan','Angkatan','teks'],['departemen_id','Departemen','pilih:departemen']] },
  dosen: { kolom: [['nip','NIP'],['nama','Nama'],['departemen','Departemen'],['id_finger','ID Finger']],
    bidang: [['nip','NIP','teks'],['nama','Nama lengkap','teks',true],['departemen_id','Departemen','pilih:departemen'],['id_finger','ID Finger','teks'],['hp','No. HP','teks']] },
  mahasiswa: { kolom: [['nim','NIM'],['nama','Nama'],['kelas','Kelas'],['id_finger','ID Finger']],
    bidang: [['nim','NIM','teks',true],['nama','Nama lengkap','teks',true],['kelas_id','Kelas','pilih:kelas'],['id_finger','ID Finger','teks'],['hp','No. HP','teks']] },
  'mata-kuliah': { kolom: [['kode','Kode'],['nama','Nama blok'],['sks','SKS'],['departemen','Departemen']],
    bidang: [['kode','Kode','teks'],['nama','Nama mata kuliah / blok','teks',true],['sks','SKS','angka'],['departemen_id','Departemen','pilih:departemen']] },
  ruangan: { kolom: [['kode','Kode'],['nama','Nama'],['kapasitas','Kapasitas']],
    bidang: [['kode','Kode ruangan','teks'],['nama','Nama ruangan','teks',true],['kapasitas','Kapasitas','angka']] },
  mesin: { kolom: [['serial','Serial'],['nama','Nama'],['ruangan','Ruangan'],['ip_address','IP']],
    bidang: [['serial','Serial number','teks',true],['nama','Nama mesin','teks'],['ruangan_id','Ruangan','pilih:ruangan'],['ip_address','IP address','teks'],['port','Port','teks']] }
}

const spek = computed(() => SPEK[kunci.value] || SPEK.departemen)
const MONO = ['nim','id_finger','serial','ip_address','angkatan','sks','kapasitas','jumlah_mahasiswa']

const judul = ref(''); const baris = ref([]); const memuat = ref(false)
const hal = ref(1); const PER_HAL = 30
const halaman = computed(() => baris.value.slice((hal.value - 1) * PER_HAL, hal.value * PER_HAL))
const kata = ref(''); const pilihan = ref({})
const dialog = ref(false); const form = ref({}); const sunting = ref(null); const sibuk = ref(false)

async function muat() {
  memuat.value = true
  try {
    const d = await api.get(`/master/${kunci.value}?cari=${encodeURIComponent(kata.value)}`)
    judul.value = d.judul; baris.value = d.baris; hal.value = 1
  } finally { memuat.value = false }
}

async function muatPilihan() { pilihan.value = await api.get('/pilihan') }

function opsi(nama) {
  const peta = { departemen: 'departemen', kelas: 'kelas', ruangan: 'ruangan' }
  return pilihan.value[peta[nama]] || []
}

function buka(b) {
  sunting.value = b
  form.value = {}
  for (const [n] of spek.value.bidang) form.value[n] = b ? (b[n] ?? '') : ''
  dialog.value = true
}

async function simpan() {
  sibuk.value = true
  try {
    if (sunting.value) await jalankan(() => api.put(`/master/${kunci.value}/${sunting.value.id}`, form.value))
    else await jalankan(() => api.post(`/master/${kunci.value}`, form.value))
    dialog.value = false
    await muat()
  } finally { sibuk.value = false }
}

async function hapus(b) {
  await ElMessageBox.confirm('Hapus data ini?', 'Konfirmasi',
    { confirmButtonText: 'Hapus', cancelButtonText: 'Batal', type: 'warning' })
  await jalankan(() => api.del(`/master/${kunci.value}/${b.id}`))
  await muat()
}

watch(kunci, () => { kata.value = ''; muat() }, { immediate: true })
muatPilihan()
</script>

<template>
  <div>
    <div class="alat">
      <h1 class="tajuk">{{ judul }}</h1>
      <el-input v-model="kata" placeholder="Cari…" clearable style="width:220px" @keyup.enter="muat" @clear="muat">
        <template #prefix><iconify-icon icon="lucide:search" width="15" /></template>
      </el-input>
      <el-button @click="muat"><iconify-icon icon="lucide:refresh-cw" width="15" /></el-button>
      <el-button type="primary" @click="buka(null)">
        <iconify-icon icon="lucide:plus" width="15" style="margin-right:5px" /> Tambah
      </el-button>
    </div>

    <div class="kartu">
      <el-table :data="halaman" v-loading="memuat" stripe style="width:100%"
                empty-text="Belum ada data.">
        <el-table-column type="index" label="#" width="60" :index="(i) => (hal - 1) * PER_HAL + i + 1" />
        <el-table-column v-for="[k, l] in spek.kolom" :key="k" :prop="k" :label="l" min-width="140">
          <template #default="{ row }">
            <span :class="MONO.includes(k) ? 'num' : ''">{{ row[k] ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="" width="150" align="right">
          <template #default="{ row }">
            <el-button link @click="buka(row)">Ubah</el-button>
            <el-button link type="danger" @click="hapus(row)">Hapus</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="baris.length > PER_HAL" class="hal">
        <el-pagination layout="prev, pager, next, total" :total="baris.length"
                       :page-size="PER_HAL" :current-page="hal" @current-change="hal = $event" />
      </div>
    </div>

    <el-dialog v-model="dialog" :title="(sunting ? 'Ubah ' : 'Tambah ') + judul" width="440">
      <el-form label-position="top">
        <el-form-item v-for="[n, l, t, wajib] in spek.bidang" :key="n" :label="l" :required="wajib">
          <el-select v-if="t.startsWith('pilih:')" v-model="form[n]" clearable placeholder="— pilih —" style="width:100%">
            <el-option v-for="o in opsi(t.split(':')[1])" :key="o.id" :label="o.label" :value="o.id" />
          </el-select>
          <el-input v-else v-model="form[n]" :type="t === 'angka' ? 'number' : 'text'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">Batal</el-button>
        <el-button type="primary" :loading="sibuk" @click="simpan">Simpan</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.alat { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.tajuk { flex: 1; min-width: 160px; font-size: 20px; font-weight: 700; }
.hal { display: flex; justify-content: center; padding: 12px; }
</style>

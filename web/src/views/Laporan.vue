<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const route = useRoute()
const pilihan = ref([]); const kelas = ref(null)
const bentuk = ref('ringkas'); const cocokkan = ref('0')
const hasil = ref(null); const memuat = ref(false)

async function muat() {
  if (!kelas.value) { hasil.value = null; return }
  memuat.value = true
  try {
    hasil.value = await api.get(`/laporan/pratinjau?kelas=${kelas.value}&ruangan=${cocokkan.value}`)
  } catch (e) { ElMessage.error(e.message); hasil.value = null }
  finally { memuat.value = false }
}

function unduh() {
  window.location.href =
    `/api/laporan/unduh?kelas=${kelas.value}&bentuk=${bentuk.value}&ruangan=${cocokkan.value}`
}

watch([kelas, cocokkan], muat)

onMounted(async () => {
  pilihan.value = (await api.get('/laporan/pilihan')).pilihan
  const dariUrl = Number(route.query.kelas)
  if (dariUrl && pilihan.value.some((p) => p.id === dariUrl)) kelas.value = dariUrl
})
</script>

<template>
  <div>
    <h1 class="tajuk">Laporan Absensi</h1>

    <section class="kartu mb">
      <div class="kartu__isi alat">
        <el-select v-model="kelas" placeholder="— pilih blok dan kelas —" style="flex:1;min-width:260px" filterable>
          <el-option v-for="p in pilihan" :key="p.id" :label="p.label" :value="p.id" />
        </el-select>
        <el-select v-model="bentuk" style="width:210px">
          <el-option label="Ringkas — Status + Waktu" value="ringkas" />
          <el-option label="Lengkap — Ceklog 1, 2, Durasi" value="lengkap" />
        </el-select>
        <el-select v-model="cocokkan" style="width:190px">
          <el-option label="Ruangan: tidak dicocokkan" value="0" />
          <el-option label="Ruangan: dicocokkan" value="1" />
        </el-select>
        <el-button type="primary" :disabled="!hasil?.baris?.length" @click="unduh">
          <iconify-icon icon="lucide:download" width="15" style="margin-right:6px" /> Unduh .xlsx
        </el-button>
      </div>
    </section>

    <div v-if="hasil" class="angka">
      <div class="stat"><b class="num">{{ hasil.statistik.peserta }}</b><span>mahasiswa</span></div>
      <div class="stat"><b class="num">{{ hasil.statistik.sesi }}</b><span>sesi</span></div>
      <div class="stat"><b class="num">{{ hasil.statistik.persen_hadir }}%</b><span>kehadiran</span></div>
      <div class="stat"><b class="num">{{ hasil.statistik.tanpa_finger }}</b><span>tanpa ID Finger</span></div>
    </div>

    <section v-if="hasil?.baris?.length" class="kartu">
      <div class="kartu__kepala">
        <h2 class="kartu__judul">Pratinjau</h2>
        <span class="redup kecil">{{ hasil.baris.length }} dari {{ hasil.total_baris }} baris</span>
      </div>
      <div class="gulir" v-loading="memuat">
        <table class="rekap">
          <thead>
            <tr>
              <th rowspan="2">#</th><th rowspan="2">NIM</th><th rowspan="2" class="kiri">Nama</th>
              <th v-for="(s, i) in hasil.sesi" :key="i" :colspan="bentuk === 'lengkap' ? 3 : 2">
                {{ s.nama }}<br><span class="redup kecil">{{ s.label_tanggal }} · {{ s.jam_mulai }}–{{ s.jam_selesai }}</span>
              </th>
            </tr>
            <tr>
              <template v-for="(s, i) in hasil.sesi" :key="'s' + i">
                <th>Status</th>
                <th v-if="bentuk === 'lengkap'">Ceklog 1</th>
                <th v-if="bentuk === 'lengkap'">Ceklog 2</th>
                <th v-if="bentuk !== 'lengkap'">Waktu</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in hasil.baris" :key="b.no">
              <td class="redup num">{{ b.no }}</td>
              <td class="nim">{{ b.nim }}</td>
              <td class="kiri">{{ b.nama }}</td>
              <template v-for="(sel, i) in b.sel" :key="i">
                <td><span :class="'st st-' + sel.status">{{ sel.status }}</span></td>
                <template v-if="bentuk === 'lengkap'">
                  <td class="num">{{ sel.ceklog[0] || (['S','I'].includes(sel.status) ? sel.waktu : '—') }}</td>
                  <td class="num">{{ sel.ceklog[1] || (['S','I'].includes(sel.status) ? sel.waktu : '—') }}</td>
                </template>
                <td v-else class="num">{{ sel.waktu }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <el-empty v-else-if="kelas && !memuat" description="Tidak ada yang bisa ditampilkan. Periksa sesi dan peserta pada blok ini." />
  </div>
</template>

<style scoped>
.tajuk { font-size: 20px; font-weight: 700; margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.alat { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.angka { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,160px),1fr)); gap: 12px; margin-bottom: 16px; }
.stat { padding: 14px 16px; background: var(--color-surface); border: 1px solid var(--color-rule); border-radius: var(--radius-panel); }
.stat b { display: block; font-size: 20px; font-weight: 600; color: var(--color-ink); }
.stat span { font-size: 12.5px; color: var(--color-muted); }
.gulir { overflow: auto; max-height: 520px; }
.rekap { width: 100%; border-collapse: collapse; font-size: 13px; }
.rekap th, .rekap td {
  padding: 7px 10px; border-bottom: 1px solid var(--color-rule);
  text-align: center; white-space: nowrap;
}
.rekap thead th {
  position: sticky; top: 0; z-index: 2; background: var(--color-surface-2);
  font-weight: 500; color: var(--color-muted); font-size: 12px;
}
.rekap .kiri { text-align: left; }
.rekap tbody tr:hover { background: var(--color-surface-2); }
</style>

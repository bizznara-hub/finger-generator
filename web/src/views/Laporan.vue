<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import Konfeti from '@/komponen/Konfeti.vue'

const route = useRoute()
const pilihan = ref([]); const kelas = ref(null)
const bentuk = ref('ringkas'); const cocokkan = ref('0')
const hasil = ref(null); const memuat = ref(false); const konfeti = ref(null)
const hal = ref(1); const PER_HAL = 30
const halaman = computed(() =>
  (hasil.value?.baris || []).slice((hal.value - 1) * PER_HAL, hal.value * PER_HAL))

async function muat() {
  if (!kelas.value) { hasil.value = null; return }
  memuat.value = true
  try {
    hasil.value = await api.get(`/laporan/pratinjau?kelas=${kelas.value}&ruangan=${cocokkan.value}`)
    hal.value = 1
  } catch (e) { ElMessage.error(e.message); hasil.value = null }
  finally { memuat.value = false }
}

function unduh() {
  window.location.href =
    `/api/laporan/unduh?kelas=${kelas.value}&bentuk=${bentuk.value}&ruangan=${cocokkan.value}`
  // momen selesai — dirayakan sesuai sistem desain
  konfeti.value?.rayakan()
  ElMessage.success('Laporan sedang diunduh.')
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
    <Konfeti ref="konfeti" />
    <h1 class="tajuk"><span class="judul-bagian__emoji">📊</span> Laporan Absensi</h1>

    <section class="kartu kartu--emas mb">
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
      <div class="stat stat--emas berdenyut"><b class="num">{{ hasil.statistik.persen_hadir }}%</b><span>kehadiran</span></div>
      <div class="stat" :class="hasil.statistik.tanpa_finger ? 'stat--coral' : ''">
        <b class="num">{{ hasil.statistik.tanpa_finger }}</b><span>tanpa ID Finger</span>
      </div>
    </div>

    <section v-if="hasil?.baris?.length" class="kartu">
      <div class="kartu__kepala">
        <h2 class="kartu__judul judul-bagian"><span class="judul-bagian__emoji">👀</span> Pratinjau</h2>
        <span class="redup kecil">{{ hasil.total_baris }} baris</span>
      </div>
      <div class="gulir" v-loading="memuat">
        <table class="rekap">
          <thead>
            <tr>
              <th rowspan="2">No</th><th rowspan="2">NIM</th><th rowspan="2" class="kiri">Nama</th>
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
            <tr v-for="b in halaman" :key="b.no">
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
.tajuk { display: flex; align-items: center; gap: 8px; font-size: var(--text-h1); font-weight: 800; letter-spacing: 2px; margin-bottom: 16px; }
.mb { margin-bottom: 16px; }
.alat { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.angka { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%,160px),1fr)); gap: 12px; margin-bottom: 16px; }
.stat {
  position: relative; padding: 14px 16px 14px 20px;
  background: var(--surface-card); border-radius: var(--r-lg); box-shadow: var(--shadow-card);
  overflow: hidden;
}
.stat::before { content: ""; position: absolute; inset-block: 0; inset-inline-start: 0; width: 3px; background: var(--primary-light); }
.stat--emas::before { background: var(--accent); }
.stat--emas { box-shadow: var(--glow-accent); }
.stat--coral::before { background: var(--coral); }
.stat--coral { box-shadow: var(--glow-coral); }
.stat b { display: block; font-size: var(--text-h1); font-weight: 800; color: var(--ink); letter-spacing: 1px; }
.stat span { font-size: var(--text-sm); color: var(--ink-muted); font-weight: 600; }
.gulir { overflow: auto; max-height: 520px; }
.hal { display: flex; justify-content: center; padding: 12px; }
.rekap { width: 100%; border-collapse: collapse; font-size: 13px; }
.rekap th, .rekap td {
  padding: 7px 10px; border-bottom: 1px solid var(--primary-bg);
  text-align: center; white-space: nowrap;
}
.rekap thead th {
  position: sticky; top: 0; z-index: 2; background: var(--primary-bg);
  font-weight: 800; color: var(--primary-dark); font-size: var(--text-sm); letter-spacing: 1px;
}
.rekap .kiri { text-align: left; }
.rekap th:first-child, .rekap td:first-child { padding-left: 22px; }
.rekap th:last-child, .rekap td:last-child { padding-right: 22px; }
.rekap tbody tr:hover { background: var(--cream); }
</style>

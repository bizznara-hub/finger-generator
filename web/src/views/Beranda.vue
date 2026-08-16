<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api'

const data = ref(null)
const maks = computed(() => Math.max(1, ...(data.value?.tren || []).map((t) => t.jumlah)))

onMounted(async () => { data.value = await api.get('/beranda') })
</script>

<template>
  <div v-loading="!data">
    <template v-if="data">
      <div class="angka">
        <router-link v-for="a in data.angka" :key="a.label" :to="a.rute" class="angka__kartu">
          <span class="angka__ikon"><iconify-icon :icon="a.ikon" width="18" /></span>
          <span class="angka__nilai num">{{ a.nilai }}</span>
          <span class="angka__label">{{ a.label }}</span>
        </router-link>
      </div>

      <div class="baris">
        <section class="kartu tumbuh">
          <div class="kartu__kepala"><h2 class="kartu__judul judul-bagian"><span class="judul-bagian__emoji">📈</span> Scan per hari</h2>
            <span class="redup kecil" v-if="data.rentang.awal">{{ data.rentang.awal }} – {{ data.rentang.akhir }}</span>
          </div>
          <div class="kartu__isi">
            <div v-if="data.tren.length" class="grafik">
              <div v-for="t in data.tren" :key="t.tanggal" class="grafik__kolom">
                <span class="grafik__batang" :style="{ height: (t.jumlah / maks * 100) + '%' }" :title="t.jumlah + ' scan'" />
                <span class="grafik__label num">{{ t.tanggal }}</span>
              </div>
            </div>
            <p v-else class="petunjuk">
              Belum ada data mentah. Tarik dari att_log atau impor berkas lewat
              <router-link to="/finger-print">Finger Print</router-link>.
            </p>
          </div>
        </section>

        <section class="kartu">
          <div class="kartu__kepala">
            <h2 class="kartu__judul judul-bagian"><span class="judul-bagian__emoji">🔍</span> Tanpa ID Finger</h2>
            <el-tag v-if="data.tanpa_finger.length" type="warning" size="small" round>
              {{ data.tanpa_finger.length }}
            </el-tag>
          </div>
          <div class="kartu__isi">
            <p class="petunjuk">Tanpa ID Finger, mesin tidak mengenali mahasiswa dan statusnya selalu Alpa.</p>
            <el-scrollbar v-if="data.tanpa_finger.length" max-height="240px">
              <div v-for="m in data.tanpa_finger" :key="m.id" class="orang">
                <span class="nim">{{ m.nim }}</span>
                <span class="orang__nama">{{ m.nama }}</span>
              </div>
            </el-scrollbar>
            <el-result v-else icon="success" sub-title="Semua mahasiswa sudah punya ID Finger." />
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.angka { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 190px), 1fr)); gap: 12px; margin-bottom: 20px; }
.angka__kartu {
  position: relative; display: grid; grid-template-columns: auto 1fr; grid-template-rows: auto auto;
  gap: 2px 12px; padding: 16px 16px 16px 20px; text-decoration: none; overflow: hidden;
  background: var(--surface-card); border-radius: var(--r-lg); box-shadow: var(--shadow-card);
  transition: transform var(--dur) var(--bounce), box-shadow var(--dur) var(--bounce);
}
.angka__kartu::before {
  content: ""; position: absolute; inset-block: 0; inset-inline-start: 0;
  width: 3px; background: var(--primary-light);
}
.angka__kartu:hover { transform: translateY(-2px); box-shadow: var(--glow-teal); }
.angka__kartu:active { transform: scale(0.97); }
.angka__ikon {
  grid-row: 1 / 3; width: 40px; height: 40px; border-radius: var(--r-md); display: grid; place-items: center;
  background: var(--primary-bg); color: var(--primary-dark); align-self: center;
}
.angka__nilai { font-size: var(--text-h1); font-weight: 800; color: var(--ink); line-height: 1.2; letter-spacing: 1px; }
.angka__label { font-size: var(--text-sm); color: var(--ink-muted); font-weight: 600; }

.baris { display: grid; grid-template-columns: 1fr; gap: 16px; }
@media (min-width: 62rem) { .baris { grid-template-columns: 1.4fr 1fr; } }

.grafik { display: flex; align-items: flex-end; gap: 6px; height: 180px; }
.grafik__kolom { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; }
.grafik__batang {
  width: 100%; max-width: 34px; margin-top: auto; min-height: 3px;
  background: linear-gradient(180deg, var(--primary-light), var(--primary));
  border-radius: var(--r-sm) var(--r-sm) 0 0; opacity: 0.9;
  box-shadow: var(--glow-teal);
}
.grafik__kolom:hover .grafik__batang { opacity: 1; }
.grafik__label { font-size: var(--text-xs); color: var(--ink-muted); font-weight: 600; }

.orang { display: flex; gap: 12px; padding: 7px 0; border-bottom: 2px dashed var(--primary-bg); font-size: var(--text-sm); }
.orang:last-child { border-bottom: 0; }
.orang__nama { color: var(--ink-2); font-weight: 600; }
</style>

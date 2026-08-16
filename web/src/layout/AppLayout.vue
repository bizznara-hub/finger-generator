<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'
import { tandaiMasuk } from '@/router'

const route = useRoute()
const router = useRouter()

const ciut = ref(localStorage.getItem('rail-ciut') === '1')
const pengguna = ref(null)
const cariTerbuka = ref(false)
const kataCari = ref('')

const MENU = [
  { grup: 'Ikhtisar', item: [
    { ke: '/',             label: 'Beranda',      ikon: 'lucide:layout-dashboard' },
    { ke: '/finger-print', label: 'Finger Print', ikon: 'lucide:fingerprint' }
  ]},
  { grup: 'Data master', item: [
    { ke: '/master/departemen',  label: 'Departemen',   ikon: 'lucide:building-2' },
    { ke: '/master/kelas',       label: 'Kelas',        ikon: 'lucide:layout-grid' },
    { ke: '/master/dosen',       label: 'Dosen',        ikon: 'lucide:user-round' },
    { ke: '/master/mahasiswa',   label: 'Mahasiswa',    ikon: 'lucide:users' },
    { ke: '/master/mata-kuliah', label: 'Mata Kuliah',  ikon: 'lucide:book-open' },
    { ke: '/master/ruangan',     label: 'Ruang Kuliah', ikon: 'lucide:door-open' }
  ]},
  { grup: 'Kegiatan', item: [
    { ke: '/jadwal',              label: 'Jadwal Kuliah', ikon: 'lucide:calendar-days' },
    { ke: '/ketidakhadiran/S',    label: 'Sakit',         ikon: 'lucide:thermometer' },
    { ke: '/ketidakhadiran/I',    label: 'Izin',          ikon: 'lucide:mail' },
    { ke: '/laporan',             label: 'Laporan',       ikon: 'lucide:file-spreadsheet' }
  ]},
  { grup: 'Sistem', item: [
    { ke: '/pengaturan', label: 'Pengaturan', ikon: 'lucide:settings' },
    { ke: '/akun',       label: 'Akun',       ikon: 'lucide:key-round' }
  ]}
]

const semuaMenu = MENU.flatMap((g) => g.item)

const hasilCari = computed(() => {
  const k = kataCari.value.trim().toLowerCase()
  if (!k) return semuaMenu
  return semuaMenu.filter((m) => m.label.toLowerCase().includes(k))
})

/* ---------- tab halaman terbuka ---------- */
const tab = ref([{ jalur: '/', label: 'Beranda' }])

function judulRute(r) {
  if (r.name === 'master') {
    const m = semuaMenu.find((x) => x.ke === r.path)
    return m ? m.label : 'Data master'
  }
  return r.meta?.judul || 'Halaman'
}

watch(
  () => route.fullPath,
  () => {
    if (route.name === 'masuk') return
    const jalur = route.fullPath
    if (!tab.value.some((t) => t.jalur === jalur)) {
      tab.value.push({ jalur, label: judulRute(route) })
      if (tab.value.length > 10) tab.value.splice(1, 1)
    }
  },
  { immediate: true }
)

function tutupTab(jalur) {
  const i = tab.value.findIndex((t) => t.jalur === jalur)
  if (i <= 0) return
  tab.value.splice(i, 1)
  if (route.fullPath === jalur) router.push(tab.value[i - 1].jalur)
}

/* ---------- remah ---------- */
const remah = computed(() => {
  const bagian = [{ label: 'Beranda', ke: '/' }]
  const induk = route.meta?.induk
  if (induk && induk !== 'Ikhtisar') bagian.push({ label: induk })
  const j = judulRute(route)
  if (j !== 'Beranda') bagian.push({ label: j })
  return bagian
})

/* ---------- aksi ---------- */
function alihkanRail() {
  ciut.value = !ciut.value
  localStorage.setItem('rail-ciut', ciut.value ? '1' : '0')
}

function layarPenuh() {
  if (document.fullscreenElement) document.exitFullscreen()
  else document.documentElement.requestFullscreen()
}

async function keluar() {
  await ElMessageBox.confirm('Keluar dari aplikasi?', 'Konfirmasi', {
    confirmButtonText: 'Keluar', cancelButtonText: 'Batal', type: 'warning'
  })
  await jalankan(() => api.post('/keluar'))
  tandaiMasuk(false)
  router.push({ name: 'masuk' })
}

function pilihCari(m) {
  cariTerbuka.value = false
  kataCari.value = ''
  router.push(m.ke)
}

function pintasan(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    cariTerbuka.value = true
  }
}

onMounted(async () => {
  window.addEventListener('keydown', pintasan)
  try {
    const d = await api.get('/status')
    pengguna.value = d.pengguna
  } catch { /* penjaga router yang menangani */ }
})
</script>

<template>
  <div class="cangkang" :class="{ 'cangkang--ciut': ciut }">

    <!-- ============ RAIL ============ -->
    <aside class="rail">
      <div class="rail__merek">
        <span class="rail__logo"><iconify-icon icon="lucide:fingerprint" width="18" /></span>
        <span v-show="!ciut" class="rail__teks">
          <b>Absensi FK</b>
          <small>Universitas Hasanuddin</small>
        </span>
      </div>

      <nav class="rail__nav">
        <template v-for="g in MENU" :key="g.grup">
          <p v-show="!ciut" class="rail__grup">{{ g.grup }}</p>
          <router-link
            v-for="m in g.item" :key="m.ke" :to="m.ke" class="rail__tautan"
            :class="{ aktif: route.path === m.ke }" :title="ciut ? m.label : null">
            <iconify-icon :icon="m.ikon" width="17" />
            <span v-show="!ciut">{{ m.label }}</span>
          </router-link>
        </template>
      </nav>
    </aside>

    <div class="utama">

      <!-- ============ HEADER ============ -->
      <header class="kepala">
        <button class="ikon-btn" :title="ciut ? 'Lebarkan menu' : 'Ciutkan menu'" @click="alihkanRail">
          <iconify-icon :icon="ciut ? 'lucide:panel-left-open' : 'lucide:panel-left-close'" width="18" />
        </button>

        <el-breadcrumb separator="/" class="remah">
          <el-breadcrumb-item v-for="(b, i) in remah" :key="i" :to="b.ke ? { path: b.ke } : undefined">
            {{ b.label }}
          </el-breadcrumb-item>
        </el-breadcrumb>

        <div class="kepala__kanan">
          <button class="cari-btn" @click="cariTerbuka = true">
            <iconify-icon icon="lucide:search" width="15" />
            <span>Cari menu</span>
            <kbd>⌘K</kbd>
          </button>

          <button class="ikon-btn" title="Layar penuh" @click="layarPenuh">
            <iconify-icon icon="lucide:maximize" width="17" />
          </button>

          <el-dropdown trigger="click">
            <button class="profil">
              <span class="profil__avatar">{{ (pengguna?.nama || 'A').charAt(0) }}</span>
              <span class="profil__nama">{{ pengguna?.nama }}</span>
              <iconify-icon icon="lucide:chevron-down" width="14" />
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/akun')">Akun</el-dropdown-item>
                <el-dropdown-item @click="router.push('/pengaturan')">Pengaturan</el-dropdown-item>
                <el-dropdown-item divided @click="keluar">Keluar</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- ============ TAB HALAMAN ============ -->
      <div class="tab">
        <router-link
          v-for="t in tab" :key="t.jalur" :to="t.jalur" class="tab__item"
          :class="{ aktif: route.fullPath === t.jalur }">
          {{ t.label }}
          <span v-if="t.jalur !== '/'" class="tab__tutup"
                @click.prevent.stop="tutupTab(t.jalur)">
            <iconify-icon icon="lucide:x" width="12" />
          </span>
        </router-link>
      </div>

      <!-- ============ ISI ============ -->
      <main class="isi">
        <router-view v-slot="{ Component }">
          <transition name="pudar" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- ============ PENCARIAN ⌘K ============ -->
    <el-dialog v-model="cariTerbuka" width="440" :show-close="false" top="12vh" class="dialog-cari">
      <el-input v-model="kataCari" placeholder="Cari menu…" size="large" autofocus clearable>
        <template #prefix><iconify-icon icon="lucide:search" width="16" /></template>
      </el-input>
      <ul class="cari-hasil">
        <li v-for="m in hasilCari" :key="m.ke" @click="pilihCari(m)">
          <iconify-icon :icon="m.ikon" width="16" />
          <span>{{ m.label }}</span>
        </li>
        <li v-if="!hasilCari.length" class="kosong">Tidak ada menu yang cocok.</li>
      </ul>
    </el-dialog>
  </div>
</template>

<style scoped>
.cangkang { display: flex; min-height: 100vh; }

/* ---------------- rail ---------------- */
.rail {
  position: fixed; inset-block: 0; inset-inline-start: 0; z-index: 200;
  width: var(--rail-w); display: flex; flex-direction: column;
  background: var(--surface-card); box-shadow: 2px 0 12px rgba(43,168,162,0.08);
  transition: width 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.cangkang--ciut .rail { width: 64px; }

.rail__merek { display: flex; align-items: center; gap: 10px; padding: 16px; height: var(--header-h); }
.rail__logo {
  width: 32px; height: 32px; flex: none; border-radius: var(--r-md);
  background: linear-gradient(180deg, var(--primary-light), var(--primary)); color: #fff;
  display: grid; place-items: center; box-shadow: var(--glow-teal);
}
.rail__teks { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }
.rail__teks b { font-size: var(--text-h3); font-weight: 800; letter-spacing: 2px; color: var(--ink); white-space: nowrap; }
.rail__teks small { font-size: var(--text-xs); color: var(--ink-muted); white-space: nowrap; font-weight: 600; }

.rail__nav { flex: 1; overflow-y: auto; padding: 8px; }
.rail__grup {
  margin: 16px 8px 6px; padding-bottom: 6px; font-size: var(--text-xs); font-weight: 800;
  color: var(--primary-dark); text-transform: uppercase; letter-spacing: 3px;
  border-bottom: 3px dashed var(--primary-bg);
}
.rail__tautan {
  display: flex; align-items: center; gap: 10px; min-height: 36px;
  padding: 8px 12px; border-radius: var(--r-round);
  color: var(--ink-2); font-size: var(--text-body); font-weight: 700;
  text-decoration: none; white-space: nowrap;
  transition: transform var(--dur) var(--bounce), background-color var(--dur), color var(--dur);
}
.rail__tautan:hover { background: var(--primary-bg); color: var(--primary-dark); transform: translateX(2px); }
.rail__tautan.aktif { background: linear-gradient(90deg, var(--primary), var(--primary-light)); color: #fff; box-shadow: var(--glow-teal); }
.cangkang--ciut .rail__tautan { justify-content: center; padding: 8px; }

/* ---------------- utama ---------------- */
.utama { flex: 1; min-width: 0; margin-inline-start: var(--rail-w); transition: margin 0.2s cubic-bezier(0.16,1,0.3,1); }
.cangkang--ciut .utama { margin-inline-start: 64px; }

.kepala {
  position: sticky; top: 0; z-index: 100;
  height: var(--header-h); display: flex; align-items: center; gap: 12px;
  padding: 0 20px; background: color-mix(in srgb, var(--surface-card) 88%, transparent);
  backdrop-filter: blur(10px); border-bottom: 3px dashed var(--primary-bg);
}
.remah { flex: 1; min-width: 0; font-size: 13px; }
.kepala__kanan { display: flex; align-items: center; gap: 8px; }

.ikon-btn {
  width: 36px; height: 36px; display: grid; place-items: center;
  border: none; background: var(--primary-bg); color: var(--primary-dark);
  border-radius: var(--r-round); cursor: pointer;
  transition: transform var(--dur) var(--bounce), box-shadow var(--dur);
}
.ikon-btn:hover { box-shadow: var(--glow-teal); }
.ikon-btn:active { transform: scale(0.95); }

.cari-btn {
  display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 14px;
  border: none; border-radius: var(--r-round);
  background: var(--cream); color: var(--primary-dark); font: inherit;
  font-size: var(--text-sm); font-weight: 700; cursor: pointer;
  transition: transform var(--dur) var(--bounce), box-shadow var(--dur);
}
.cari-btn:hover { box-shadow: var(--glow-accent); }
.cari-btn:active { transform: scale(0.95); }
.cari-btn kbd {
  font-family: var(--font-mono); font-size: var(--text-xs); padding: 1px 6px;
  border-radius: var(--r-round); background: var(--accent); color: var(--primary-dark); font-weight: 700;
}

.profil {
  display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 12px 0 4px;
  border: none; background: var(--primary-bg); border-radius: var(--r-round);
  color: var(--primary-dark); font: inherit; font-size: var(--text-sm); font-weight: 700; cursor: pointer;
  transition: transform var(--dur) var(--bounce);
}
.profil:active { transform: scale(0.95); }
.profil__avatar {
  width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
  background: linear-gradient(180deg, var(--accent-light), var(--accent));
  color: var(--primary-dark); font-size: var(--text-sm); font-weight: 800;
}

/* ---------------- tab ---------------- */
.tab {
  display: flex; gap: 4px; align-items: center; height: var(--tab-h);
  padding: 0 20px; overflow-x: auto;
  background: var(--surface-card); border-bottom: 3px dashed var(--primary-bg);
}
.tab__item {
  display: inline-flex; align-items: center; gap: 6px; flex: none;
  height: 28px; padding: 0 14px; border-radius: var(--r-round);
  background: var(--primary-bg); color: var(--primary-dark);
  font-size: var(--text-sm); font-weight: 700; text-decoration: none; white-space: nowrap;
  transition: transform var(--dur) var(--bounce), box-shadow var(--dur);
}
.tab__item:hover { transform: translateY(-1px); }
.tab__item.aktif { background: linear-gradient(180deg, var(--accent-light), var(--accent)); color: var(--primary-dark); box-shadow: var(--glow-accent); }
.tab__tutup { display: grid; place-items: center; border-radius: 50%; padding: 1px; }
.tab__tutup:hover { background: rgb(0 0 0 / 0.08); }

/* ---------------- isi ---------------- */
.isi { padding: 24px 20px 64px; }

.pudar-enter-active, .pudar-leave-active { transition: opacity 0.15s ease; }
.pudar-enter-from, .pudar-leave-to { opacity: 0; }

/* ---------------- pencarian ---------------- */
.cari-hasil { list-style: none; margin: 12px 0 0; padding: 0; max-height: 300px; overflow-y: auto; }
.cari-hasil li {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: var(--r-round); cursor: pointer; font-size: var(--text-body);
  font-weight: 700; color: var(--ink-2);
}
.cari-hasil li:hover { background: var(--primary-bg); color: var(--primary-dark); }
.cari-hasil li.kosong { color: var(--ink-muted); cursor: default; justify-content: center; }
.cari-hasil li.kosong:hover { background: transparent; }

@media (max-width: 60rem) {
  .rail { transform: translateX(-100%); }
  .cangkang--ciut .rail { transform: none; width: var(--rail-w); }
  .utama, .cangkang--ciut .utama { margin-inline-start: 0; }
  .cari-btn span { display: none; }
  .profil__nama { display: none; }
}
</style>

<style>
.dialog-cari .el-dialog__header { display: none; }
.dialog-cari .el-dialog__body { padding: 16px; }
</style>

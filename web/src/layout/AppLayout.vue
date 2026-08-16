<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'
import { tandaiMasuk } from '@/router'

const route = useRoute()
const router = useRouter()

const ciut = ref(localStorage.getItem('rail-ciut') === '1')
const pengguna = ref(null)

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
    { ke: '/jadwal',           label: 'Jadwal Kuliah', ikon: 'lucide:calendar-days' },
    { ke: '/ketidakhadiran/S', label: 'Sakit',         ikon: 'lucide:thermometer' },
    { ke: '/ketidakhadiran/I', label: 'Izin',          ikon: 'lucide:mail' },
    { ke: '/laporan',          label: 'Laporan',       ikon: 'lucide:file-spreadsheet' }
  ]},
  { grup: 'Sistem', item: [
    { ke: '/pengaturan', label: 'Pengaturan', ikon: 'lucide:settings' },
    { ke: '/akun',       label: 'Akun',       ikon: 'lucide:key-round' }
  ]}
]

const semuaMenu = MENU.flatMap((g) => g.item)

function judulRute(r) {
  if (r.name === 'master') {
    const m = semuaMenu.find((x) => x.ke === r.path)
    return m ? m.label : 'Data master'
  }
  return r.meta?.judul || 'Halaman'
}

const remah = computed(() => {
  const bagian = [{ label: 'Beranda', ke: '/' }]
  const induk = route.meta?.induk
  if (induk && induk !== 'Ikhtisar') bagian.push({ label: induk })
  const j = judulRute(route)
  if (j !== 'Beranda') bagian.push({ label: j })
  return bagian
})

function alihkanRail() {
  ciut.value = !ciut.value
  localStorage.setItem('rail-ciut', ciut.value ? '1' : '0')
}

async function keluar() {
  await ElMessageBox.confirm('Keluar dari aplikasi?', 'Konfirmasi', {
    confirmButtonText: 'Keluar', cancelButtonText: 'Batal', type: 'warning'
  })
  await jalankan(() => api.post('/keluar'))
  tandaiMasuk(false)
  router.push({ name: 'masuk' })
}

onMounted(async () => {
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
        <img class="rail__logo" src="/logo.png" alt="Logo" width="32" height="32">
        <span v-show="!ciut" class="rail__teks">
          <b>Finger FK</b>
          <small>Megabuana Palopo</small>
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
      </header>

      <!-- ============ ISI ============ -->
      <main class="isi">
        <router-view v-slot="{ Component }">
          <transition name="pudar" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.cangkang { display: flex; min-height: 100vh; }

/* ---------------- rail ---------------- */
.rail {
  position: fixed; inset-block: 0; inset-inline-start: 0; z-index: 200;
  width: var(--rail-w); display: flex; flex-direction: column;
  background: var(--surface-card); box-shadow: 2px 0 12px rgba(43, 168, 162, 0.08);
  transition: width 0.2s var(--bounce);
}
.cangkang--ciut .rail { width: 64px; }

.rail__merek { display: flex; align-items: center; gap: 10px; padding: 16px; height: var(--header-h); }
.rail__logo {
  width: 32px; height: 32px; flex: none;
  object-fit: contain;
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
.rail__tautan.aktif {
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
  color: #fff; box-shadow: var(--glow-teal);
}
.cangkang--ciut .rail__tautan { justify-content: center; padding: 8px; }

/* ---------------- utama ---------------- */
.utama { flex: 1; min-width: 0; margin-inline-start: var(--rail-w); transition: margin 0.2s var(--bounce); }
.cangkang--ciut .utama { margin-inline-start: 64px; }

.kepala {
  position: sticky; top: 0; z-index: 100;
  height: var(--header-h); display: flex; align-items: center; gap: 12px;
  padding: 0 20px; background: color-mix(in srgb, var(--surface-card) 88%, transparent);
  backdrop-filter: blur(10px); border-bottom: 3px dashed var(--primary-bg);
}
.remah { flex: 1; min-width: 0; font-size: var(--text-sm); }

.ikon-btn {
  width: 36px; height: 36px; display: grid; place-items: center;
  border: none; background: var(--primary-bg); color: var(--primary-dark);
  border-radius: var(--r-round); cursor: pointer;
  transition: transform var(--dur) var(--bounce), box-shadow var(--dur);
}
.ikon-btn:hover { box-shadow: var(--glow-teal); }
.ikon-btn:active { transform: scale(0.95); }

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

/* ---------------- isi ---------------- */
.isi { padding: 24px 20px 64px; }

.pudar-enter-active, .pudar-leave-active { transition: opacity 0.15s ease; }
.pudar-enter-from, .pudar-leave-to { opacity: 0; }

@media (max-width: 60rem) {
  .rail { transform: translateX(-100%); }
  .cangkang--ciut .rail { transform: none; width: var(--rail-w); }
  .utama, .cangkang--ciut .utama { margin-inline-start: 0; }
  .profil__nama { display: none; }
}
</style>

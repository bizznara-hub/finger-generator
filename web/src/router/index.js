import { createRouter, createWebHistory } from 'vue-router'
import { api } from '@/api'

const rute = [
  { path: '/masuk', name: 'masuk', component: () => import('@/views/Masuk.vue'), meta: { bebas: true, judul: 'Masuk' } },
  {
    path: '/',
    component: () => import('@/layout/AppLayout.vue'),
    children: [
      { path: '', name: 'beranda', component: () => import('@/views/Beranda.vue'), meta: { judul: 'Beranda', induk: 'Ikhtisar' } },
      { path: 'finger-print', name: 'finger', component: () => import('@/views/FingerPrint.vue'), meta: { judul: 'Finger Print', induk: 'Ikhtisar' } },
      { path: 'finger-print/log', name: 'log-scan', component: () => import('@/views/LogScan.vue'), meta: { judul: 'Log scan', induk: 'Finger Print' } },
      { path: 'master/:kunci', name: 'master', component: () => import('@/views/Master.vue'), meta: { judul: 'Data master', induk: 'Data master' } },
      { path: 'jadwal', name: 'jadwal', component: () => import('@/views/Jadwal.vue'), meta: { judul: 'Jadwal Kuliah', induk: 'Kegiatan' } },
      { path: 'jadwal/kelas/:id', name: 'jadwal-kelas', component: () => import('@/views/JadwalKelas.vue'), meta: { judul: 'Sesi kelas', induk: 'Jadwal Kuliah' } },
      { path: 'ketidakhadiran/:jenis', name: 'ketidakhadiran', component: () => import('@/views/Ketidakhadiran.vue'), meta: { judul: 'Ketidakhadiran', induk: 'Kegiatan' } },
      { path: 'laporan', name: 'laporan', component: () => import('@/views/Laporan.vue'), meta: { judul: 'Laporan', induk: 'Kegiatan' } },
      { path: 'pengaturan', name: 'pengaturan', component: () => import('@/views/Pengaturan.vue'), meta: { judul: 'Pengaturan', induk: 'Sistem' } },
      { path: 'akun', name: 'akun', component: () => import('@/views/Akun.vue'), meta: { judul: 'Akun', induk: 'Sistem' } }
    ]
  },
  { path: '/:sisa(.*)*', redirect: '/' }
]

const router = createRouter({ history: createWebHistory(), routes: rute })

let sudahCek = false
let masuk = false

router.beforeEach(async (ke) => {
  if (!sudahCek) {
    try {
      const d = await api.get('/status')
      masuk = !!d.pengguna
    } catch {
      masuk = false
    }
    sudahCek = true
  }
  if (!ke.meta.bebas && !masuk) return { name: 'masuk', query: { lanjut: ke.fullPath } }
  if (ke.name === 'masuk' && masuk) return { name: 'beranda' }
  return true
})

export function tandaiMasuk(nilai) {
  masuk = nilai
  sudahCek = true
}

export default router

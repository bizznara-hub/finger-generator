<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { api, jalankan } from '@/api'

const d = ref({ baris: [], total: 0, hal: 1, halaman_akhir: 1 })
const kata = ref(''); const memuat = ref(false)

async function muat(hal = 1) {
  memuat.value = true
  try { d.value = await api.get(`/mentah/log?hal=${hal}&cari=${encodeURIComponent(kata.value)}`) }
  finally { memuat.value = false }
}

async function kosongkan() {
  await ElMessageBox.confirm(
    `Hapus SEMUA ${d.value.total} baris log scan? Tindakan ini tidak bisa dibatalkan.`,
    'Konfirmasi', { confirmButtonText: 'Hapus semua', cancelButtonText: 'Batal', type: 'error' })
  await jalankan(() => api.del('/mentah/log'))
  await muat()
}

onMounted(() => muat())
</script>

<template>
  <div>
    <div class="alat">
      <h1 class="tajuk">Log scan <span class="redup kecil">{{ d.total }} baris</span></h1>
      <el-input v-model="kata" placeholder="Cari ID Finger…" clearable style="width:200px"
                @keyup.enter="muat()" @clear="muat()" />
      <el-button @click="muat()"><iconify-icon icon="lucide:search" width="15" /></el-button>
      <el-button v-if="d.total" type="danger" plain @click="kosongkan">Kosongkan</el-button>
    </div>

    <div class="kartu">
      <el-table :data="d.baris" v-loading="memuat" stripe empty-text="Belum ada data scan.">
        <el-table-column label="ID Finger" width="120">
          <template #default="{ row }"><b class="num">{{ row.id_finger }}</b></template>
        </el-table-column>
        <el-table-column prop="nama_mesin" label="Nama di mesin" min-width="140">
          <template #default="{ row }"><span class="redup">{{ row.nama_mesin || '—' }}</span></template>
        </el-table-column>
        <el-table-column label="Tanggal" width="130">
          <template #default="{ row }"><span class="num">{{ row.tanggal }}</span></template>
        </el-table-column>
        <el-table-column label="Jam" width="90">
          <template #default="{ row }"><span class="num">{{ row.jam }}</span></template>
        </el-table-column>
        <el-table-column label="Serial" min-width="140">
          <template #default="{ row }"><span class="num redup">{{ row.serial || '—' }}</span></template>
        </el-table-column>
        <el-table-column label="Sumber" width="110">
          <template #default="{ row }"><el-tag size="small" type="info">{{ row.sumber }}</el-tag></template>
        </el-table-column>
      </el-table>
    </div>

    <el-pagination v-if="d.halaman_akhir > 1" class="hal" layout="prev, pager, next"
                   :page-count="d.halaman_akhir" :current-page="d.hal" @current-change="muat" />
  </div>
</template>

<style scoped>
.alat { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.tajuk { flex: 1; min-width: 160px; font-size: 20px; font-weight: 700; }
.hal { margin-top: 16px; justify-content: center; }
</style>

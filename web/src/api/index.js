// Klien API tipis. Semua permintaan membawa cookie sesi.
import { ElMessage } from 'element-plus'

const DASAR = '/api'

async function minta(jalur, opsi = {}) {
  const r = await fetch(DASAR + jalur, { credentials: 'same-origin', ...opsi })

  if (r.status === 401) {
    // sesi habis — biarkan router yang mengarahkan ke halaman masuk
    window.dispatchEvent(new CustomEvent('sesi-habis'))
    throw new Error('Sesi berakhir. Silakan masuk kembali.')
  }

  const jenis = r.headers.get('content-type') || ''
  if (!jenis.includes('application/json')) {
    if (!r.ok) throw new Error(`Permintaan gagal (${r.status}).`)
    return r
  }

  const d = await r.json()
  if (!r.ok) throw new Error(d.error || `Permintaan gagal (${r.status}).`)
  return d
}

const json = (metode) => (jalur, badan) =>
  minta(jalur, {
    method: metode,
    headers: { 'Content-Type': 'application/json' },
    body: badan === undefined ? undefined : JSON.stringify(badan)
  })

export const api = {
  get: (jalur) => minta(jalur),
  post: json('POST'),
  put: json('PUT'),
  del: json('DELETE'),
  unggah: (jalur, formData) => minta(jalur, { method: 'POST', body: formData })
}

// Bungkus pemanggilan supaya galat selalu tampil sebagai pesan, bukan diam.
export async function jalankan(fn, { sukses } = {}) {
  try {
    const hasil = await fn()
    if (sukses) ElMessage.success(typeof sukses === 'string' ? sukses : hasil?.pesan)
    else if (hasil?.pesan) ElMessage.success(hasil.pesan)
    return hasil
  } catch (e) {
    ElMessage.error(e.message)
    throw e
  }
}

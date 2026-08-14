# PRD — Sistem Absensi Fakultas Kedokteran

**Status:** draf untuk disetujui
**Versi:** 0.1
**Tanggal:** 14 Agustus 2026

---

## 1. Latar belakang

Fakultas sudah punya aplikasi absensi berbasis PHP (`absensi/`) yang menarik data
dari mesin fingerprint Fingerspot dan mencetak laporan kehadiran per blok. Aplikasi
itu kini bermasalah:

| Masalah | Akibat |
|---|---|
| Seluruh kode memakai `mysql_*` yang dihapus sejak PHP 7 (2015) | Aplikasi tidak bisa dijalankan di server mana pun yang masih didukung |
| Laporan diekspor sebagai HTML ber-ekstensi `.xls` | Bukan berkas Excel sungguhan; tanpa sel, tanpa rumus |
| Laporan hanya mengenal status **H** dan **A** | Kolom S, I, Total Kehadiran, dan rumus persentase diketik manual di Excel setiap kali |
| Tidak ada pencatatan sakit dan izin | Tidak ada jejak; keputusan status bergantung ingatan petugas |
| Penyaringan kehadiran mengabaikan ruangan | Mahasiswa yang menempel di mesin ruangan mana pun tetap dihitung hadir |
| Validasi masukan hanya `addslashes`, ID di URL disamarkan MD5 | Rawan penyusupan SQL dan akses tanpa izin |

Bukti bahwa laporan disunting manual: pada berkas rujukan
`data jadi - Rekapan Absensi PBL Kelas A Blok NEUROLOGI Angk 2024.xlsx`,
seluruh kolom *Waktu* berisi teks `MANUAL`, dan judulnya memuat salah ketik
`SEMESETER` yang persis sama dengan yang ada di `reports/absen_mahasiswa.php`.

## 2. Tujuan

1. Menggantikan aplikasi PHP lama dengan aplikasi yang berjalan di lingkungan modern.
2. Menghasilkan laporan absensi per blok dalam **`.xlsx` sungguhan**, lengkap dengan
   status H/A/S/I, Total Kehadiran, dan rumus persentase — tanpa penyuntingan manual.
3. Menyediakan **dua jalur** pengambilan data mentah: tarik langsung dari `att_log`
   Fingerspot, dan impor berkas hasil ekspor mesin.
4. Mencatat sakit dan izin sebagai data, bukan koreksi manual di Excel.

### Bukan tujuan (versi ini)

- Akun untuk dosen dan mahasiswa (hanya **admin**, sesuai keputusan).
- Aplikasi seluler dan notifikasi.
- Absensi dosen (menyusul; struktur data sudah disiapkan).
- Migrasi otomatis data dari database PHP lama.

## 3. Pengguna

**Admin** — satu-satunya peran. Mengelola seluruh data master, menyusun jadwal,
menarik/mengimpor data mesin, mencatat sakit-izin, dan mencetak laporan.

## 4. Tech stack

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Bahasa | Python 3.11 | Pembaca `.xls` mesin dan penulis `.xlsx` sudah jadi dan teruji di Python |
| Kerangka web | Flask 3 | Ringan, tanpa proses build, cocok untuk aplikasi CRUD |
| ORM | SQLAlchemy 2 + Flask-SQLAlchemy | Netral terhadap SQLite maupun PostgreSQL |
| Basis data | SQLite (lokal) / PostgreSQL (bila `DATABASE_URL` diisi) | Bisa mulai tanpa layanan luar, naik kelas kapan saja |
| Sumber att_log | PyMySQL, koneksi **baca saja** ke MySQL Fingerspot | Tidak menyentuh basis data mesin |
| Pembaca berkas mesin | pandas + xlrd | Sudah terbukti membaca 3 format ekspor mesin |
| Penulis laporan | openpyxl | `.xlsx` asli, mendukung rumus dan penggabungan sel |
| Antarmuka | Jinja2 + HTML/CSS/JS biasa | Tanpa npm, tanpa build; satu perintah jalan |
| Autentikasi | Sesi Flask + hash sandi Werkzeug | Cukup untuk peran tunggal |

### Alternatif yang dipertimbangkan

**PHP 8 + Laravel.** Paling dekat dengan aplikasi lama dan mungkin lebih akrab bagi
tim pemelihara. Ditolak karena bagian tersulit — membaca `.xls` BIFF8 keluaran mesin
dan menulis `.xlsx` berformat rumit — sudah selesai dan teruji di Python; menulis
ulang bagian itu adalah risiko terbesar tanpa imbalan.

**Next.js / React.** Ditolak karena aplikasi ini didominasi formulir CRUD, dan
menambah rantai build JavaScript hanya mempersulit pemasangan di lingkungan kampus.

## 5. Model data

```
departemen ─┬─ dosen (id_finger)
            ├─ kelas ── mahasiswa (id_finger, nim)
            └─ mata_kuliah (= Blok)
                    │
ruangan ── mesin (serial, ip)        pengaturan (menit_perjam, menit_pergantian,
   │                                              toleransi, koneksi att_log)
   │
   └── jadwal ── jadwal_kelas ─┬─ jadwal_hari ── jadwal_jam ── jadwal_dosen
                               └─ jadwal_mahasiswa

log_scan (id_finger, tanggal, jam, serial, sumber)
ketidakhadiran (mahasiswa, jenis S/I, tanggal, sesi, keterangan)
pengguna (admin)
```

Hierarki jadwal diambil apa adanya dari aplikasi lama karena sudah tepat:
**jadwal** (penawaran blok) → **jadwal_kelas** (kelas peserta) → **jadwal_hari**
(tanggal) → **jadwal_jam** (sesi).

Kunci penghubung mesin dan orang adalah `id_finger`, tersimpan di tabel
`mahasiswa` dan `dosen`, dicocokkan dengan `att_log.pin` atau kolom User ID pada
berkas ekspor.

## 6. Modul dan menu

| Menu | Fungsi |
|---|---|
| Beranda | Ringkasan: jumlah mahasiswa, blok berjalan, scan terakhir masuk, mahasiswa yang belum punya `id_finger` |
| Finger Print | Daftar mesin (serial, IP, ruangan). Tarik dari `att_log`, impor berkas `.xls`, lihat log scan |
| Departemen | CRUD |
| Kelas | CRUD, berisi daftar mahasiswanya |
| Dosen | CRUD + `id_finger` |
| Mahasiswa | CRUD + `id_finger` + impor massal dari Excel/CSV |
| Mata Kuliah | CRUD blok |
| Ruang Kuliah | CRUD |
| Jadwal Kuliah | Susun blok → kelas → tanggal → **sesi**. Sesi dibuat manual dan bisa diubah |
| Sakit | Catat mahasiswa sakit per tanggal atau per sesi |
| Izin | Sama, dengan jenis izin |
| Laporan | Pilih blok + kelas → pratinjau → unduh `.xlsx` |
| Pengaturan | Menit per jam, menit pergantian, toleransi, identitas kop, koneksi att_log |
| Akun | Ubah nama, username, sandi |

## 7. Aturan penentuan status

Untuk setiap **mahasiswa × sesi**, berurutan:

1. Ada catatan **Sakit** yang berlaku → **S**
2. Ada catatan **Izin** yang berlaku → **I**
3. Ada scan dalam jendela waktu sesi → **H**, kolom *Waktu* diisi scan pertama
4. Selain itu → **A**

**Jendela waktu sesi:**

```
jam_selesai = jam_masuk + (jml_jam × menit_perjam) + ((jml_jam − 1) × menit_pergantian)
jendela      = [jam_masuk − toleransi_awal, jam_selesai + toleransi_akhir]
```

Rumus jam selesai diambil dari aplikasi lama. Admin boleh menimpanya dengan
jam selesai manual per sesi.

**Pencocokan ruangan.** Bila sesi punya ruangan dan mesin sudah dipetakan ke
ruangan, scan hanya dihitung bila berasal dari mesin di ruangan tersebut. Bisa
dimatikan di Pengaturan, karena aplikasi lama tidak menerapkannya.

**Pembulatan jam.** Mesin menulis `07:33:59.941` untuk pukul **07:34**; detik ≥ 30
dibulatkan ke atas sebelum disimpan.

## 8. Keluaran laporan

Mengikuti berkas rujukan, dalam `.xlsx` asli:

```
LAPORAN ABSEN MAHASISWA SEMESTER {semester} {tahun ajaran}
FAKULTAS KEDOKTERAN
UNIVERSITAS HASANUDDIN

Blok:  {nama blok}
Kelas: {nama kelas}

┌────┬─────┬──────┬──────────────────┬─────┬─ ... ─┬────────────────┬───────┬────────┐
│ No │ NIM │ Nama │ Senin, 23/02/2026│ ... │       │Jumlah Kehadiran│ Total │Persen  │
│    │     │      │ PBL 1 (MODUL 1)  │     │       │  H │ A │ S │ I │       │        │
│    │     │      │  08.00 - 09.35   │     │       │    │   │   │   │       │        │
│    │     │      │ Status  │ Waktu  │     │       │    │   │   │   │       │        │
└────┴─────┴──────┴─────────┴────────┴─────┴─ ... ─┴────┴───┴───┴───┴───────┴────────┘
```

Rumus ditulis hidup, bukan angka mati:

- `H` = `COUNTIF(<rentang sesi>;"H")`, demikian pula A, S, I
- `Total Kehadiran` = `H + S + I`
- `Persentasi (%)` = `Total ÷ jumlah sesi`, format `0%`

Dua bentuk kolom tersedia saat mencetak:

- **Ringkas** — `Status | Waktu`, sama persis dengan berkas rujukan (baku)
- **Lengkap** — `Status | Ceklog 1 | Ceklog 2 | Durasi (jam)` + kolom Total Jam

> Catatan: rumus di berkas rujukan mengandung dua kekeliruan yang akan diperbaiki —
> `COUNTIF(D12:P12;"A")` yang rentangnya bocor ke kolom rekap, dan `=T12:T145/6`
> yang rapuh di Excel versi baru.

## 9. Dua jalur data mentah

**Jalur A — tarik dari att_log.** Aplikasi menyambung baca-saja ke MySQL Fingerspot,
mengambil `att_log` (`pin`, `scan_date`, `sn`) untuk rentang tanggal tertentu, lalu
menyimpannya ke `log_scan`. Butuh aplikasi berada di jaringan yang sama dengan
server Fingerspot.

**Jalur B — impor berkas.** Admin mengunggah hasil ekspor mesin. Tiga format dikenali:

| Ekspor | Kelengkapan |
|---|---|
| Catatan Kehadiran Karyawan | Paling lengkap — seluruh sentuhan jari |
| Laporan Kehadiran | ±14% scan hilang karena dipaksa masuk slot pagi/siang/lembur |
| Kehadiran Tidak Normal | Paling sedikit; Sabtu dan Minggu tidak ikut terekspor |

Keduanya menulis ke tabel yang sama dan menandai `sumber`. Scan kembar
(`id_finger` + tanggal + jam + serial) diabaikan, sehingga impor berulang aman.

## 10. Keamanan

- Sandi disimpan sebagai hash (Werkzeug), bukan teks polos.
- Seluruh query lewat SQLAlchemy — tidak ada perangkaian string SQL.
- ID pada URL memakai angka biasa, dan setiap permintaan diperiksa haknya —
  MD5 pada aplikasi lama bukan otorisasi, hanya penyamaran.
- Sesi tidak diikat ke alamat IP, agar tidak putus saat jaringan berpindah.
- Koneksi att_log memakai kredensial **baca saja**.
- Berkas berisi data pribadi tidak pernah ikut ke repositori.

## 11. Pemasangan

| Cara | Keterangan |
|---|---|
| Lokal | `./jalankan.sh`, data di `data.db` (SQLite). Bisa memakai kedua jalur data |
| Server kampus | Sama, ditambah PostgreSQL lewat `DATABASE_URL` |
| Vercel | Hanya bila `DATABASE_URL` diisi. Jalur att_log **tidak bisa** dipakai kecuali MySQL Fingerspot dapat dijangkau dari internet |

## 12. Batasan yang diketahui

1. **Mesin tidak mencatat ruangan pada berkas ekspor.** Ekspor `.xls` hanya memuat
   User ID, tanggal, dan jam. Pencocokan ruangan hanya mungkin lewat jalur att_log,
   yang menyimpan `sn` mesin.
2. **Mahasiswa tanpa `id_finger` akan selalu A.** Beranda menampilkan daftarnya
   supaya ketahuan sejak awal.
3. **Sesi yang bertumpang waktu di ruang berbeda** tidak bisa dibedakan bila
   pencocokan ruangan dimatikan.
4. Data pada contoh berkas mentah bulan Juli 2026 hanya memuat 53 pengguna mesin,
   bukan 167 mahasiswa — pemetaan `id_finger` untuk mahasiswa masih harus disiapkan.

## 13. Tahapan pengerjaan

| Tahap | Isi |
|---|---|
| 1 | Kerangka aplikasi, basis data, autentikasi, tata letak sidebar |
| 2 | Data master: departemen, kelas, mahasiswa, dosen, ruangan, mata kuliah, mesin |
| 3 | Jadwal kuliah: blok → kelas → tanggal → sesi, plus pendaftaran peserta |
| 4 | Dua jalur data mentah + halaman log scan |
| 5 | Sakit dan izin |
| 6 | Laporan: pratinjau dan unduh `.xlsx` |
| 7 | Pengaturan, akun, beranda |
| 8 | Impor massal mahasiswa, pengujian dengan data asli |

## 14. Tolok ukur keberhasilan

1. Laporan satu blok dapat dicetak tanpa satu pun penyuntingan manual di Excel.
2. Berkas hasil dibuka di Excel menampilkan rumus hidup pada kolom H/A/S/I,
   Total Kehadiran, dan Persentasi.
3. Data mentah bulan Juli 2026 dapat diimpor dan menghasilkan angka yang sama
   dengan perhitungan manual.
4. Aplikasi berjalan pada Python yang masih didukung, tanpa peringatan usang.

---

## Yang masih perlu diputuskan

1. **Kredensial `att_log`** — host, nama basis data, pengguna, sandi. Tanpa ini
   jalur A tidak bisa diuji.
2. **Pencocokan ruangan** — dinyalakan atau dimatikan secara baku?
3. **Impor massal mahasiswa** — bentuk berkasnya seperti apa? Idealnya satu berkas
   berisi NIM, nama, kelas, dan `id_finger` sekaligus.
4. **Migrasi data lama** — apakah isi `db_absenfkuh` yang sekarang perlu dipindahkan,
   atau mulai dari data baru?

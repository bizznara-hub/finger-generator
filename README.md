# Generator Rekap Absensi Fingerprint

Aplikasi web untuk mengubah **data mentah** hasil ekspor mesin fingerprint menjadi
**rekap absensi** dengan tata letak yang sama seperti berkas referensi
`data jadi - Rekapan Absensi PBL ... .xlsx`.

## Menjalankan

```bash
cd app
./jalankan.sh
```

Lalu buka <http://127.0.0.1:5057>. Perintah pertama akan menyiapkan lingkungan Python
otomatis (butuh `python3`); jalankan berikutnya langsung menyala.

## Alur pemakaian

1. **Unggah data mentah** — boleh beberapa file sekaligus, hasilnya digabung dan
   duplikatnya dibuang.
2. **Tentukan sesi** — aplikasi mengambil *tanggal* dari data, lalu menerapkan jadwal:
   satu sesi per hari, mulai **07.30**, selesai mengikuti scan terakhir pada rumpun pertama
   hari itu. Kolom *Jam asli di data* ditampilkan sebagai pembanding. Beri nama sesi
   (`PBL 1 (MODUL 1)`), rapikan jamnya, hapus hari yang bukan kegiatan pembelajaran.
3. **Daftar peserta** — isi NIM dan nama lengkap, atau unduh template CSV,
   isi di Excel, lalu unggah kembali.
4. **Judul laporan** — kop, blok, kelas, nama file.
5. **Pratinjau & unduh** — periksa hasilnya, lalu unduh `.xlsx`.

## Format masukan yang didukung

| Ekspor mesin | Kelengkapan |
|---|---|
| **Catatan Kehadiran Karyawan** | Paling lengkap — semua sentuhan jari |
| Laporan Kehadiran | ±14% scan hilang karena dipaksa ke slot pagi/siang/lembur |
| Kehadiran Tidak Normal | Paling sedikit; hari Sabtu/Minggu tidak ikut terekspor |

Bila ragu, unggah **Catatan Kehadiran Karyawan**. Mengunggah beberapa file sekaligus aman
karena aplikasi menggabungkan dan membuang duplikat.

## Jadwal sesi

Jam mulai **tidak** diambil dari data mentah, melainkan dari jadwal pembelajaran
(baku **07.30**, bisa diubah di langkah 2). Ini disengaja: bila jam mulai ditarik dari
scan paling awal, jendelanya jadi melingkar — siapa pun yang menempel otomatis dianggap
tepat waktu, dan yang datang paling telat justru menentukan batas.

Dua pola tersedia:

- **Satu sesi per hari** (baku) — tiap hari aktif menghasilkan satu sesi, mulai 07.30,
  selesai dari scan terakhir rumpun pertama. Scan siang/sore tidak membentuk sesi.
- **Setiap rumpun scan jadi sesi** — jam apa adanya dari data. Berguna untuk menelaah
  pola kegiatan, bukan untuk penilaian.

## Kolom keluaran per sesi

Setiap sesi menghasilkan empat kolom:

| Kolom | Isi |
|---|---|
| Status | H / A / S / I |
| Ceklog 1 | Scan **pertama** di dalam jendela sesi |
| Ceklog 2 | Scan **kedua** di dalam jendela sesi (`-` bila hanya menempel sekali) |
| Durasi (jam) | Selisih Ceklog 2 − Ceklog 1, dalam jam desimal |

Di bagian rekap ada **Total Jam** yang menjumlahkan seluruh kolom Durasi
(`=SUM(...)`, sehingga tetap hidup bila angkanya disunting di Excel).

## Aturan penentuan status

- **H** — ada scan dalam rentang `jam mulai − toleransi awal` sampai
  `jam selesai + toleransi terlambat`.
- **A** — tidak ada scan dalam rentang tersebut.
- **S** / **I** — tidak bisa disimpulkan dari mesin (butuh surat), jadi diisi manual
  lewat data `override` dan ditandai `MANUAL` pada kolom *Waktu*.

Jam dari mesin dibulatkan lebih dulu: mesin menulis `07:33:59.941` untuk pukul **07:34**.

## Deploy ke Vercel

Repo ini siap dipakai apa adanya: `api/index.py` menjadi titik masuk dan
`vercel.json` mengarahkan seluruh rute ke sana.

```bash
vercel --prod
```

Atau hubungkan repo GitHub-nya lewat dasbor Vercel — tiap `git push` akan otomatis ter-deploy.

Aplikasi ini **stateless**: tidak ada file yang disimpan di server. Hasil pembacaan data
mentah dikirim balik ke browser lalu disertakan lagi pada setiap permintaan berikutnya.
Ini penting di Vercel, karena tiap permintaan bisa dilayani instance berbeda yang tidak
berbagi filesystem.

## Privasi data

Data kehadiran memuat informasi pribadi. `.gitignore` sudah memblokir `*.xls`, `*.xlsx`,
dan `*.csv` supaya tidak pernah ikut ter-commit. Simpan berkas mentah **di luar** repo ini.

## Struktur berkas

```
.
├── api/index.py        Titik masuk Vercel
├── app.py              Server web + endpoint API
├── core/parser.py      Pembaca 3 format ekspor mesin -> log scan
├── core/sesi.py        Deteksi sesi otomatis dari sebaran jam
├── core/rekap.py       Penentuan status + penulis .xlsx
├── templates/          Halaman antarmuka
└── static/             Gaya dan skrip antarmuka
```

## Catatan tentang berkas referensi

Rumus di berkas referensi diperbaiki di keluaran aplikasi:

- `=COUNTIF(D12:P12,"A")` — rentangnya bocor ke kolom rekap; diperbaiki jadi `D12:O12`.
- `=T12:T145/6` — referensi rentang dibagi angka, rapuh di Excel versi baru;
  diperbaiki jadi `=T12/<jumlah sesi>` sehingga persentase ikut menyesuaikan
  bila jumlah sesi bukan 6.

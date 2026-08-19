# Sistem Absensi Fakultas Kedokteran

Aplikasi web untuk mengelola data akademik dan mencetak **laporan absensi per blok**
dari mesin fingerprint, langsung dalam bentuk `.xlsx` siap pakai.

Menggantikan aplikasi PHP lama (`absensi/`) yang tidak lagi bisa berjalan di PHP modern.

> **Status:** dalam pengerjaan. Rancangan lengkap ada di [`docs/PRD.md`](docs/PRD.md).

---

## Tech stack

| Lapisan | Pilihan |
|---|---|
| Bahasa | Python 3.9 ke atas |
| Kerangka web | Flask 3 |
| ORM | SQLAlchemy 2 + Flask-SQLAlchemy |
| Basis data | SQLite (lokal) · PostgreSQL (bila `DATABASE_URL` diisi) |
| Sumber att_log | PyMySQL, koneksi baca-saja ke MySQL Fingerspot |
| Baca berkas mesin | pandas + xlrd |
| Tulis laporan | openpyxl |
| Antarmuka | Vue 3 + Vite + Element Plus + Pinia |
| Peladen produksi | gunicorn di dalam Docker |

Alasan pemilihan dan alternatif yang ditolak: lihat [bagian 4 PRD](docs/PRD.md#4-tech-stack).

## Menjalankan

```bash
./jalankan.sh
```

Buka <http://127.0.0.1:5057>. Perintah pertama menyiapkan lingkungan Python dan
membangun antarmuka sendiri (butuh `python3` dan `npm`). Akun awal:
**admin / admin** — segera ganti lewat menu Akun.

> Skrip ini memakai peladen pengembangan bawaan Flask dan **hanya untuk bekerja
> di komputer sendiri**. Untuk dipasang sungguhan, lihat bagian Docker di bawah.

Data tersimpan di `data.db`. Untuk memakai PostgreSQL:

```bash
export DATABASE_URL="postgresql://pengguna:sandi@host:5432/namadb"
./jalankan.sh
```

## Menjalankan dengan Docker

Cara ini yang dipakai untuk VPS. Node hanya bekerja saat citra dibangun dan tidak
ikut ke hasil akhir, jadi server cukup punya Docker.

```bash
cp .env.contoh .env
openssl rand -hex 32          # salin hasilnya ke SECRET_KEY di dalam .env
docker compose up -d --build
```

Buka <http://127.0.0.1:5057>. Akun awal **admin / admin** — segera ganti.

`SECRET_KEY` sengaja dibuat wajib: tanpa itu Flask memakai kunci bawaan yang
tertulis di dalam kode, sehingga cookie sesi bisa dipalsukan siapa pun yang
membaca repositori ini.

Basis data SQLite berada di volume `basisdata` (`/data/data.db` di dalam wadah),
terpisah dari citra sehingga selamat saat aplikasi dibangun ulang. Untuk memakai
PostgreSQL:

```bash
# isi POSTGRES_PASSWORD di .env, lalu:
DATABASE_URL=postgresql://finger:SANDI@postgres:5432/finger \
  docker compose --profile postgres up -d --build
```

### Mengisi data awal di dalam wadah

`seed.py` membaca berkas rujukan yang tidak ikut dalam repositori, jadi
berkasnya dipasang saat perintah dijalankan:

```bash
docker compose run --rm \
  -v "$HOME/fingerprint:/rujukan:ro" \
  aplikasi python seed.py --rekap "/rujukan/data jadi - ....xlsx" --dosen /rujukan/dosen.txt
```

Bila basis data lokal sudah terisi, menyalinnya lebih cepat:

```bash
docker compose cp data.db aplikasi:/data/data.db && docker compose restart aplikasi
```

`restart` di situ bukan sekadar kebiasaan. Berkas hasil `cp` membawa UID mesin
asal, dan titik masuk wadah membereskan kepemilikan `/data` saat start. Tanpa
langkah itu aplikasi tetap bisa membaca sehingga tampak sehat, tetapi setiap
penyimpanan gagal dengan *attempt to write a readonly database*.

### Memasang di server lokal kampus (Windows atau Linux)

Jalur `att_log` membuka koneksi MySQL langsung ke basis data software
Fingerspot, sehingga aplikasi harus berada di jaringan yang sama dengan mesin.
Jalur impor `.xls` tidak menuntut itu dan tetap bisa dipakai dari mana saja.

Di Windows, Docker bukan sekadar pilihan yang lebih rapi - gunicorn tidak
berjalan di Windows karena bergantung pada `fork`, jadi tanpa Docker peladennya
harus diganti waitress dan susunannya menyimpang dari yang sudah teruji di sini.

**Menghubungkan ke Fingerspot di komputer yang sama.** Isi Host att_log dengan
`host.docker.internal`, bukan `127.0.0.1`. Dari dalam wadah, `127.0.0.1`
menunjuk wadah itu sendiri, bukan Windows-nya.

**Bila Fingerspot ada di komputer lain**, isi alamat IP-nya, lalu di komputer
tersebut: buka `bind-address` MySQL, buat pengguna yang hanya boleh
`SELECT` pada `att_log`, dan batasi firewall ke satu IP peladen aplikasi.

**Menyala sendiri setelah komputer dinyalakan ulang.** `restart: unless-stopped`
hanya bekerja bila mesin Docker sudah hidup. Pada Docker Desktop, mesin itu baru
hidup setelah ada pengguna yang login, jadi aktifkan *Start Docker Desktop when
you log in* sekaligus login otomatis Windows - atau pakai Linux, yang
menjalankan Docker sebagai layanan tanpa perlu login.

**Cadangan.** Basis data ada di volume `basisdata`, di luar citra:

```bash
docker compose cp aplikasi:/data/data.db ./cadangan-$(date +%F).db
```

### Pemasangan di Proxmox + Ubuntu Server

Susunan yang disarankan untuk server kampus. Keempat lapisannya menyala sendiri
setelah listrik kembali, tanpa perlu ada yang login:

```
Proxmox        nyala saat komputer dihidupkan
└─ VM Ubuntu   "Start at boot" dicentang
   └─ Docker   layanan systemd
      └─ wadah restart: unless-stopped
```

**1. Buat VM di Proxmox.** Virtualisasi (VT-x atau AMD-V) harus aktif di BIOS.

| Setelan | Nilai |
|---|---|
| ISO | Ubuntu Server LTS |
| CPU · RAM · Disk | 2 vCPU · 4 GB · 32 GB |
| Jaringan | Bridge `vmbr0` — VM harus sejaringan dengan PC Fingerspot |
| Options | **Start at boot: Yes** |

Pakai VM, bukan LXC. Docker di dalam LXC menuntut `nesting=1`, `keyctl`, dan
kadang penyesuaian AppArmor — terlalu banyak kejutan untuk mesin produksi.

Ukuran di atas berasal dari pengukuran nyata: aplikasi memakai 152 MB saat diam
dan 304 MB pada puncak 20 unduhan laporan berbarengan.

**2. Beri VM alamat IP tetap** lewat `/etc/netplan/`, atau reservasi DHCP di
router. Alamat aplikasi tidak boleh berubah-ubah.

**3. Pasang Docker Engine** (bukan Docker Desktop):

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # keluar lalu masuk lagi
docker compose version             # pastikan plugin compose ikut terpasang
```

**4. Jalankan aplikasi:**

```bash
git clone https://github.com/bizznara-hub/finger-generator.git
cd finger-generator/app
cp .env.contoh .env
openssl rand -hex 32               # salin ke SECRET_KEY di dalam .env
docker compose up -d --build
```

Periksa dengan `docker compose ps` — statusnya harus `healthy` dalam sekitar
10 detik. Buka `http://IP-VM:5057`, masuk dengan **admin / admin**, lalu segera
ganti sandinya.

**5. Siapkan pengguna MySQL read-only di PC Fingerspot.**

Aplikasi hanya membaca `att_log`, jadi haknya dibatasi persis sesempit itu.
Jalankan di PC Fingerspot, ganti `IP_VM` dan nama basis datanya:

```sql
CREATE USER 'finger_baca'@'IP_VM' IDENTIFIED BY 'sandi-yang-kuat';
GRANT SELECT ON nama_db_fingerspot.att_log TO 'finger_baca'@'IP_VM';
FLUSH PRIVILEGES;
```

Lalu izinkan koneksi dari luar: pada `my.ini` ubah `bind-address` menjadi
`0.0.0.0`, restart layanan MySQL, dan buka porta 3306 di Windows Firewall
**hanya untuk IP VM** — bukan untuk semua alamat.

Isi kredensialnya di menu **Pengaturan → Koneksi att_log**, lalu tekan Uji
Koneksi. Host diisi alamat IP PC Fingerspot; `host.docker.internal` hanya
berlaku bila Fingerspot berada di komputer yang sama dengan Docker.

**6. Cadangan berlapis.** Harian untuk basis datanya saja:

```bash
docker compose cp aplikasi:/data/data.db /cadangan/finger-harian.db
```

Ditambah `vzdump` mingguan di Proxmox untuk seluruh VM. Lapis pertama penting:
memulihkan satu VM utuh hanya demi satu berkas basis data itu merepotkan.

**Sebelum dianggap selesai**, pastikan ID Finger tiap mahasiswa sama dengan User
ID yang terdaftar di mesin. Bila mesin memakai nomor urut sedangkan ID Finger
berisi NIM, `att_log` tersambung dengan baik tetapi seluruh laporan tetap 0%.

### Di belakang Nginx atau Caddy

Ubah pemetaan porta menjadi `127.0.0.1:5057:5057` supaya aplikasi tidak terbuka
langsung ke internet, lalu teruskan dari peladen web yang menangani TLS. Cookie
sesi memakai `SameSite=Lax` dan belum menyetel `Secure`, jadi TLS memang harus
diakhiri di lapisan itu.

## Dua jalur data mentah

**Jalur A — tarik dari att_log.** Menyambung baca-saja ke basis data software
Fingerspot dan menarik tabel `att_log` untuk rentang tanggal tertentu. Kredensialnya
diisi di menu Pengaturan. Aplikasi harus berada di jaringan yang sama dengan server
Fingerspot.

**Jalur B — impor berkas ekspor mesin.** Tiga format dikenali:

| Ekspor mesin | Kelengkapan |
|---|---|
| **Catatan Kehadiran Karyawan** | Paling lengkap — seluruh sentuhan jari |
| Laporan Kehadiran | ±14% scan hilang karena dipaksa masuk slot pagi/siang/lembur |
| Kehadiran Tidak Normal | Paling sedikit; Sabtu dan Minggu tidak ikut terekspor |

Bila ragu, pakai **Catatan Kehadiran Karyawan**. Mengimpor berkas yang sama dua kali
aman — scan kembar diabaikan.

## Alur pemakaian

1. Isi data master: Departemen → Kelas → Mahasiswa (beserta **ID Finger**) → Dosen →
   Ruang Kuliah → Mata Kuliah
2. Daftarkan mesin di menu **Finger Print**, petakan ke ruangannya
3. Susun **Jadwal Kuliah**: blok → kelas → tanggal → **sesi** (dibuat manual, bisa diubah)
4. Tarik atau impor data mentah
5. Catat **Sakit** dan **Izin** bila ada
6. Buka **Laporan**, pilih blok dan kelas, lalu unduh `.xlsx`

## Penentuan status

Untuk setiap mahasiswa pada setiap sesi, berurutan:

1. Tercatat **Sakit** → `S`
2. Tercatat **Izin** → `I`
3. Ada scan di dalam jendela sesi → `H`, kolom *Waktu* diisi scan pertama
4. Selain itu → `A`

Jendela sesi dihitung:

```
jam_selesai = jam_masuk + (jml_jam × menit_perjam) + ((jml_jam − 1) × menit_pergantian)
jendela      = [jam_masuk − toleransi_awal, jam_selesai + toleransi_akhir]
```

`menit_perjam`, `menit_pergantian`, dan toleransi diatur di menu **Pengaturan**.
Jam selesai boleh ditimpa manual per sesi.

Mesin menulis `07:33:59.941` untuk pukul **07:34** — detik ≥ 30 dibulatkan ke atas
sebelum disimpan.

## Bentuk laporan

Mengikuti berkas rujukan, dengan rumus hidup (bukan angka mati):

- `H`, `A`, `S`, `I` = `COUNTIF` atas rentang kolom sesi
- `Total Kehadiran` = `H + S + I`
- `Persentasi (%)` = `Total ÷ jumlah sesi`, format `0%`

Dua bentuk kolom saat mencetak:

- **Ringkas** — `Status | Waktu`, sama persis dengan berkas rujukan (baku)
- **Lengkap** — `Status | Ceklog 1 | Ceklog 2 | Durasi (jam)`, plus kolom Total Jam

## Struktur berkas

```
.
├── app.py              Titik masuk; menyajikan API dan hasil build antarmuka
├── core/               Logika domain, tidak menyentuh lapisan web
│   ├── models.py       Skema basis data
│   ├── parser.py       Pembaca 3 format ekspor mesin
│   ├── attlog.py       Penarik data dari MySQL Fingerspot
│   ├── impor.py        Pembaca daftar peserta dari berkas unggahan
│   ├── laporan.py      Penentuan status H/A/S/I
│   └── rekap.py        Penulis .xlsx
├── api/                46 rute JSON
│   ├── auth.py         Masuk, keluar, akun
│   ├── master.py       CRUD data master
│   ├── jadwal.py       Blok, kelas, tanggal, sesi, peserta
│   ├── mentah.py       Impor berkas mesin dan tarik att_log
│   ├── laporan.py      Pratinjau dan unduh .xlsx
│   └── sistem.py       Beranda, pengaturan, profil jam
├── web/                Antarmuka Vue 3 + Vite + Element Plus
│   ├── src/views/      Satu berkas per halaman
│   └── dist/           Hasil build yang disajikan Flask
├── Dockerfile          Citra dua tahap: Node membangun, Python menjalankan
├── docker-compose.yml  Layanan aplikasi dan profil postgres
└── docs/PRD.md         Rancangan lengkap
```

## Privasi data

Data kehadiran memuat informasi pribadi. `.gitignore` memblokir `*.xls`, `*.xlsx`,
`*.csv`, dan `*.db` agar tidak pernah ikut ter-commit. Simpan berkas mentah **di luar**
repositori ini.

## Pemasangan di Vercel

Aplikasi ini bisa di-deploy ke Vercel, tetapi:

- **Wajib** mengisi `DATABASE_URL` ke PostgreSQL — filesystem Vercel tidak menyimpan apa pun
- Jalur att_log **tidak bisa** dipakai kecuali MySQL Fingerspot dapat dijangkau dari internet

Untuk pemakaian sehari-hari di kampus, menjalankannya di server lokal lebih tepat.

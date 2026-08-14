# Design — Sistem Absensi Fakultas Kedokteran

Sistem desain terkunci untuk aplikasi ini. Setiap halaman membaca berkas ini sebelum
menulis kode. Jangan membuat sistem baru per halaman — perluas atau ubah berkas ini
bila sistemnya perlu tumbuh.

Dibangun dengan Hallmark v1.1.0 · genre modern-minimal · macrostructure Index-First · tema Cobalt.

## Genre

**modern-minimal** — register dashboard/platform. Bukan editorial, bukan playful.
Aplikasi ini dipakai petugas akademik setiap hari untuk pekerjaan data; nadanya
**utilitarian / technical** — instrument panel, bukan brosur.

## Macrostructure family

- **Halaman aplikasi** (beranda, daftar data, jadwal, log, laporan): **Index-First** —
  halamannya memang daftar; navigasi sebagai desain, tanpa hero, tanpa naratif.
- **Halaman formulir** (tambah/ubah, pengaturan, akun): **Long Document** — satu kolom,
  label di atas kolom isian, tanpa dua kolom yang memaksa mata bolak-balik.
- **Halaman masuk**: panel tunggal terpusat. Satu-satunya halaman tanpa rail.

Halaman dalam satu family berbagi bentuk yang sama; yang boleh berbeda hanya
susunan panelnya.

## Theme — Cobalt

Kertas *cool near-white* yang direkayasa, tinta charcoal dingin, **satu** sinyal kobalt.
Bukan `#fff`, bukan `#000`. Seluruh nilai di bawah **sudah diverifikasi kontrasnya**
(WCAG 2.1, dihitung dari OKLCH — bukan dikira-kira).

- `--color-paper`      oklch(98.6% 0.003 250)
- `--color-paper-2`    oklch(96.8% 0.005 251)
- `--color-paper-3`    oklch(94.4% 0.007 252)
- `--color-ink`        oklch(21% 0.021 259)   · 17.02:1 di atas kertas
- `--color-ink-2`      oklch(33% 0.018 257)   · 11.73:1
- `--color-muted`      oklch(50% 0.015 256)   ·  5.76:1
- `--color-rule`       oklch(90.5% 0.006 252)
- `--color-rule-2`     oklch(84% 0.009 253)
- `--color-accent`     oklch(50% 0.2 256)     ·  5.90:1 dengan teks putih di atasnya
- `--color-accent-ink` oklch(99% 0.004 250)
- `--color-focus`      oklch(50% 0.2 256)
- `--color-graphite`   oklch(20.5% 0.017 261) · rail, 12.49:1

Aksen semula `oklch(58% …)` sesuai spesifikasi Cobalt, tetapi gagal kontras untuk teks
putih di atasnya (4,25:1 — ambang 4,5:1). Diturunkan ke `50%`: satu nilai itu
memperbaiki tombol, tautan, dan status Hadir sekaligus, sehingga disiplin *satu sinyal
kobalt* tetap utuh.

**Aksen dipakai < 5% viewport** — hanya tombol utama, cincin fokus, penanda menu
terpilih, dan status Hadir. Tidak pernah sebagai latar besar.

**Satu pita gelap**: rail sisi kiri. Itu satu-satunya permukaan gelap.

### Warna status kehadiran

- `--color-hadir` oklch(50% 0.2 256) — kobalt, sama dengan aksen · 5.31:1
- `--color-alpa`  oklch(51% 0.19 27)  · 5.47:1
- `--color-sakit` oklch(49% 0.12 75)  · 5.58:1
- `--color-izin`  oklch(50% 0.16 310) · 5.67:1

## Typography

Tiga muka huruf — batas maksimum Hallmark.

- **Display**: Geist **700**, tracking `-0.022em`, roman
- **Body**: Geist 400 / 500 / 600 — satu famili dengan display
- **Mono**: Geist Mono 400 / 500 — hanya untuk data: NIM, ID Finger, jam, angka

Bobot display 700 melawan body 400 = jarak **300 unit**, sesuai aturan Hallmark.
Bobot 600 vs 400 (yang saya pakai di percobaan pertama) hanya 200 unit dan terbaca
sebagai setelan bawaan, bukan pilihan.

Skala **rasio 1.25 (major third)** dari 16px, bukan kenaikan sembarang:

`2xs` 11px · `xs` 13px · `sm` 14px · `base` 16px · `md` 20px · `lg` 25px · `xl` 31px · `2xl` 39px

Hierarki dibawa **bobot dan ukuran**, bukan bayangan:

```
judul halaman 31px/700 → judul panel 11px/500 mono → tubuh 16px/400
→ tabel 14px/400 → angka readout 39px/400 mono
```

Mono pada NIM dan jam bukan gaya: kolom `07:34` dan `C011241006` menjadi rata
sehingga terbaca sekali lihat. Itu inti pekerjaan aplikasi ini.

## Spacing

Skala 4 poin sembilan langkah, di `static/css/tokens.css`. Halaman **wajib** memakai
token, tidak pernah nilai mentah.

`3xs` 2px · `2xs` 4px · `xs` 8px · `sm` 12px · `md` 16px · `lg` 24px · `xl` 40px ·
`2xl` 64px · `3xl` 96px

**Irama padding sengaja tidak seragam** — padding yang sama di semua tempat membuat
halaman terbaca sebagai template:

| Tempat | Padding |
|---|---|
| Halaman | 40px atas, 96px bawah |
| Panel (isi) | 24px |
| Kepala panel | 12px / 24px |
| Sel tabel | 8px / 12px |

## Motion

Cobalt itu *composed*, bukan animated. Gerak hanya di tempat yang menjelaskan sesuatu.

- Easing: `--ease-out` cubic-bezier(0.16, 1, 0.3, 1) — tanpa bounce, tanpa overshoot
- Durasi: `--dur-1` 120ms (hover), `--dur-2` 200ms (panel)
- Yang boleh dianimasikan: `opacity` dan `transform` saja
- **Tanpa reveal saat gulir.** Ini alat kerja; data harus langsung terlihat
- `prefers-reduced-motion: reduce` → seluruh transisi dimatikan

## Microinteractions

- **Silent success** — perubahan yang terlihat sendiri tidak perlu notifikasi meriah
- Cincin fokus muncul **seketika**, tidak pernah dianimasikan
- Tombol hapus selalu memakai `confirm()` bawaan peramban, bukan modal buatan
- Hover pada baris tabel: pergeseran latar 1 tingkat, tidak lebih

## CTA voice

- **Primer**: isi kobalt padat, radius 6px, teks `--color-accent-ink`. Satu per panel
- **Sekunder**: garis rambut 1px, latar kertas, teks tinta
- **Bahaya**: garis rambut merah, teks merah, isi hanya saat hover
- Label menyebut tujuannya: "Simpan pengaturan", "Unduh .xlsx", "Tarik data" —
  tidak pernah "Klik di sini" atau "Submit"

## Radius & rule

- Kontrol (tombol, input, select): `--radius-control` 6px — "digambar dengan penggaris"
- Panel: `--radius-panel` 10px
- Seluruh permukaan dibatasi **garis rambut 1px**, bukan bayangan. Tanpa kartu
  bertumpuk, tanpa `box-shadow` selain lift 1px pada rail

## Per-page allowances

- Halaman aplikasi **tidak boleh** memakai enrichment — fungsi yang membawa halaman
- Tanpa ilustrasi, tanpa ikon dekoratif, tanpa latar bertekstur
- **Tanpa pustaka ikon sama sekali.** Menu dan tombol dipimpin tipografi. Mencampur
  pustaka ikon adalah tell AI; satu-satunya SVG yang boleh adalah penanda fungsional
  dengan `aria-hidden="true"`

## Yang wajib sama di semua halaman

- Rail grafit di kiri, wordmark memakai muka display (Space Grotesk 700)
- Kepala halaman: eyebrow mono UPPERCASE **di atas** judul, satu kolom (tidak pernah
  bersebelahan — itu tell editorial-template)
- Warna aksen dan penempatannya (< 5% viewport)
- Pasangan Geist + Geist Mono
- Bentuk tombol dan irama padding
- Panel bergaris rambut dengan kepala panel bertipografi mono

## Yang boleh berbeda

- Susunan panel di dalam halaman
- Jumlah kolom pada `.grid` formulir
- Ada atau tidaknya baris statistik di atas

## Batasan yang disepakati

- Font diambil dari Google Fonts CDN (keputusan 14/08/2026). **Konsekuensinya
  tampilan berubah bila server kampus terputus dari internet** — `font-display: swap`
  dan tumpukan cadangan sistem sudah dipasang agar tetap terbaca.
- Aset tema Ace/Bootstrap lama masih ada di repo sampai hasil Cobalt disetujui.

## Exports

### tokens.css

Berkas hidupnya di `static/css/tokens.css`. Salin utuh untuk memakai sistem ini di
proyek lain.

```css
:root {
  --color-paper:      oklch(98.6% 0.003 250);
  --color-paper-2:    oklch(96.8% 0.005 251);
  --color-paper-3:    oklch(94.4% 0.007 252);
  --color-ink:        oklch(21% 0.021 259);
  --color-ink-2:      oklch(33% 0.018 257);
  --color-muted:      oklch(50% 0.015 256);
  --color-rule:       oklch(90.5% 0.006 252);
  --color-rule-2:     oklch(84% 0.009 253);
  --color-accent:     oklch(50% 0.2 256);
  --color-accent-ink: oklch(99% 0.004 250);
  --color-focus:      oklch(50% 0.2 256);
  --color-graphite:   oklch(20.5% 0.017 261);

  --font-display: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-body:    "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono:    "JetBrains Mono", ui-monospace, monospace;

  --space-3xs: 0.125rem; --space-2xs: 0.25rem; --space-xs: 0.5rem;
  --space-sm:  0.75rem;  --space-md:  1rem;    --space-lg: 1.5rem;
  --space-xl:  2.5rem;   --space-2xl: 4rem;    --space-3xl: 6rem;

  --text-2xs: 0.6875rem; --text-xs: 0.8125rem; --text-sm: 0.875rem;
  --text-base: 1rem;     --text-md: 1.25rem;   --text-lg: 1.5625rem;
  --text-xl: 1.9531rem;  --text-2xl: 2.4414rem;

  --w-body: 400; --w-medium: 500; --w-display: 700;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-1: 120ms; --dur-2: 200ms;
  --radius-control: 6px; --radius-panel: 10px;
}
```

### DTCG tokens.json

```json
{
  "color": {
    "paper":  { "$value": "oklch(98.6% 0.003 250)", "$type": "color" },
    "ink":    { "$value": "oklch(21% 0.021 259)",    "$type": "color" },
    "accent": { "$value": "oklch(50% 0.2 256)",     "$type": "color" }
  },
  "font": {
    "display": { "$value": "Space Grotesk", "$type": "fontFamily" },
    "body":    { "$value": "Inter",         "$type": "fontFamily" },
    "mono":    { "$value": "JetBrains Mono","$type": "fontFamily" }
  },
  "space": { "md": { "$value": "1.5rem", "$type": "dimension" } }
}
```

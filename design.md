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

## Theme — DNA dari Art Design Pro (disesuaikan)

Diekstrak dari `github.com/Daymychen/art-design-pro` (Vue 3 + Element Plus, MIT).
Demonya SPA sehingga CSS terrender tidak terbaca; token dibaca **langsung dari kode
sumbernya**, yang justru lebih otoritatif.

### Yang diambil

- **Permukaan berlapis** — latar halaman abu muda, kartu/rail/tabel putih di atasnya.
  Ini yang memberi kedalaman lembut tanpa bayangan.
- **Primer periwinkle** (dari `#5D87FF`) menggantikan kobalt yang keras.
- **Sukses mint-teal** (dari `#13DEB9`) — bukan hijau generik.
- **Tinggi kontrol 36px**, sama dengan `--el-component-custom-height`.
- **Item menu berbentuk pil menjorok** dengan tint primer saat aktif.

### Yang TIDAK diambil, dan alasannya

Kesembilan warna aksen Art Design Pro **gagal WCAG AA** untuk teks putih di atasnya:

| Warna asli | Teks putih |
|---|---|
| Primer `#5D87FF` | 3,29:1 |
| Bahaya `#FF4D4F` | 3,27:1 |
| Oranye `#F9901F` | 2,32:1 |
| Sukses `#13DEB9` | 1,72:1 |

Palet itu cantik justru karena terang — dan itu pula yang membuatnya gagal. Aplikasi
ini dipakai membaca angka berjam-jam, jadi ronanya dipertahankan dan lightness-nya
diturunkan sampai lulus 4,5:1 pada **tiga** kondisi sekaligus: teks putih di atas isi,
isi di atas tint lembutnya, dan isi di atas latar halaman.

### Token

- `--color-bg`        oklch(97.2% 0.004 267) — latar halaman
- `--color-surface`   oklch(99.5% 0.001 267) — kartu, rail, tabel
- `--color-surface-2` oklch(97.6% 0.004 267) — hover baris, kepala tabel
- `--color-ink`       oklch(24% 0.023 255)   · 16,21:1
- `--color-ink-2`     oklch(32% 0.022 255)   · 11,69:1
- `--color-muted`     oklch(52% 0.014 258)   ·  5,08:1
- `--color-rule`      oklch(92.9% 0.005 267)
- `--color-accent`    oklch(55% 0.175 267)   ·  5,03:1 dengan teks putih
- `--color-ok`        oklch(51% 0.143 175)   — mint-teal
- `--color-warn`      oklch(55% 0.157 74)    — amber
- `--color-bad`       oklch(56% 0.203 24)    — merah
- `--color-info`      oklch(56% 0.142 300)   — ungu

Seluruh 17 pasangan diverifikasi: **0 gagal**.

## Typography

Dua muka huruf. Art Design Pro tidak memakai webfont sama sekali (font sistem bawaan
Element Plus), jadi referensi itu tidak menjawab soal font — Geist tetap dipakai.

- **Display & body**: Geist 400 / 500 / 600 / 700
- **Mono**: Geist Mono 400 / 500 — hanya untuk data: NIM, ID Finger, jam, angka

Bobot judul 700 melawan tubuh 400 = jarak 300 unit.

Skala rasio 1.25 dari 16px:
`2xs` 11px · `xs` 13px · `sm` 14px · `base` 16px · `md` 20px · `lg` 25px · `xl` 31px

## Spacing

Skala 4 poin sembilan langkah, di `static/css/tokens.css`.

`3xs` 2px · `2xs` 4px · `xs` 8px · `sm` 12px · `md` 16px · `lg` 24px · `xl` 40px ·
`2xl` 64px · `3xl` 96px

Irama padding sengaja tidak seragam: halaman 40px, kartu 24px, sel tabel 12/16px.

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

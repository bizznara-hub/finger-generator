"""Deteksi otomatis sesi (jam kegiatan) dari sebaran waktu scan."""

import re

import pandas as pd

HARI_ID = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jum'at",
    5: "Sabtu",
    6: "Minggu",
}


def nama_hari(tanggal):
    return HARI_ID[pd.Timestamp(tanggal).dayofweek]


def label_tanggal(tanggal):
    t = pd.Timestamp(tanggal)
    return f"{nama_hari(t)}, {t.strftime('%d/%m/%Y')}"


def _fmt(menit):
    return f"{int(menit) // 60:02d}.{int(menit) % 60:02d}"


def ke_menit(teks):
    """'07.30' / '07:30' -> menit sejak tengah malam."""
    m = re.match(r"^\s*(\d{1,2})\s*[.:]?\s*(\d{2})\s*$", str(teks))
    if not m:
        raise ValueError(f"Format jam tidak valid: {teks!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def _rumpun_per_tanggal(grup, jeda_menit, min_peserta):
    """Pecah scan satu hari menjadi rumpun-rumpun yang dipisahkan jeda panjang."""
    grup = grup.sort_values("menit")
    kelompok, berjalan = [], [grup.iloc[0]]
    for i in range(1, len(grup)):
        if grup.menit.iloc[i] - grup.menit.iloc[i - 1] > jeda_menit:
            kelompok.append(berjalan)
            berjalan = []
        berjalan.append(grup.iloc[i])
    kelompok.append(berjalan)
    return [k for k in kelompok if len({r.uid for r in k}) >= min_peserta]


def deteksi_sesi(log, jeda_menit=45, min_peserta=4, mode="harian", jam_mulai="07.30"):
    """Susun daftar sesi dari sebaran waktu scan.

    mode "harian"  : satu sesi per hari. Jam mulai dikunci ke `jam_mulai`,
                     jam selesai diambil dari scan terakhir rumpun pertama hari itu.
                     Scan siang/sore tidak membentuk sesi tersendiri.
    mode "rumpun"  : setiap rumpun scan menjadi satu sesi, jamnya apa adanya
                     dari data. Berguna untuk menelaah, bukan untuk penilaian.
    """
    mulai_tetap = ke_menit(jam_mulai) if mode == "harian" else None
    sesi = []

    for tanggal, grup in log.groupby("tanggal"):
        rumpun = _rumpun_per_tanggal(grup, jeda_menit, min_peserta)
        if not rumpun:
            continue
        dipakai = rumpun[:1] if mode == "harian" else rumpun

        for k in dipakai:
            peserta = {r.uid for r in k}
            awal_data, akhir_data = k[0].menit, k[-1].menit
            mulai = mulai_tetap if mode == "harian" else awal_data
            selesai = max(akhir_data, mulai + 30)
            sesi.append(
                {
                    "tanggal": pd.Timestamp(tanggal).strftime("%Y-%m-%d"),
                    "label_tanggal": label_tanggal(tanggal),
                    "nama": "",
                    "jam_mulai": _fmt(mulai),
                    "jam_selesai": _fmt(selesai),
                    "peserta": len(peserta),
                    "jam_data": f"{_fmt(awal_data)}-{_fmt(akhir_data)}",
                }
            )

    sesi.sort(key=lambda s: (s["tanggal"], s["jam_mulai"]))
    for i, s in enumerate(sesi, 1):
        s["no"] = i
        s["nama"] = f"SESI {i}"
    return sesi

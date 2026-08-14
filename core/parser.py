"""Baca file .xls mentah dari mesin fingerprint menjadi log scan yang rapi.

Mendukung 3 format ekspor yang dipakai mesin:
  - "catatan"      : Catatan Kehadiran Karyawan (grid 30 kolom tanggal)  <- paling lengkap
  - "laporan"      : Laporan Kehadiran (sheet detail per 3 orang)
  - "tidaknormal"  : Kehadiran Tidak Normal (flat, 1 baris per orang per tanggal)

Semua format dikembalikan sebagai DataFrame kolom: uid, nama, tanggal, jam.
"""

import re

import pandas as pd

RE_JAM = re.compile(r"\b(\d{1,2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?")
RE_PERIODE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s*~\s*(\d{4})-(\d{2})-(\d{2})")
RE_SHEET_DETAIL = re.compile(r"^\d+(,\d+)*$")


class FormatTidakDikenali(Exception):
    pass


def _bulatkan(jam, menit, detik):
    """Mesin menulis 07:33:59.941 untuk pukul 07:34 - bulatkan ke menit terdekat."""
    if detik and float(detik) >= 30:
        menit += 1
    if menit >= 60:
        menit -= 60
        jam += 1
    return f"{jam % 24:02d}:{menit:02d}"


def _jam_dari_sel(nilai):
    """Ambil semua jam dari satu sel (bisa berisi beberapa baris)."""
    hasil = []
    for j, m, d in RE_JAM.findall(str(nilai)):
        hasil.append(_bulatkan(int(j), int(m), d))
    return hasil


def _cari_periode(df):
    """Cari teks 'Tanggal Kehadiran:2026-07-01~2026-07-30' di mana pun dalam sheet."""
    for baris in df.head(8).itertuples(index=False):
        for sel in baris:
            m = RE_PERIODE.search(str(sel))
            if m:
                awal = pd.Timestamp(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                akhir = pd.Timestamp(int(m.group(4)), int(m.group(5)), int(m.group(6)))
                return awal, akhir
    return None, None


def _tanggal_dari_hari(periode_awal, periode_akhir, hari):
    """Nomor hari (1..31) -> tanggal penuh. Periode bisa melintasi 2 bulan."""
    for acuan in (periode_awal, periode_akhir):
        if acuan is None:
            continue
        try:
            tgl = pd.Timestamp(acuan.year, acuan.month, hari)
        except ValueError:
            continue
        if periode_awal <= tgl <= periode_akhir:
            return tgl
    try:
        return pd.Timestamp(periode_awal.year, periode_awal.month, hari)
    except ValueError:
        return None


def _parse_catatan(df):
    """Format grid: blok per orang, header 'User ID.：', kolom 1..30 = tanggal."""
    awal, akhir = _cari_periode(df)
    if awal is None:
        raise FormatTidakDikenali("Periode tanggal tidak ditemukan di file.")

    mulai_blok = [
        r for r in range(df.shape[0]) if str(df.iat[r, 4]).strip().startswith("User ID")
    ]
    if not mulai_blok:
        raise FormatTidakDikenali("Tidak ada blok 'User ID' pada file.")

    baris = []
    for i, s in enumerate(mulai_blok):
        try:
            uid = int(float(df.iat[s, 5]))
        except (TypeError, ValueError):
            continue
        nama = str(df.iat[s, 11]).strip()
        akhir_blok = mulai_blok[i + 1] if i + 1 < len(mulai_blok) else df.shape[0]

        # baris tepat di bawah header berisi nomor hari
        peta_hari = {}
        for c in range(1, df.shape[1]):
            v = df.iat[s + 1, c]
            if pd.notna(v):
                try:
                    peta_hari[c] = int(float(v))
                except (TypeError, ValueError):
                    pass
        if not peta_hari:
            continue

        for r in range(s + 2, akhir_blok):
            for c, hari in peta_hari.items():
                v = df.iat[r, c]
                if pd.isna(v):
                    continue
                tgl = _tanggal_dari_hari(awal, akhir, hari)
                if tgl is None:
                    continue
                for jam in _jam_dari_sel(v):
                    baris.append((uid, nama, tgl, jam))
    return baris


def _parse_laporan(xl):
    """Format sheet detail: 3 orang per sheet, tiap blok lebar 15 kolom."""
    baris = []
    for nama_sheet in xl.sheet_names:
        if not RE_SHEET_DETAIL.match(nama_sheet):
            continue
        df = xl.parse(nama_sheet, header=None)
        awal, akhir = _cari_periode(df)
        if awal is None:
            continue
        for blok in range(3):
            c0 = blok * 15
            if c0 + 9 >= df.shape[1]:
                continue
            nama = df.iat[3, c0 + 9]
            uid = df.iat[4, c0 + 9]
            if pd.isna(nama) or pd.isna(uid):
                continue
            for r in range(12, df.shape[0]):
                sel_hari = df.iat[r, c0]
                if pd.isna(sel_hari):
                    continue
                m = re.match(r"(\d+)", str(sel_hari).strip())
                if not m:
                    continue
                tgl = _tanggal_dari_hari(awal, akhir, int(m.group(1)))
                if tgl is None:
                    continue
                for off in (1, 3, 6, 8, 10, 12):
                    if c0 + off >= df.shape[1]:
                        continue
                    v = df.iat[r, c0 + off]
                    if pd.isna(v):
                        continue
                    for jam in _jam_dari_sel(v):
                        baris.append((int(float(uid)), str(nama).strip(), tgl, jam))
    return baris


def _parse_tidaknormal(df):
    """Format flat: kolom 0=uid, 1=nama, 3=tanggal, 4..7=jam masuk/keluar."""
    baris = []
    for r in range(4, df.shape[0]):
        uid = df.iat[r, 0]
        if pd.isna(uid):
            continue
        try:
            uid = int(float(uid))
        except (TypeError, ValueError):
            continue
        nama = str(df.iat[r, 1]).strip()
        try:
            tgl = pd.Timestamp(df.iat[r, 3]).normalize()
        except (TypeError, ValueError):
            continue
        for c in range(4, 8):
            if c >= df.shape[1]:
                break
            v = df.iat[r, c]
            if pd.isna(v):
                continue
            for jam in _jam_dari_sel(v):
                baris.append((uid, nama, tgl, jam))
    return baris


def deteksi_format(xl):
    if any(RE_SHEET_DETAIL.match(s) for s in xl.sheet_names):
        return "laporan"
    df = xl.parse(0, header=None)
    if df.shape[1] > 5 and df.head(30).iloc[:, 4].astype(str).str.startswith("User ID").any():
        return "catatan"
    teks = " ".join(str(x) for x in df.head(4).values.ravel())
    if "Tidak Normal" in teks:
        return "tidaknormal"
    raise FormatTidakDikenali(
        "File tidak dikenali. Gunakan ekspor 'Catatan Kehadiran Karyawan', "
        "'Laporan Kehadiran', atau 'Kehadiran Tidak Normal'."
    )


def baca_mentah(sumber):
    """Baca satu file .xls/.xlsx mentah -> (DataFrame log scan, nama format).

    `sumber` boleh berupa path maupun objek file (BytesIO), sehingga aplikasi
    tidak perlu menulis apa pun ke disk.
    """
    xl = pd.ExcelFile(sumber)
    fmt = deteksi_format(xl)

    if fmt == "laporan":
        baris = _parse_laporan(xl)
    else:
        df = xl.parse(0, header=None)
        baris = _parse_catatan(df) if fmt == "catatan" else _parse_tidaknormal(df)

    log = pd.DataFrame(baris, columns=["uid", "nama", "tanggal", "jam"])
    if log.empty:
        raise FormatTidakDikenali("Tidak ada data scan yang bisa dibaca dari file ini.")

    return _rapikan(log), fmt


def _rapikan(log):
    log = log.drop_duplicates().sort_values(["uid", "tanggal", "jam"], ignore_index=True)
    log["menit"] = log.jam.str[:2].astype(int) * 60 + log.jam.str[3:5].astype(int)
    return log


def ke_muatan(log):
    """Ubah log jadi bentuk ringkas untuk dikirim ke browser."""
    return [
        [int(r.uid), r.nama, pd.Timestamp(r.tanggal).strftime("%Y-%m-%d"), r.jam]
        for r in log.itertuples(index=False)
    ]


def dari_muatan(muatan):
    """Kebalikan `ke_muatan`: bangun ulang DataFrame log dari data kiriman browser."""
    if not muatan:
        raise FormatTidakDikenali("Data scan kosong. Silakan unggah ulang file mentah.")
    log = pd.DataFrame(muatan, columns=["uid", "nama", "tanggal", "jam"])
    log["uid"] = log.uid.astype(int)
    log["tanggal"] = pd.to_datetime(log.tanggal)
    return _rapikan(log)


def gabung_mentah(sumber_sumber):
    """Baca beberapa file sekaligus dan gabungkan lognya."""
    semua, format_terpakai = [], []
    for s in sumber_sumber:
        log, fmt = baca_mentah(s)
        semua.append(log)
        format_terpakai.append(fmt)
    gabungan = (
        pd.concat(semua, ignore_index=True)
        .drop_duplicates(subset=["uid", "tanggal", "jam"])
        .sort_values(["uid", "tanggal", "jam"], ignore_index=True)
    )
    return gabungan, format_terpakai

"""Membaca daftar nama atau NIM dari berkas unggahan.

Berkas tidak pernah ditulis ke disk. Isinya dibaca dari memori, dicocokkan
dengan mahasiswa yang sudah ada, lalu dilupakan - sistem cukup tahu siapa yang
terdaftar, bukan menyimpan berkasnya.
"""

import re

import pandas as pd


class FormatTidakDidukung(Exception):
    pass


# NIM biasanya beberapa huruf kode prodi diikuti deretan angka, misalnya
# C011241006. Dipakai hanya untuk menebak mana teks yang *bermaksud* NIM,
# sehingga yang tidak cocok bisa dilaporkan balik ke admin.
POLA_NIM = re.compile(r"^[A-Za-z]{0,4}\d{6,14}$")


def kunci(teks):
    """Samakan bentuk penulisan: huruf kecil, tanpa spasi dan tanda baca."""
    return re.sub(r"[^a-z0-9]", "", (teks or "").lower())


def baca_sel(aliran, nama_berkas):
    """Kembalikan seluruh isi sel sebagai daftar teks.

    Sengaja tidak menebak baris judul atau posisi kolom. Berkas daftar hadir
    datang dalam banyak bentuk, dan pencocokan nanti dilakukan terhadap data
    yang sudah ada - jadi memindai semua sel lebih tahan banting daripada
    menuntut susunan kolom tertentu.
    """
    nama = (nama_berkas or "").lower()
    if nama.endswith(".csv"):
        df = pd.read_csv(aliran, header=None, dtype=str,
                         keep_default_na=False, sep=None, engine="python")
    elif nama.endswith((".xls", ".xlsx")):
        df = pd.read_excel(aliran, header=None, dtype=str)
    else:
        raise FormatTidakDidukung(
            f"Format berkas {nama_berkas} tidak didukung. Gunakan .xls, .xlsx, atau .csv."
        )

    sel = []
    for nilai in df.to_numpy().ravel():
        teks = "" if nilai is None else str(nilai).strip()
        if teks and teks.lower() != "nan":
            sel.append(teks)
    return sel


def cocokkan(sel, daftar_mahasiswa):
    """Cocokkan isi sel dengan mahasiswa yang sudah ada.

    Kembalikan (mahasiswa yang cocok, teks mirip NIM yang tidak dikenali).
    NIM diutamakan; nama dipakai sebagai cadangan supaya berkas yang hanya
    memuat nama tetap bisa dipakai.
    """
    per_nim, per_nama = {}, {}
    for m in daftar_mahasiswa:
        per_nim[kunci(m.nim)] = m
        # setdefault: bila ada dua nama identik, yang pertama dipertahankan
        # dan pasangannya dilaporkan sebagai tidak dikenali, bukan ditebak.
        per_nama.setdefault(kunci(m.nama), m)

    cocok, tidak = {}, []
    for teks in sel:
        k = kunci(teks)
        if not k:
            continue
        m = per_nim.get(k) or per_nama.get(k)
        if m:
            cocok[m.id] = m
        elif POLA_NIM.match(teks.replace(" ", "")):
            tidak.append(teks)

    # urutan dipertahankan, hanya diseragamkan supaya laporan tidak berulang
    unik = list(dict.fromkeys(tidak))
    return list(cocok.values()), unik

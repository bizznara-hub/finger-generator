"""Isi basis data dengan data awal dari berkas rujukan.

Skrip ini **membaca** berkas rekap yang sudah ada; nama dan NIM mahasiswa tidak
pernah ditanam di dalam kode, supaya data pribadi tidak ikut ke repositori.

    ./.venv/bin/python seed.py \
        --rekap "../data jadi - Rekapan Absensi PBL Kelas A Blok NEUROLOGI Angk 2024.xlsx" \
        --mentah "../data mentah - Catatan Kehadiran Karyawan.xls"

Pilihan lain:
    --kosongkan      hapus seluruh isi tabel lebih dulu
    --petakan-demo   petakan ID Finger mesin ke mahasiswa pertama, hanya untuk
                     mencoba alur laporan. Pemetaan ini KARANGAN, bukan data asli.
"""

import argparse
import io
import re
import sys
from datetime import datetime, time

import pandas as pd

from app import app
from core import parser as pembaca
from core.models import (
    Departemen,
    Jadwal,
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    JadwalMahasiswa,
    Kelas,
    Ketidakhadiran,
    LogScan,
    Mahasiswa,
    MataKuliah,
    Mesin,
    Pengaturan,
    Ruangan,
    db,
)

# Daftar departemen Fakultas Kedokteran. Bukan data pribadi, jadi aman
# ditulis di dalam kode.
DEPARTEMEN = [
    "Anatomi",
    "Anestesiologi",
    "Biokimia",
    "Farmakologi",
    "Fisiologi",
    "Forensik dan Medikolegal",
    "Histologi",
    "IKM dan IKK",
    "Ilmu Bedah",
    "Ilmu Faal",
    "Ilmu Gizi",
    "Ilmu Kedokteran Jiwa",
    "Ilmu Kesehatan Anak",
    "Ilmu Kesehatan Kulit dan Kelamin",
    "Ilmu Kesehatan Mata",
    "Ilmu Kesehatan THT",
    "Ilmu Penyakit Dalam",
    "Ilmu Penyakit Saraf",
    "Kardiologi dan Kedok Vaskuler",
    "Kedokteran Fisik dan Rehabilitasi",
    "Kedokteran Kehakiman (Forensik dan Modikolegal)",
    "Mikrobiologi",
    "Obstetri dan Ginekologi",
    "Orthopedi dan Traumatologi",
    "Parasitologi",
    "Patologi Anatomi",
    "Patologi Klinik",
    "Prodi S1",
    "Psikiatri",
    "Pulmonologi",
    "Radiologi",
    "Rehabilitasi Medik",
]


# Pilihan kelas yang dipakai fakultas.
KELAS = [
    "A",
    "A & B & C",
    "A & C",
    "B",
    "C",
    "D",
    "Internasional",
    "Khusus",
    "Reguler",
]


def isi_kelas():
    """Tambahkan kelas yang belum ada. Aman dijalankan berulang."""
    baru = 0
    for nama in KELAS:
        if not Kelas.query.filter_by(nama=nama).first():
            db.session.add(Kelas(nama=nama))
            baru += 1
    db.session.commit()
    return baru


HENTI = {"dan", "di", "dari", "untuk"}


def _potong(nama):
    """Kata bermakna dari sebuah nama departemen; isi tanda kurung diabaikan."""
    bersih = re.sub(r"\([^)]*\)", " ", nama)
    return [k for k in re.findall(r"[A-Za-z0-9]+", bersih) if k.lower() not in HENTI]


def _singkat(kata, panjang=0):
    """Singkatan dari inisial. Kata yang sudah berupa akronim dipakai utuh,
    sehingga "IKM dan IKK" menjadi IKM, bukan II."""
    if not kata:
        return "DEP"
    if kata[0].isupper() and len(kata[0]) >= 2:
        dasar = kata[0]
    elif len(kata) == 1:
        dasar = kata[0][:3].upper()
    else:
        dasar = "".join(k if (k.isupper() and len(k) >= 2) else k[0] for k in kata).upper()
    if panjang and len(kata) > 1:
        dasar = dasar[:-1] + kata[-1][:1 + panjang].upper()
    elif panjang:
        dasar = kata[0][:3 + panjang].upper()
    return dasar


def kode_departemen(nama, dipakai):
    """Kode unik untuk satu departemen. `dipakai` adalah himpunan kode terpakai."""
    kata = _potong(nama)
    k = _singkat(kata)
    if k in dipakai:
        for tambah in range(1, 5):
            calon = _singkat(kata, tambah)
            if calon not in dipakai:
                return calon
        i = 2
        while f"{k}{i}" in dipakai:
            i += 1
        return f"{k}{i}"
    return k


def isi_departemen():
    """Tambahkan departemen yang belum ada dan lengkapi kode yang masih kosong.
    Aman dijalankan berulang."""
    baru = berkode = 0
    dipakai = {d.kode for d in Departemen.query.all() if d.kode}

    for nama in DEPARTEMEN:
        obj = Departemen.query.filter_by(nama=nama).first()
        if not obj:
            obj = Departemen(nama=nama)
            db.session.add(obj)
            baru += 1
        if not obj.kode:
            obj.kode = kode_departemen(nama, dipakai)
            dipakai.add(obj.kode)
            berkode += 1

    # departemen di luar daftar yang belum berkode ikut dilengkapi
    for obj in Departemen.query.all():
        if not obj.kode:
            obj.kode = kode_departemen(obj.nama, dipakai)
            dipakai.add(obj.kode)
            berkode += 1

    db.session.commit()
    return baru, berkode


def baca_rekap(path):
    """Ambil sesi, mahasiswa, dan status dari berkas rekap."""
    df = pd.read_excel(path, header=None)

    sesi = []
    for k in range(50):  # berhenti sendiri saat kolom habis
        c = 3 + 2 * k
        if c >= df.shape[1]:
            break
        tanggal, nama, jam = df.iat[7, c], df.iat[8, c], df.iat[9, c]
        if pd.isna(tanggal) or pd.isna(nama):
            break
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(tanggal))
        if not m:
            break
        jam_str = str(jam)
        jm = re.findall(r"(\d{1,2})[.:](\d{2})", jam_str)
        if len(jm) < 2:
            break
        sesi.append({
            "tanggal": datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date(),
            "nama": str(nama).strip(),
            "mulai": time(int(jm[0][0]), int(jm[0][1])),
            "selesai": time(int(jm[1][0]), int(jm[1][1])),
        })

    mahasiswa = []
    for r in range(11, df.shape[0]):
        nim, nama = df.iat[r, 1], df.iat[r, 2]
        if pd.isna(nim) or pd.isna(nama):
            continue
        status = []
        for k in range(len(sesi)):
            v = df.iat[r, 3 + 2 * k]
            status.append(str(v).strip().upper() if pd.notna(v) else "")
        mahasiswa.append({"nim": str(nim).strip(), "nama": str(nama).strip(), "status": status})

    # keterangan blok dari baris judul
    blok = kelas = semester = tahun = None
    for r in range(0, 8):
        for c in range(0, 3):
            v = df.iat[r, c]
            if pd.isna(v):
                continue
            t = str(v)
            if t.lower().startswith("blok:"):
                blok = t.split(":", 1)[1].strip()
            elif t.lower().startswith("kelas:"):
                kelas = t.split(":", 1)[1].strip()
            elif "SEMES" in t.upper():
                mm = re.search(r"SEMES\w*\s+(\w+)\s+([\d/]+)", t.upper())
                if mm:
                    semester, tahun = mm.group(1).capitalize(), mm.group(2)

    return {"sesi": sesi, "mahasiswa": mahasiswa, "blok": blok or "NEUROLOGI",
            "kelas": kelas or "A", "semester": semester or "Akhir",
            "tahun": tahun or "2025/2026"}


def kosongkan():
    """Hapus isi tabel dari anak ke induk agar kunci asing tidak tersandung."""
    urutan = (Ketidakhadiran, JadwalMahasiswa, JadwalJam, JadwalHari, JadwalKelas,
              Jadwal, LogScan, Mahasiswa, Kelas, MataKuliah, Mesin, Ruangan, Departemen)
    for model in urutan:
        model.query.delete()
    db.session.commit()


def main():
    ap = argparse.ArgumentParser(description="Isi basis data dengan data awal.")
    ap.add_argument("--rekap", help="berkas .xlsx rekap absensi (opsional)")
    ap.add_argument("--mentah", help="berkas .xls ekspor mesin (opsional)")
    ap.add_argument("--kosongkan", action="store_true", help="hapus isi tabel lebih dulu")
    ap.add_argument("--petakan-demo", action="store_true",
                    help="petakan ID Finger ke mahasiswa pertama (KARANGAN, untuk coba-coba)")
    a = ap.parse_args()

    d = baca_rekap(a.rekap) if a.rekap else None
    if d:
        print(f"Terbaca dari rekap : {len(d['mahasiswa'])} mahasiswa · {len(d['sesi'])} sesi")
        print(f"Blok               : {d['blok']} · Kelas {d['kelas']} · {d['semester']} {d['tahun']}")

    with app.app_context():
        if a.kosongkan:
            kosongkan()
            print("Tabel dikosongkan.")

        Pengaturan.ambil()

        baru_dep, berkode = isi_departemen()
        print(f"Departemen         : {baru_dep} baru, {berkode} diberi kode, "
              f"total {Departemen.query.count()}")

        baru_kls = isi_kelas()
        print(f"Kelas              : {baru_kls} baru, total {Kelas.query.count()}")

        if d is None:
            print("\nSelesai. Berkas rekap tidak diberikan, jadi hanya departemen yang diisi.")
            return

        dep = Departemen.query.filter_by(nama="Pendidikan Dokter").first()
        if not dep:
            dep = Departemen(kode="PD", nama="Pendidikan Dokter")
            db.session.add(dep)
            db.session.flush()

        # NIM berbentuk C011241006: empat huruf/angka kode prodi, lalu dua digit angkatan
        angkatan = None
        if d["mahasiswa"]:
            m = re.search(r"[A-Za-z]\d{3}(\d{2})", d["mahasiswa"][0]["nim"])
            if m:
                angkatan = "20" + m.group(1)
        kelas = Kelas.query.filter_by(nama=d["kelas"], angkatan=angkatan).first()
        if not kelas:
            kelas = Kelas(nama=d["kelas"], angkatan=angkatan, departemen_id=dep.id)
            db.session.add(kelas)
            db.session.flush()

        # ---------- ruangan ----------
        ruang = {}
        for nama in ("Ruang PBL 1", "Ruang PBL 2", "Ruang PBL 3", "Ruang PBL 4", "Ruang Pleno"):
            r = Ruangan.query.filter_by(nama=nama).first()
            if not r:
                r = Ruangan(kode=nama.replace("Ruang ", "").replace(" ", "").upper(),
                            nama=nama, kapasitas=200 if "Pleno" in nama else 25)
                db.session.add(r)
                db.session.flush()
            ruang[nama] = r

        # ---------- mahasiswa ----------
        baru = 0
        peta_mhs = {}
        for m in d["mahasiswa"]:
            obj = Mahasiswa.query.filter_by(nim=m["nim"]).first()
            if not obj:
                # ID Finger mengikuti NIM: mesin didaftarkan dengan NIM sebagai User ID
            obj = Mahasiswa(nim=m["nim"], nama=m["nama"], kelas_id=kelas.id,
                            id_finger=m["nim"])
                db.session.add(obj)
                db.session.flush()
                baru += 1
            peta_mhs[m["nim"]] = obj
        # mahasiswa lama yang belum berisi ID Finger ikut disamakan dengan NIM
        disamakan = 0
        for obj in Mahasiswa.query.all():
            if not (obj.id_finger or "").strip():
                obj.id_finger = obj.nim
                disamakan += 1
        db.session.commit()
        print(f"Mahasiswa          : {baru} baru, {disamakan} ID Finger disamakan "
              f"dengan NIM, total {Mahasiswa.query.count()}")

        # ---------- mata kuliah + jadwal ----------
        mk = MataKuliah.query.filter_by(nama=d["blok"]).first()
        if not mk:
            mk = MataKuliah(kode=d["blok"][:3].upper(), nama=d["blok"], sks=5, departemen_id=dep.id)
            db.session.add(mk)
            db.session.flush()

        jadwal = Jadwal.query.filter_by(mata_kuliah_id=mk.id, tahun_ajaran=d["tahun"]).first()
        if not jadwal:
            jadwal = Jadwal(mata_kuliah_id=mk.id, semester=d["semester"], tahun_ajaran=d["tahun"])
            db.session.add(jadwal)
            db.session.flush()

        jk = JadwalKelas.query.filter_by(jadwal_id=jadwal.id, kelas_id=kelas.id).first()
        if not jk:
            jk = JadwalKelas(jadwal_id=jadwal.id, kelas_id=kelas.id)
            db.session.add(jk)
            db.session.flush()

        terdaftar = {x.mahasiswa_id for x in jk.peserta}
        for obj in peta_mhs.values():
            if obj.id not in terdaftar:
                db.session.add(JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=obj.id))
        db.session.commit()

        # ---------- sesi ----------
        peta_sesi = []
        for s in d["sesi"]:
            hari = JadwalHari.query.filter_by(jadwal_kelas_id=jk.id, tanggal=s["tanggal"]).first()
            if not hari:
                hari = JadwalHari(jadwal_kelas_id=jk.id, tanggal=s["tanggal"])
                db.session.add(hari)
                db.session.flush()
            sesi = JadwalJam.query.filter_by(jadwal_hari_id=hari.id, kegiatan=s["nama"]).first()
            if not sesi:
                menit = (s["selesai"].hour * 60 + s["selesai"].minute) - (s["mulai"].hour * 60 + s["mulai"].minute)
                sesi = JadwalJam(
                    jadwal_hari_id=hari.id,
                    kegiatan=s["nama"],
                    jam_masuk=s["mulai"],
                    jml_jam=max(1, round(menit / 50)),
                    jam_selesai_manual=s["selesai"],
                    ruangan_id=ruang["Ruang Pleno"].id if "PLENO" in s["nama"].upper() else ruang["Ruang PBL 1"].id,
                )
                db.session.add(sesi)
                db.session.flush()
            peta_sesi.append(sesi)
        db.session.commit()
        print(f"Sesi               : {len(peta_sesi)} — " +
              ", ".join(f"{s.kegiatan} {s.jam_masuk.strftime('%H.%M')}" for s in peta_sesi))

        # ---------- sakit & izin dari rekap ----------
        tambah_s = tambah_i = 0
        for m in d["mahasiswa"]:
            obj = peta_mhs[m["nim"]]
            for i, st in enumerate(m["status"]):
                if st not in ("S", "I") or i >= len(peta_sesi):
                    continue
                sesi = peta_sesi[i]
                ada = Ketidakhadiran.query.filter_by(
                    mahasiswa_id=obj.id, jadwal_jam_id=sesi.id, jenis=st).first()
                if ada:
                    continue
                db.session.add(Ketidakhadiran(
                    mahasiswa_id=obj.id, jenis=st, tanggal=sesi.hari.tanggal,
                    jadwal_jam_id=sesi.id, keterangan="Dari rekap sebelumnya"))
                if st == "S":
                    tambah_s += 1
                else:
                    tambah_i += 1
        db.session.commit()
        print(f"Ketidakhadiran     : {tambah_s} sakit, {tambah_i} izin")

        # ---------- data mentah ----------
        if a.mentah:
            with open(a.mentah, "rb") as f:
                log, fmt = pembaca.gabung_mentah([io.BytesIO(f.read())])
            awal, akhir = log.tanggal.min().date(), log.tanggal.max().date()
            ada = {(s.id_finger, s.tanggal, s.jam, s.serial)
                   for s in LogScan.query.filter(LogScan.tanggal >= awal,
                                                 LogScan.tanggal <= akhir).all()}
            n = 0
            for r in log.itertuples(index=False):
                jam = time(int(r.jam[:2]), int(r.jam[3:5]))
                kunci = (str(r.uid), r.tanggal.date(), jam, None)
                if kunci in ada:
                    continue
                ada.add(kunci)
                db.session.add(LogScan(id_finger=str(r.uid), nama_mesin=r.nama,
                                       tanggal=r.tanggal.date(), jam=jam, sumber="impor"))
                n += 1
            db.session.commit()
            print(f"Log scan           : {n} baru dari format {fmt}, total {LogScan.query.count()}")

        # ---------- pemetaan demo ----------
        if a.petakan_demo:
            uid = sorted({s.id_finger for s in LogScan.query.all()}, key=lambda x: int(x))
            urut = sorted(peta_mhs.values(), key=lambda m: m.nim)
            n = 0
            for m, u in zip(urut, uid):
                if not m.id_finger:
                    m.id_finger = u
                    n += 1
            db.session.commit()
            print(f"ID Finger (DEMO)   : {n} mahasiswa dipetakan — pemetaan KARANGAN, bukan data asli")

        tanpa = Mahasiswa.query.filter((Mahasiswa.id_finger.is_(None)) | (Mahasiswa.id_finger == "")).count()
        print(f"\nSelesai. Mahasiswa tanpa ID Finger: {tanpa}")
        if tanpa:
            print("Isi ID Finger lewat menu Mahasiswa agar kehadiran bisa dibaca dari mesin.")


if __name__ == "__main__":
    sys.exit(main())

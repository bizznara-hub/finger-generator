"""Beranda dan pengaturan."""

from datetime import datetime

from flask import jsonify, request
from sqlalchemy import func

from core.models import (
    Dosen,
    Jadwal,
    JadwalJam,
    Kelas,
    Ketidakhadiran,
    LogScan,
    Mahasiswa,
    MataKuliah,
    Pengaturan,
    ProfilJam,
    Ruangan,
    db,
)

from . import GalatAPI, bp


@bp.get("/beranda")
def beranda():
    tanpa_finger = (Mahasiswa.query
                    .filter((Mahasiswa.id_finger.is_(None)) | (Mahasiswa.id_finger == ""))
                    .order_by(Mahasiswa.nim).all())
    awal, akhir = db.session.query(func.min(LogScan.tanggal), func.max(LogScan.tanggal)).one()

    # sepuluh hari terakhir yang ada datanya, untuk grafik batang
    tren = (db.session.query(LogScan.tanggal, func.count(LogScan.id))
            .group_by(LogScan.tanggal).order_by(LogScan.tanggal.desc()).limit(14).all())

    return jsonify(
        angka=[
            {"label": "Mahasiswa", "nilai": Mahasiswa.query.count(), "rute": "/master/mahasiswa", "ikon": "lucide:users"},
            {"label": "Dosen", "nilai": Dosen.query.count(), "rute": "/master/dosen", "ikon": "lucide:user-round"},
            {"label": "Kelas", "nilai": Kelas.query.count(), "rute": "/master/kelas", "ikon": "lucide:layout-grid"},
            {"label": "Mata kuliah", "nilai": MataKuliah.query.count(), "rute": "/master/mata-kuliah", "ikon": "lucide:book-open"},
            {"label": "Ruangan", "nilai": Ruangan.query.count(), "rute": "/master/ruangan", "ikon": "lucide:door-open"},
            {"label": "Blok terjadwal", "nilai": Jadwal.query.count(), "rute": "/jadwal", "ikon": "lucide:calendar-days"},
            {"label": "Sesi", "nilai": JadwalJam.query.count(), "rute": "/jadwal", "ikon": "lucide:clock"},
            {"label": "Scan tersimpan", "nilai": LogScan.query.count(), "rute": "/finger-print/log", "ikon": "lucide:fingerprint"},
        ],
        rentang={"awal": awal.strftime("%d/%m/%Y") if awal else None,
                 "akhir": akhir.strftime("%d/%m/%Y") if akhir else None},
        jumlah_izin=Ketidakhadiran.query.count(),
        tren=[{"tanggal": t.strftime("%d/%m"), "jumlah": n} for t, n in reversed(tren)],
        tanpa_finger=[{"id": m.id, "nim": m.nim, "nama": m.nama,
                       "kelas": m.kelas.label if m.kelas else None} for m in tanpa_finger],
    )


@bp.get("/pengaturan")
def ambil_pengaturan():
    p = Pengaturan.ambil()
    return jsonify(profil_jam=[_profil(x) for x in ProfilJam.query.order_by(ProfilJam.id)],
                   pengaturan={
        "toleransi_awal": p.toleransi_awal, "toleransi_akhir": p.toleransi_akhir,
        "nama_institusi": p.nama_institusi, "nama_universitas": p.nama_universitas,
        "attlog_host": p.attlog_host, "attlog_port": p.attlog_port,
        "attlog_nama_db": p.attlog_nama_db, "attlog_user": p.attlog_user,
        "attlog_sandi_tersimpan": bool(p.attlog_sandi),
    })


@bp.put("/pengaturan")
def simpan_pengaturan():
    p = Pengaturan.ambil()
    d = request.get_json(silent=True) or {}

    def angka(k, baku):
        try:
            return int(d.get(k, baku))
        except (TypeError, ValueError):
            return baku

    p.toleransi_awal = angka("toleransi_awal", 15)
    p.toleransi_akhir = angka("toleransi_akhir", 15)

    def jam(k):
        t = (d.get(k) or "").strip()
        for pola in ("%H:%M", "%H.%M"):
            try:
                return datetime.strptime(t, pola).time()
            except ValueError:
                continue
        return None

    p.nama_institusi = (d.get("nama_institusi") or "").strip() or None
    p.nama_universitas = (d.get("nama_universitas") or "").strip() or None
    p.attlog_host = (d.get("attlog_host") or "").strip() or None
    p.attlog_port = angka("attlog_port", 3306)
    p.attlog_nama_db = (d.get("attlog_nama_db") or "").strip() or None
    p.attlog_user = (d.get("attlog_user") or "").strip() or None
    if (d.get("attlog_sandi") or "").strip():
        p.attlog_sandi = d["attlog_sandi"].strip()
    db.session.commit()
    return jsonify(pesan="Pengaturan disimpan.")


# --------------------------------------------------------------------------
# Profil jam. Aplikasi PHP menyimpan beberapa aturan sekaligus dan tiap jadwal
# menunjuk salah satunya, jadi daftarnya perlu bisa diubah admin sendiri.
# --------------------------------------------------------------------------


def _profil(x):
    def jam(t):
        return t.strftime("%H:%M") if t else ""

    return {
        "id": x.id,
        "label": x.label,
        "menit_perjam": x.menit_perjam,
        "menit_pergantian": x.menit_pergantian,
        "jam_kuliah": jam(x.jam_kuliah),
        "istirahat_mulai": jam(x.istirahat_mulai),
        "istirahat_selesai": jam(x.istirahat_selesai),
        "jam_perhari": x.jam_perhari,
        "bawaan": x.bawaan,
        "dipakai": Jadwal.query.filter_by(profil_jam_id=x.id).count(),
    }


def _jam_atau_none(t):
    t = (t or "").strip()
    for pola in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(t, pola).time()
        except ValueError:
            continue
    return None


def _terapkan_profil(x, d):
    def angka(k, baku):
        try:
            return int(d.get(k, baku))
        except (TypeError, ValueError):
            return baku

    x.menit_perjam = angka("menit_perjam", 50)
    x.menit_pergantian = angka("menit_pergantian", 0)
    x.jam_perhari = angka("jam_perhari", 8)
    x.jam_kuliah = _jam_atau_none(d.get("jam_kuliah"))
    x.istirahat_mulai = _jam_atau_none(d.get("istirahat_mulai"))
    x.istirahat_selesai = _jam_atau_none(d.get("istirahat_selesai"))

    if not 1 <= x.menit_perjam <= 180:
        raise GalatAPI("Jumlah menit per jam harus antara 1 dan 180.")
    if not 0 <= x.menit_pergantian <= 120:
        raise GalatAPI("Menit pergantian harus antara 0 dan 120.")
    if not 1 <= x.jam_perhari <= 24:
        raise GalatAPI("Jumlah jam per hari harus antara 1 dan 24.")
    # Istirahat hanya bermakna bila keduanya terisi dan urutannya benar.
    if bool(x.istirahat_mulai) != bool(x.istirahat_selesai):
        raise GalatAPI("Jam istirahat harus diisi keduanya, atau dikosongkan keduanya.")
    if x.istirahat_mulai and x.istirahat_selesai <= x.istirahat_mulai:
        raise GalatAPI("Istirahat selesai harus sesudah istirahat mulai.")


@bp.get("/profil-jam")
def daftar_profil():
    return jsonify(baris=[_profil(x) for x in ProfilJam.query.order_by(ProfilJam.id)])


@bp.post("/profil-jam")
def tambah_profil():
    x = ProfilJam()
    _terapkan_profil(x, request.get_json(silent=True) or {})
    db.session.add(x)
    db.session.commit()
    return jsonify(baris=_profil(x), pesan="Pengaturan jam ditambahkan.")


@bp.put("/profil-jam/<int:id_profil>")
def ubah_profil(id_profil):
    x = db.session.get(ProfilJam, id_profil)
    if x is None:
        raise GalatAPI("Pengaturan jam tidak ditemukan.", 404)
    _terapkan_profil(x, request.get_json(silent=True) or {})
    db.session.commit()
    return jsonify(baris=_profil(x), pesan="Pengaturan jam diperbarui.")


@bp.post("/profil-jam/<int:id_profil>/bawaan")
def jadikan_bawaan(id_profil):
    x = db.session.get(ProfilJam, id_profil)
    if x is None:
        raise GalatAPI("Pengaturan jam tidak ditemukan.", 404)
    ProfilJam.query.update({ProfilJam.bawaan: False})
    x.bawaan = True
    db.session.commit()
    return jsonify(pesan=f"{x.label} dijadikan bawaan.")


@bp.delete("/profil-jam/<int:id_profil>")
def hapus_profil(id_profil):
    x = db.session.get(ProfilJam, id_profil)
    if x is None:
        raise GalatAPI("Pengaturan jam tidak ditemukan.", 404)
    # Diperiksa sendiri, bukan diserahkan ke kunci asing: SQLite tidak
    # menegakkannya sehingga jadwal akan menunjuk profil yang sudah hilang.
    dipakai = Jadwal.query.filter_by(profil_jam_id=x.id).count()
    if dipakai:
        raise GalatAPI(f"Tidak bisa dihapus karena masih dipakai {dipakai} jadwal.")
    if ProfilJam.query.count() <= 1:
        raise GalatAPI("Sisakan sedikitnya satu pengaturan jam.")
    sisa_bawaan = x.bawaan
    db.session.delete(x)
    db.session.flush()
    if sisa_bawaan:
        lain = ProfilJam.query.order_by(ProfilJam.id).first()
        if lain:
            lain.bawaan = True
    db.session.commit()
    return jsonify(pesan="Pengaturan jam dihapus.")

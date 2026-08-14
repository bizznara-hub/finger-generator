"""Beranda dan pengaturan."""

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
    Ruangan,
    db,
)

from . import bp


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
    return jsonify(pengaturan={
        "menit_perjam": p.menit_perjam, "menit_pergantian": p.menit_pergantian,
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

    p.menit_perjam = angka("menit_perjam", 50)
    p.menit_pergantian = angka("menit_pergantian", 10)
    p.toleransi_awal = angka("toleransi_awal", 15)
    p.toleransi_akhir = angka("toleransi_akhir", 15)
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

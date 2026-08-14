"""Beranda - ringkasan keadaan data."""

from flask import Blueprint
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
    Ruangan,
    db,
)

from .dasar import halaman

bp = Blueprint("beranda", __name__)


@bp.route("/")
def index():
    tanpa_finger = (
        Mahasiswa.query.filter(
            (Mahasiswa.id_finger.is_(None)) | (Mahasiswa.id_finger == "")
        )
        .order_by(Mahasiswa.nim)
        .all()
    )
    rentang = db.session.query(
        func.min(LogScan.tanggal), func.max(LogScan.tanggal)
    ).one()

    angka = [
        ("Mahasiswa", Mahasiswa.query.count(), "master.daftar", {"kunci": "mahasiswa"}),
        ("Dosen", Dosen.query.count(), "master.daftar", {"kunci": "dosen"}),
        ("Kelas", Kelas.query.count(), "master.daftar", {"kunci": "kelas"}),
        ("Mata kuliah", MataKuliah.query.count(), "master.daftar", {"kunci": "mata-kuliah"}),
        ("Ruangan", Ruangan.query.count(), "master.daftar", {"kunci": "ruangan"}),
        ("Blok terjadwal", Jadwal.query.count(), "jadwal.daftar", {}),
        ("Sesi", JadwalJam.query.count(), "jadwal.daftar", {}),
        ("Scan tersimpan", LogScan.query.count(), "absensi.log", {}),
    ]

    return halaman(
        "beranda",
        "beranda.html",
        angka=angka,
        tanpa_finger=tanpa_finger,
        rentang=rentang,
        jumlah_izin=Ketidakhadiran.query.count(),
    )


def daftarkan(app):
    app.register_blueprint(bp)

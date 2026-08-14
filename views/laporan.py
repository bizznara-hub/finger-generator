"""Menu Laporan - pratinjau dan unduh rekap absensi per blok."""

import re

from flask import Blueprint, abort, request, send_file

from core import laporan as mesin
from core import rekap
from core.models import Jadwal, JadwalKelas, Pengaturan, db

from .dasar import ambil_int, galat, halaman

bp = Blueprint("laporan", __name__, url_prefix="/laporan")


def _nama_berkas(teks):
    bersih = re.sub(r"[^A-Za-z0-9 _-]+", "", teks).strip() or "Rekapan Absensi"
    return bersih[:120]


def _judul_dan_meta(jk, pengaturan):
    jadwal = jk.jadwal
    semester = (jadwal.semester or "").upper()
    tahun = jadwal.tahun_ajaran or ""
    baris1 = " ".join(x for x in ["LAPORAN ABSEN MAHASISWA SEMESTER", semester, tahun] if x)
    judul = [baris1, pengaturan.nama_institusi or "", pengaturan.nama_universitas or ""]
    meta = [
        f"Blok:  {jadwal.mata_kuliah.nama if jadwal.mata_kuliah else '-'}",
        f"Kelas: {jk.kelas.nama if jk.kelas else '-'}",
    ]
    return [b for b in judul if b], meta


@bp.route("/")
def index():
    pengaturan = Pengaturan.ambil()
    id_jk = ambil_int(request.args.get("kelas"))
    bentuk = request.args.get("bentuk", "ringkas")
    cocokkan = request.args.get("ruangan") == "1"

    pilihan = (
        db.session.query(JadwalKelas)
        .join(Jadwal, JadwalKelas.jadwal_id == Jadwal.id)
        .order_by(Jadwal.id.desc())
        .all()
    )

    jk = sesi = baris = angka = None
    if id_jk:
        jk = db.session.get(JadwalKelas, id_jk) or abort(404)
        sesi, baris = mesin.susun(jk.id, pengaturan, cocokkan_ruangan=cocokkan)
        angka = mesin.statistik(sesi, baris)
        if not sesi:
            galat("Blok ini belum punya sesi. Tambahkan dulu di menu Jadwal Kuliah.")
        elif not baris:
            galat("Belum ada mahasiswa terdaftar pada kelas ini.")

    return halaman(
        "laporan",
        "laporan/index.html",
        pilihan=pilihan,
        jk=jk,
        sesi=sesi,
        baris=baris,
        angka=angka,
        bentuk=bentuk,
        cocokkan=cocokkan,
        pratinjau=(baris or [])[:60],
    )


@bp.route("/unduh")
def unduh():
    pengaturan = Pengaturan.ambil()
    id_jk = ambil_int(request.args.get("kelas"))
    bentuk = request.args.get("bentuk", "ringkas")
    cocokkan = request.args.get("ruangan") == "1"
    if not id_jk:
        abort(400)

    jk = db.session.get(JadwalKelas, id_jk) or abort(404)
    sesi, baris = mesin.susun(jk.id, pengaturan, cocokkan_ruangan=cocokkan)
    if not sesi or not baris:
        abort(400)

    judul, meta = _judul_dan_meta(jk, pengaturan)
    buf = rekap.tulis_xlsx(sesi, baris, judul, meta, bentuk=bentuk)

    blok = jk.jadwal.mata_kuliah.nama if jk.jadwal.mata_kuliah else "Blok"
    nama = _nama_berkas(f"Rekapan Absensi {blok} Kelas {jk.kelas.nama if jk.kelas else ''}")
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{nama}.xlsx",
    )


def daftarkan(app):
    app.register_blueprint(bp)

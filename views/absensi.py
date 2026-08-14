"""Menu Finger Print - dua jalur pengambilan data mentah, plus daftar log scan."""

import io
from datetime import datetime, time

from flask import Blueprint, redirect, request, url_for

from core import attlog, parser
from core.models import LogScan, Mesin, Pengaturan, db

from .dasar import galat, halaman, sukses

bp = Blueprint("absensi", __name__, url_prefix="/finger-print")


def _tanggal(teks):
    try:
        return datetime.strptime(teks, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@bp.route("/")
def index():
    pengaturan = Pengaturan.ambil()
    terakhir = LogScan.query.order_by(LogScan.tanggal.desc(), LogScan.jam.desc()).first()
    per_sumber = (
        db.session.query(LogScan.sumber, db.func.count(LogScan.id))
        .group_by(LogScan.sumber)
        .all()
    )
    return halaman(
        "finger",
        "absensi/index.html",
        mesin=Mesin.query.order_by(Mesin.serial).all(),
        pengaturan=pengaturan,
        jumlah=LogScan.query.count(),
        terakhir=terakhir,
        per_sumber=per_sumber,
        attlog_siap=bool(pengaturan.attlog_host and pengaturan.attlog_nama_db),
    )


@bp.post("/impor")
def impor():
    berkas = request.files.getlist("berkas")
    if not berkas or all(f.filename == "" for f in berkas):
        galat("Belum ada berkas yang dipilih.")
        return redirect(url_for("absensi.index"))

    isi = []
    for f in berkas:
        nama = (f.filename or "").lower()
        if not nama.endswith((".xls", ".xlsx")):
            galat(f"Format berkas {f.filename} tidak didukung. Gunakan .xls atau .xlsx.")
            return redirect(url_for("absensi.index"))
        isi.append(io.BytesIO(f.read()))

    try:
        log, format_terpakai = parser.gabung_mentah(isi)
    except parser.FormatTidakDikenali as e:
        galat(str(e))
        return redirect(url_for("absensi.index"))
    except Exception as e:  # noqa: BLE001 - tampilkan apa adanya ke admin
        galat(f"Gagal membaca berkas: {e}")
        return redirect(url_for("absensi.index"))

    tanggal_awal = log.tanggal.min().date()
    tanggal_akhir = log.tanggal.max().date()
    ada = {
        (s.id_finger, s.tanggal, s.jam, s.serial)
        for s in LogScan.query.filter(
            LogScan.tanggal >= tanggal_awal, LogScan.tanggal <= tanggal_akhir
        ).all()
    }

    baru = dilewati = 0
    for r in log.itertuples(index=False):
        jam = time(int(r.jam[:2]), int(r.jam[3:5]))
        kunci = (str(r.uid), r.tanggal.date(), jam, None)
        if kunci in ada:
            dilewati += 1
            continue
        ada.add(kunci)
        db.session.add(
            LogScan(
                id_finger=str(r.uid),
                nama_mesin=r.nama,
                tanggal=r.tanggal.date(),
                jam=jam,
                serial=None,
                sumber="impor",
            )
        )
        baru += 1
    db.session.commit()

    sukses(
        f"Impor selesai dari format {', '.join(format_terpakai)}: "
        f"{baru} scan baru, {dilewati} kembar dilewati."
    )
    return redirect(url_for("absensi.log"))


@bp.post("/tarik")
def tarik():
    pengaturan = Pengaturan.ambil()
    awal = _tanggal(request.form.get("tanggal_awal"))
    akhir = _tanggal(request.form.get("tanggal_akhir"))
    if awal is None or akhir is None:
        galat("Isi rentang tanggal terlebih dahulu.")
        return redirect(url_for("absensi.index"))
    if akhir < awal:
        awal, akhir = akhir, awal
    try:
        baru, dilewati = attlog.tarik(pengaturan, awal, akhir)
    except attlog.GalatAttlog as e:
        galat(str(e))
        return redirect(url_for("absensi.index"))
    sukses(f"Tarik att_log selesai: {baru} scan baru, {dilewati} kembar dilewati.")
    return redirect(url_for("absensi.log"))


@bp.post("/uji-koneksi")
def uji_koneksi():
    try:
        jumlah = attlog.uji_koneksi(Pengaturan.ambil())
        sukses(f"Koneksi berhasil. Tabel att_log berisi {jumlah:,} baris.".replace(",", "."))
    except attlog.GalatAttlog as e:
        galat(str(e))
    return redirect(url_for("absensi.index"))


@bp.route("/log")
def log():
    hal = max(1, int(request.args.get("hal", 1) or 1))
    kata = (request.args.get("cari") or "").strip()
    q = LogScan.query
    if kata:
        q = q.filter(LogScan.id_finger.ilike(f"%{kata}%"))
    q = q.order_by(LogScan.tanggal.desc(), LogScan.jam.desc())
    per_hal = 100
    total = q.count()
    baris = q.limit(per_hal).offset((hal - 1) * per_hal).all()
    return halaman(
        "finger",
        "absensi/log.html",
        baris=baris,
        hal=hal,
        total=total,
        per_hal=per_hal,
        kata=kata,
        halaman_akhir=max(1, -(-total // per_hal)),
    )


@bp.post("/log/kosongkan")
def kosongkan():
    jumlah = LogScan.query.delete()
    db.session.commit()
    sukses(f"{jumlah} baris log scan dihapus.")
    return redirect(url_for("absensi.log"))


def daftarkan(app):
    app.register_blueprint(bp)

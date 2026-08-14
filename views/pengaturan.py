"""Menu Pengaturan - aturan jam, toleransi, identitas kop, koneksi att_log."""

from flask import Blueprint, redirect, request, url_for

from core.models import Pengaturan, db

from .dasar import ambil_int, ambil_teks, halaman, sukses

bp = Blueprint("pengaturan", __name__, url_prefix="/pengaturan")


@bp.route("/", methods=["GET", "POST"])
def index():
    p = Pengaturan.ambil()
    if request.method == "POST":
        p.menit_perjam = ambil_int(request.form.get("menit_perjam"), 50) or 50
        p.menit_pergantian = ambil_int(request.form.get("menit_pergantian"), 10) or 0
        p.toleransi_awal = ambil_int(request.form.get("toleransi_awal"), 15) or 0
        p.toleransi_akhir = ambil_int(request.form.get("toleransi_akhir"), 15) or 0
        p.nama_institusi = ambil_teks(request.form, "nama_institusi")
        p.nama_universitas = ambil_teks(request.form, "nama_universitas")
        p.attlog_host = ambil_teks(request.form, "attlog_host") or None
        p.attlog_port = ambil_int(request.form.get("attlog_port"), 3306)
        p.attlog_nama_db = ambil_teks(request.form, "attlog_nama_db") or None
        p.attlog_user = ambil_teks(request.form, "attlog_user") or None
        sandi = ambil_teks(request.form, "attlog_sandi")
        if sandi:
            p.attlog_sandi = sandi
        db.session.commit()
        sukses("Pengaturan disimpan.")
        return redirect(url_for("pengaturan.index"))
    return halaman("pengaturan", "pengaturan.html", p=p)


def daftarkan(app):
    app.register_blueprint(bp)

"""Menu Akun - ubah identitas dan sandi admin."""

from flask import Blueprint, g, redirect, request, url_for

from core.models import Pengguna, db

from .dasar import ambil_teks, galat, halaman, sukses

bp = Blueprint("akun", __name__, url_prefix="/akun")


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nama = ambil_teks(request.form, "nama")
        username = ambil_teks(request.form, "username")
        lama = request.form.get("sandi_lama") or ""
        baru = request.form.get("sandi_baru") or ""
        ulang = request.form.get("sandi_ulang") or ""

        if not nama or not username:
            galat("Nama dan username wajib diisi.")
        elif Pengguna.query.filter(
            Pengguna.username == username, Pengguna.id != g.pengguna.id
        ).first():
            galat("Username itu sudah dipakai.")
        elif baru and not g.pengguna.cek_sandi(lama):
            galat("Sandi lama salah.")
        elif baru and baru != ulang:
            galat("Sandi baru dan ulangannya tidak sama.")
        elif baru and len(baru) < 6:
            galat("Sandi baru minimal 6 karakter.")
        else:
            g.pengguna.nama = nama
            g.pengguna.username = username
            if baru:
                g.pengguna.set_sandi(baru)
            db.session.commit()
            sukses("Akun diperbarui.")
            return redirect(url_for("akun.index"))
    return halaman("akun", "akun.html")


def daftarkan(app):
    app.register_blueprint(bp)

"""Masuk dan keluar aplikasi."""

from flask import Blueprint, redirect, render_template, request, session, url_for

from core.models import Pengguna

bp = Blueprint("auth", __name__)


@bp.route("/masuk", methods=["GET", "POST"])
def masuk():
    galat = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        sandi = request.form.get("sandi") or ""
        pengguna = Pengguna.query.filter_by(username=username).first()
        if pengguna and pengguna.aktif and pengguna.cek_sandi(sandi):
            session.clear()
            session["pengguna"] = pengguna.id
            lanjut = request.args.get("lanjut")
            if lanjut and lanjut.startswith("/"):
                return redirect(lanjut)
            return redirect(url_for("beranda.index"))
        galat = "Username atau sandi salah."
    return render_template("masuk.html", galat=galat)


@bp.route("/keluar")
def keluar():
    session.clear()
    return redirect(url_for("auth.masuk"))


def daftarkan(app):
    app.register_blueprint(bp)

"""Sistem Absensi Fakultas Kedokteran - titik masuk aplikasi."""

import os

from flask import Flask, g, redirect, request, session, url_for

from core.models import Pengaturan, Pengguna, db, semai_awal

BASIS = os.path.dirname(os.path.abspath(__file__))

# Halaman yang boleh dibuka tanpa login
BEBAS = {"auth.masuk", "static"}


def url_basis_data():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///" + os.path.join(BASIS, "data.db")
    # Heroku/Vercel kadang memberi skema lama yang tidak dikenali SQLAlchemy 2
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def buat_aplikasi():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "ganti-kunci-ini-di-produksi"),
        SQLALCHEMY_DATABASE_URI=url_basis_data(),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
    )
    db.init_app(app)

    from views import (
        absensi,
        akun,
        auth,
        beranda,
        izin,
        jadwal,
        laporan,
        master,
        pengaturan,
    )

    for modul in (
        auth,
        beranda,
        master,
        jadwal,
        absensi,
        izin,
        laporan,
        pengaturan,
        akun,
    ):
        modul.daftarkan(app)

    @app.before_request
    def wajib_masuk():
        if request.endpoint in BEBAS or request.endpoint is None:
            return None
        pengguna_id = session.get("pengguna")
        if not pengguna_id:
            return redirect(url_for("auth.masuk", lanjut=request.path))
        g.pengguna = db.session.get(Pengguna, pengguna_id)
        if g.pengguna is None or not g.pengguna.aktif:
            session.clear()
            return redirect(url_for("auth.masuk"))
        g.pengaturan = Pengaturan.ambil()
        return None

    @app.context_processor
    def bagikan():
        return {
            "pengguna": getattr(g, "pengguna", None),
            "menu_aktif": getattr(g, "menu_aktif", ""),
        }

    with app.app_context():
        db.create_all()
        if semai_awal():
            app.logger.info("Akun awal dibuat: admin / admin")

    return app


app = buat_aplikasi()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=bool(os.environ.get("DEBUG")))

"""Sistem Absensi Fakultas Kedokteran.

Flask berperan sebagai REST API dan penyaji hasil build antarmuka Vue.
Seluruh logika domain tetap di paket `core/` dan tidak menyentuh lapisan web.
"""

import os
from datetime import timedelta

from flask import Flask, jsonify, send_from_directory

from core.models import db, semai_awal

BASIS = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(BASIS, "web", "dist")


def url_basis_data():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///" + os.path.join(BASIS, "data.db")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def buat_aplikasi():
    app = Flask(__name__, static_folder=None)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "ganti-kunci-ini-di-produksi"),
        SQLALCHEMY_DATABASE_URI=url_basis_data(),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        SESSION_COOKIE_SAMESITE="Lax",
    )
    db.init_app(app)

    from api import daftarkan as daftarkan_api

    daftarkan_api(app)

    # ---------- penyajian antarmuka Vue ----------

    @app.route("/", defaults={"jalur": ""})
    @app.route("/<path:jalur>")
    def spa(jalur):
        """Kirim berkas statis bila ada; selebihnya index.html agar router Vue bekerja."""
        if not os.path.isdir(DIST):
            return (
                jsonify(
                    error="Antarmuka belum dibangun.",
                    petunjuk="Jalankan: cd web && npm install && npm run build",
                ),
                503,
            )
        penuh = os.path.join(DIST, jalur)
        if jalur and os.path.isfile(penuh):
            return send_from_directory(DIST, jalur)
        return send_from_directory(DIST, "index.html")

    with app.app_context():
        db.create_all()
        if semai_awal():
            app.logger.info("Akun awal dibuat: admin / admin")

    return app


app = buat_aplikasi()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=bool(os.environ.get("DEBUG")))

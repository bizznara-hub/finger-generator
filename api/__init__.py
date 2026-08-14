"""REST API untuk antarmuka Vue.

Seluruh rute mengembalikan JSON. Satu-satunya pengecualian adalah unduhan
berkas (laporan .xlsx dan template roster) yang mengembalikan biner.
"""

from flask import Blueprint, jsonify, session

from core.models import Pengguna, db

bp = Blueprint("api", __name__, url_prefix="/api")

# Rute yang boleh diakses tanpa sesi
BEBAS = {"api.masuk", "api.status"}


class GalatAPI(Exception):
    """Kesalahan yang aman ditampilkan ke pengguna."""

    def __init__(self, pesan, kode=400):
        super().__init__(pesan)
        self.pesan = pesan
        self.kode = kode


def pengguna_aktif():
    pid = session.get("pengguna")
    if not pid:
        return None
    p = db.session.get(Pengguna, pid)
    return p if (p and p.aktif) else None


def daftarkan(app):
    from . import auth, jadwal, laporan, master, mentah, sistem  # noqa: F401

    @bp.before_request
    def _jaga():
        from flask import request

        if request.endpoint in BEBAS:
            return None
        if pengguna_aktif() is None:
            return jsonify(error="Sesi berakhir. Silakan masuk kembali."), 401
        return None

    @bp.errorhandler(GalatAPI)
    def _galat(e):
        return jsonify(error=e.pesan), e.kode

    @bp.errorhandler(Exception)
    def _tak_terduga(e):
        app.logger.exception("Galat tak terduga pada API")
        return jsonify(error=f"Terjadi kesalahan: {e}"), 500

    app.register_blueprint(bp)

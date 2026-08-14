"""Menu Sakit dan Izin.

Keduanya satu tabel dengan kolom jenis (S / I), tetapi tampil sebagai dua menu
terpisah supaya alur kerja petugas tetap sesuai kebiasaan.
"""

from datetime import datetime

from flask import Blueprint, abort, redirect, request, url_for

from core.models import (
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    Ketidakhadiran,
    Mahasiswa,
    db,
)

from .dasar import ambil_int, ambil_teks, galat, halaman, sukses

bp = Blueprint("izin", __name__, url_prefix="/ketidakhadiran")

JUDUL = {"S": "Sakit", "I": "Izin"}


def _jenis(kunci):
    if kunci not in JUDUL:
        abort(404)
    return kunci


def _tanggal(teks):
    try:
        return datetime.strptime(teks, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@bp.route("/<kunci>")
def daftar(kunci):
    jenis = _jenis(kunci)
    kata = (request.args.get("cari") or "").strip()
    q = Ketidakhadiran.query.filter_by(jenis=jenis).join(Mahasiswa)
    if kata:
        pola = f"%{kata}%"
        q = q.filter((Mahasiswa.nama.ilike(pola)) | (Mahasiswa.nim.ilike(pola)))
    baris = q.order_by(Ketidakhadiran.tanggal.desc()).all()
    return halaman(
        f"ketidakhadiran-{jenis}",
        "izin/daftar.html",
        baris=baris,
        jenis=jenis,
        judul=JUDUL[jenis],
        kata=kata,
        mahasiswa=Mahasiswa.query.order_by(Mahasiswa.nim).all(),
    )


@bp.post("/<kunci>/tambah")
def tambah(kunci):
    jenis = _jenis(kunci)
    mahasiswa_id = ambil_int(request.form.get("mahasiswa_id"))
    tanggal = _tanggal(request.form.get("tanggal"))
    if not mahasiswa_id or tanggal is None:
        galat("Mahasiswa dan tanggal wajib diisi.")
        return redirect(url_for("izin.daftar", kunci=jenis))

    db.session.add(
        Ketidakhadiran(
            mahasiswa_id=mahasiswa_id,
            jenis=jenis,
            tanggal=tanggal,
            jadwal_jam_id=ambil_int(request.form.get("jadwal_jam_id")),
            keterangan=ambil_teks(request.form, "keterangan"),
        )
    )
    db.session.commit()
    sukses(f"Catatan {JUDUL[jenis].lower()} ditambahkan.")
    return redirect(url_for("izin.daftar", kunci=jenis))


@bp.post("/<int:id_baris>/hapus")
def hapus(id_baris):
    baris = db.session.get(Ketidakhadiran, id_baris) or abort(404)
    jenis = baris.jenis
    db.session.delete(baris)
    db.session.commit()
    sukses("Catatan dihapus.")
    return redirect(url_for("izin.daftar", kunci=jenis))


@bp.route("/sesi-pada-tanggal")
def sesi_pada_tanggal():
    """Dipakai formulir untuk menawarkan sesi yang ada pada tanggal terpilih."""
    from flask import jsonify

    tanggal = _tanggal(request.args.get("tanggal"))
    mahasiswa_id = ambil_int(request.args.get("mahasiswa_id"))
    if tanggal is None:
        return jsonify(sesi=[])

    q = (
        db.session.query(JadwalJam, JadwalHari)
        .join(JadwalHari, JadwalJam.jadwal_hari_id == JadwalHari.id)
        .filter(JadwalHari.tanggal == tanggal)
    )
    if mahasiswa_id:
        from core.models import JadwalMahasiswa

        q = q.join(
            JadwalKelas, JadwalHari.jadwal_kelas_id == JadwalKelas.id
        ).join(
            JadwalMahasiswa, JadwalMahasiswa.jadwal_kelas_id == JadwalKelas.id
        ).filter(JadwalMahasiswa.mahasiswa_id == mahasiswa_id)

    hasil = [
        {"id": s.id, "label": f"{s.kegiatan} ({s.jam_masuk.strftime('%H.%M')})"}
        for s, _ in q.order_by(JadwalJam.jam_masuk).all()
    ]
    return jsonify(sesi=hasil)


def daftarkan(app):
    app.register_blueprint(bp)

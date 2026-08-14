"""Jadwal kuliah: blok -> kelas -> tanggal -> sesi, beserta pendaftaran peserta.

Sesi (jadwal_jam) dibuat manual oleh admin dan bisa diubah kapan saja.
"""

from datetime import datetime, timedelta

from flask import Blueprint, abort, redirect, request, url_for

from core.laporan import label_tanggal
from core.models import (
    Departemen,
    Dosen,
    Jadwal,
    JadwalDosen,
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    JadwalMahasiswa,
    Kelas,
    Mahasiswa,
    MataKuliah,
    Pengaturan,
    Ruangan,
    db,
)

from .dasar import ambil_int, ambil_teks, galat, halaman, sukses

bp = Blueprint("jadwal", __name__, url_prefix="/jadwal")


def _tanggal(teks):
    try:
        return datetime.strptime(teks, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _jam(teks):
    for pola in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(teks, pola).time()
        except (TypeError, ValueError):
            continue
    return None


@bp.route("/")
def daftar():
    baris = Jadwal.query.order_by(Jadwal.id.desc()).all()
    return halaman("jadwal", "jadwal/daftar.html", baris=baris)


@bp.route("/tambah", methods=["GET", "POST"])
@bp.route("/<int:id_jadwal>/ubah", methods=["GET", "POST"])
def sunting(id_jadwal=None):
    obj = db.session.get(Jadwal, id_jadwal) if id_jadwal else Jadwal()
    if id_jadwal and obj is None:
        abort(404)
    if request.method == "POST":
        obj.mata_kuliah_id = ambil_int(request.form.get("mata_kuliah_id"))
        obj.semester = ambil_teks(request.form, "semester")
        obj.tahun_ajaran = ambil_teks(request.form, "tahun_ajaran")
        if not obj.mata_kuliah_id:
            galat("Mata kuliah wajib dipilih.")
        else:
            if not id_jadwal:
                db.session.add(obj)
            db.session.commit()
            sukses("Jadwal blok tersimpan.")
            return redirect(url_for("jadwal.rinci", id_jadwal=obj.id))
    return halaman(
        "jadwal",
        "jadwal/formulir.html",
        obj=obj,
        mata_kuliah=MataKuliah.query.order_by(MataKuliah.nama).all(),
    )


@bp.post("/<int:id_jadwal>/hapus")
def hapus(id_jadwal):
    obj = db.session.get(Jadwal, id_jadwal) or abort(404)
    db.session.delete(obj)
    db.session.commit()
    sukses("Jadwal blok dihapus.")
    return redirect(url_for("jadwal.daftar"))


@bp.route("/<int:id_jadwal>")
def rinci(id_jadwal):
    obj = db.session.get(Jadwal, id_jadwal) or abort(404)
    terpakai = {jk.kelas_id for jk in obj.kelas_jadwal}
    tersedia = [k for k in Kelas.query.order_by(Kelas.nama).all() if k.id not in terpakai]
    return halaman("jadwal", "jadwal/rinci.html", obj=obj, kelas_tersedia=tersedia)


@bp.post("/<int:id_jadwal>/kelas")
def tambah_kelas(id_jadwal):
    obj = db.session.get(Jadwal, id_jadwal) or abort(404)
    kelas_id = ambil_int(request.form.get("kelas_id"))
    if not kelas_id:
        galat("Pilih kelas terlebih dahulu.")
        return redirect(url_for("jadwal.rinci", id_jadwal=obj.id))

    jk = JadwalKelas(jadwal_id=obj.id, kelas_id=kelas_id)
    db.session.add(jk)
    db.session.flush()

    # daftarkan seluruh mahasiswa kelas itu sebagai peserta
    for mhs in Mahasiswa.query.filter_by(kelas_id=kelas_id).all():
        db.session.add(JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=mhs.id))
    db.session.commit()
    sukses("Kelas ditambahkan beserta seluruh mahasiswanya.")
    return redirect(url_for("jadwal.kelas", id_jk=jk.id))


@bp.post("/kelas/<int:id_jk>/hapus")
def hapus_kelas(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or abort(404)
    id_jadwal = jk.jadwal_id
    db.session.delete(jk)
    db.session.commit()
    sukses("Kelas dikeluarkan dari blok ini.")
    return redirect(url_for("jadwal.rinci", id_jadwal=id_jadwal))


@bp.route("/kelas/<int:id_jk>")
def kelas(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or abort(404)
    pengaturan = Pengaturan.ambil()
    hari = (
        JadwalHari.query.filter_by(jadwal_kelas_id=id_jk)
        .order_by(JadwalHari.tanggal)
        .all()
    )
    terdaftar = {p.mahasiswa_id for p in jk.peserta}
    belum = (
        Mahasiswa.query.filter(Mahasiswa.id.notin_(terdaftar or [0]))
        .order_by(Mahasiswa.nim)
        .all()
        if terdaftar
        else Mahasiswa.query.order_by(Mahasiswa.nim).all()
    )
    return halaman(
        "jadwal",
        "jadwal/kelas.html",
        jk=jk,
        hari=hari,
        pengaturan=pengaturan,
        label_tanggal=label_tanggal,
        ruangan=Ruangan.query.order_by(Ruangan.nama).all(),
        departemen=Departemen.query.order_by(Departemen.nama).all(),
        dosen=Dosen.query.order_by(Dosen.nama).all(),
        belum_terdaftar=belum,
    )


@bp.post("/kelas/<int:id_jk>/hari")
def tambah_hari(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or abort(404)
    awal = _tanggal(request.form.get("tanggal"))
    akhir = _tanggal(request.form.get("tanggal_akhir")) or awal
    if awal is None:
        galat("Tanggal tidak valid.")
        return redirect(url_for("jadwal.kelas", id_jk=jk.id))
    if akhir < awal:
        awal, akhir = akhir, awal

    ada = {h.tanggal for h in JadwalHari.query.filter_by(jadwal_kelas_id=jk.id).all()}
    jumlah = 0
    tanggal = awal
    while tanggal <= akhir and jumlah < 200:
        if tanggal not in ada:
            db.session.add(JadwalHari(jadwal_kelas_id=jk.id, tanggal=tanggal))
            jumlah += 1
        tanggal += timedelta(days=1)
    db.session.commit()
    sukses(f"{jumlah} tanggal ditambahkan." if jumlah else "Tanggal itu sudah ada.")
    return redirect(url_for("jadwal.kelas", id_jk=jk.id))


@bp.post("/hari/<int:id_hari>/hapus")
def hapus_hari(id_hari):
    hari = db.session.get(JadwalHari, id_hari) or abort(404)
    id_jk = hari.jadwal_kelas_id
    db.session.delete(hari)
    db.session.commit()
    sukses("Tanggal beserta sesinya dihapus.")
    return redirect(url_for("jadwal.kelas", id_jk=id_jk))


def _terapkan_sesi(sesi, form):
    sesi.kegiatan = ambil_teks(form, "kegiatan")
    sesi.jam_masuk = _jam(ambil_teks(form, "jam_masuk"))
    sesi.jml_jam = ambil_int(form.get("jml_jam"), 2) or 2
    sesi.jam_selesai_manual = _jam(ambil_teks(form, "jam_selesai_manual"))
    sesi.ruangan_id = ambil_int(form.get("ruangan_id"))
    sesi.departemen_id = ambil_int(form.get("departemen_id"))
    if not sesi.kegiatan:
        return "Nama kegiatan wajib diisi."
    if sesi.jam_masuk is None:
        return "Jam masuk tidak valid."
    return None


@bp.post("/hari/<int:id_hari>/sesi")
def tambah_sesi(id_hari):
    hari = db.session.get(JadwalHari, id_hari) or abort(404)
    sesi = JadwalJam(jadwal_hari_id=hari.id)
    pesan = _terapkan_sesi(sesi, request.form)
    if pesan:
        galat(pesan)
    else:
        db.session.add(sesi)
        db.session.flush()
        for id_dosen in request.form.getlist("dosen_id"):
            if id_dosen:
                db.session.add(JadwalDosen(jadwal_jam_id=sesi.id, dosen_id=int(id_dosen)))
        db.session.commit()
        sukses("Sesi ditambahkan.")
    return redirect(url_for("jadwal.kelas", id_jk=hari.jadwal_kelas_id))


@bp.post("/sesi/<int:id_sesi>/ubah")
def ubah_sesi(id_sesi):
    sesi = db.session.get(JadwalJam, id_sesi) or abort(404)
    pesan = _terapkan_sesi(sesi, request.form)
    if pesan:
        galat(pesan)
    else:
        JadwalDosen.query.filter_by(jadwal_jam_id=sesi.id).delete()
        for id_dosen in request.form.getlist("dosen_id"):
            if id_dosen:
                db.session.add(JadwalDosen(jadwal_jam_id=sesi.id, dosen_id=int(id_dosen)))
        db.session.commit()
        sukses("Sesi diperbarui.")
    return redirect(url_for("jadwal.kelas", id_jk=sesi.hari.jadwal_kelas_id))


@bp.post("/sesi/<int:id_sesi>/hapus")
def hapus_sesi(id_sesi):
    sesi = db.session.get(JadwalJam, id_sesi) or abort(404)
    id_jk = sesi.hari.jadwal_kelas_id
    db.session.delete(sesi)
    db.session.commit()
    sukses("Sesi dihapus.")
    return redirect(url_for("jadwal.kelas", id_jk=id_jk))


@bp.post("/kelas/<int:id_jk>/peserta")
def tambah_peserta(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or abort(404)
    ditambah = 0
    for id_mhs in request.form.getlist("mahasiswa_id"):
        if not id_mhs:
            continue
        ada = JadwalMahasiswa.query.filter_by(
            jadwal_kelas_id=jk.id, mahasiswa_id=int(id_mhs)
        ).first()
        if ada is None:
            db.session.add(
                JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=int(id_mhs))
            )
            ditambah += 1
    db.session.commit()
    sukses(f"{ditambah} mahasiswa ditambahkan.")
    return redirect(url_for("jadwal.kelas", id_jk=jk.id))


@bp.post("/peserta/<int:id_peserta>/hapus")
def hapus_peserta(id_peserta):
    p = db.session.get(JadwalMahasiswa, id_peserta) or abort(404)
    id_jk = p.jadwal_kelas_id
    db.session.delete(p)
    db.session.commit()
    sukses("Peserta dikeluarkan.")
    return redirect(url_for("jadwal.kelas", id_jk=id_jk))


def daftarkan(app):
    app.register_blueprint(bp)

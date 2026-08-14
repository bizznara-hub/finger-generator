"""Data master: departemen, kelas, mahasiswa, dosen, ruangan, mata kuliah, mesin.

Ketujuhnya berbentuk sama - daftar, tambah, ubah, hapus - jadi semuanya dijalankan
oleh satu mesin CRUD yang digerakkan spesifikasi, bukan tujuh salinan kode.
"""

from flask import Blueprint, abort, redirect, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from core.models import (
    Departemen,
    Dosen,
    Kelas,
    Mahasiswa,
    MataKuliah,
    Mesin,
    Ruangan,
    db,
)

from .dasar import ambil_teks, galat, halaman, sukses

bp = Blueprint("master", __name__, url_prefix="/master")


class Bidang:
    def __init__(self, nama, label, tipe="text", wajib=False, pilihan=None, bantuan=None):
        self.nama = nama
        self.label = label
        self.tipe = tipe  # text | number | select | tel
        self.wajib = wajib
        self.pilihan = pilihan  # fungsi -> [(nilai, label), ...]
        self.bantuan = bantuan

    def daftar_pilihan(self):
        return self.pilihan() if self.pilihan else []


class Spek:
    def __init__(self, kunci, judul, model, kolom, bidang, urut=None, cari=None):
        self.kunci = kunci
        self.judul = judul
        self.model = model
        self.kolom = kolom  # [(label, fungsi(baris) -> teks)]
        self.bidang = bidang
        self.urut = urut
        self.cari = cari or []  # kolom yang ikut dicari

    def query(self, kata=""):
        q = self.model.query
        if kata and self.cari:
            pola = f"%{kata}%"
            q = q.filter(or_(*[k.ilike(pola) for k in self.cari]))
        if self.urut is not None:
            q = q.order_by(self.urut)
        return q


def _pilihan(model, label=lambda x: x.nama, urut=None):
    def ambil():
        q = model.query.order_by(urut if urut is not None else model.id)
        return [(str(x.id), label(x)) for x in q]

    return ambil


SPEK = {}


def _daftar_spek():
    SPEK["departemen"] = Spek(
        "departemen",
        "Departemen",
        Departemen,
        [("Kode", lambda x: x.kode or "-"), ("Nama", lambda x: x.nama)],
        [
            Bidang("kode", "Kode"),
            Bidang("nama", "Nama departemen", wajib=True),
        ],
        urut=Departemen.nama,
        cari=[Departemen.nama, Departemen.kode],
    )

    SPEK["kelas"] = Spek(
        "kelas",
        "Kelas",
        Kelas,
        [
            ("Nama", lambda x: x.nama),
            ("Angkatan", lambda x: x.angkatan or "-"),
            ("Departemen", lambda x: x.departemen.nama if x.departemen else "-"),
            ("Jumlah mahasiswa", lambda x: Mahasiswa.query.filter_by(kelas_id=x.id).count()),
        ],
        [
            Bidang("nama", "Nama kelas", wajib=True, bantuan="Contoh: A"),
            Bidang("angkatan", "Angkatan", bantuan="Contoh: 2024"),
            Bidang(
                "departemen_id",
                "Departemen",
                tipe="select",
                pilihan=_pilihan(Departemen, urut=Departemen.nama),
            ),
        ],
        urut=Kelas.nama,
        cari=[Kelas.nama, Kelas.angkatan],
    )

    SPEK["mahasiswa"] = Spek(
        "mahasiswa",
        "Mahasiswa",
        Mahasiswa,
        [
            ("NIM", lambda x: x.nim),
            ("Nama", lambda x: x.nama),
            ("Kelas", lambda x: x.kelas.label if x.kelas else "-"),
            ("ID Finger", lambda x: x.id_finger or "belum diisi"),
        ],
        [
            Bidang("nim", "NIM", wajib=True),
            Bidang("nama", "Nama lengkap", wajib=True),
            Bidang(
                "kelas_id",
                "Kelas",
                tipe="select",
                pilihan=_pilihan(Kelas, label=lambda x: x.label, urut=Kelas.nama),
            ),
            Bidang(
                "id_finger",
                "ID Finger",
                bantuan="User ID pada mesin fingerprint. Kosong = selalu dihitung Alpa.",
            ),
            Bidang("hp", "No. HP", tipe="tel"),
        ],
        urut=Mahasiswa.nim,
        cari=[Mahasiswa.nim, Mahasiswa.nama, Mahasiswa.id_finger],
    )

    SPEK["dosen"] = Spek(
        "dosen",
        "Dosen",
        Dosen,
        [
            ("NIP", lambda x: x.nip or "-"),
            ("Nama", lambda x: x.nama),
            ("Departemen", lambda x: x.departemen.nama if x.departemen else "-"),
            ("ID Finger", lambda x: x.id_finger or "belum diisi"),
        ],
        [
            Bidang("nip", "NIP"),
            Bidang("nama", "Nama lengkap", wajib=True),
            Bidang(
                "departemen_id",
                "Departemen",
                tipe="select",
                pilihan=_pilihan(Departemen, urut=Departemen.nama),
            ),
            Bidang("id_finger", "ID Finger", bantuan="User ID pada mesin fingerprint."),
            Bidang("hp", "No. HP", tipe="tel"),
        ],
        urut=Dosen.nama,
        cari=[Dosen.nama, Dosen.nip, Dosen.id_finger],
    )

    SPEK["ruangan"] = Spek(
        "ruangan",
        "Ruang Kuliah",
        Ruangan,
        [
            ("Kode", lambda x: x.kode or "-"),
            ("Nama", lambda x: x.nama),
            ("Kapasitas", lambda x: x.kapasitas or "-"),
        ],
        [
            Bidang("kode", "Kode ruangan"),
            Bidang("nama", "Nama ruangan", wajib=True),
            Bidang("kapasitas", "Kapasitas", tipe="number"),
        ],
        urut=Ruangan.nama,
        cari=[Ruangan.nama, Ruangan.kode],
    )

    SPEK["mata-kuliah"] = Spek(
        "mata-kuliah",
        "Mata Kuliah",
        MataKuliah,
        [
            ("Kode", lambda x: x.kode or "-"),
            ("Nama blok", lambda x: x.nama),
            ("SKS", lambda x: x.sks or "-"),
            ("Departemen", lambda x: x.departemen.nama if x.departemen else "-"),
        ],
        [
            Bidang("kode", "Kode"),
            Bidang("nama", "Nama mata kuliah / blok", wajib=True, bantuan="Contoh: NEUROLOGI"),
            Bidang("sks", "SKS", tipe="number"),
            Bidang(
                "departemen_id",
                "Departemen",
                tipe="select",
                pilihan=_pilihan(Departemen, urut=Departemen.nama),
            ),
        ],
        urut=MataKuliah.nama,
        cari=[MataKuliah.nama, MataKuliah.kode],
    )

    SPEK["mesin"] = Spek(
        "mesin",
        "Mesin Finger Print",
        Mesin,
        [
            ("Serial", lambda x: x.serial),
            ("Nama", lambda x: x.nama or "-"),
            ("Ruangan", lambda x: x.ruangan.nama if x.ruangan else "belum dipetakan"),
            ("IP", lambda x: x.ip_address or "-"),
        ],
        [
            Bidang(
                "serial",
                "Serial number",
                wajib=True,
                bantuan="Harus sama dengan kolom sn pada att_log.",
            ),
            Bidang("nama", "Nama mesin"),
            Bidang(
                "ruangan_id",
                "Ruangan",
                tipe="select",
                pilihan=_pilihan(Ruangan, urut=Ruangan.nama),
            ),
            Bidang("ip_address", "IP address"),
            Bidang("port", "Port"),
        ],
        urut=Mesin.serial,
        cari=[Mesin.serial, Mesin.nama],
    )


_daftar_spek()


def _spek(kunci):
    spek = SPEK.get(kunci)
    if spek is None:
        abort(404)
    return spek


def _isi_dari_form(spek, obj, form):
    kosong = []
    for bidang in spek.bidang:
        nilai = ambil_teks(form, bidang.nama)
        if bidang.wajib and not nilai:
            kosong.append(bidang.label)
        if bidang.tipe in ("number", "select"):
            setattr(obj, bidang.nama, int(nilai) if nilai else None)
        else:
            setattr(obj, bidang.nama, nilai or None)
    return kosong


@bp.route("/<kunci>")
def daftar(kunci):
    spek = _spek(kunci)
    kata = request.args.get("cari", "").strip()
    baris = spek.query(kata).all()
    return halaman(
        kunci, "master/daftar.html", spek=spek, baris=baris, kata=kata, judul=spek.judul
    )


@bp.route("/<kunci>/tambah", methods=["GET", "POST"])
def tambah(kunci):
    spek = _spek(kunci)
    obj = spek.model()
    if request.method == "POST":
        kosong = _isi_dari_form(spek, obj, request.form)
        if kosong:
            galat("Wajib diisi: " + ", ".join(kosong))
        else:
            try:
                db.session.add(obj)
                db.session.commit()
                sukses(f"{spek.judul} berhasil ditambahkan.")
                return redirect(url_for("master.daftar", kunci=kunci))
            except IntegrityError:
                db.session.rollback()
                galat("Data serupa sudah ada. Periksa kolom yang harus unik.")
    return halaman(
        kunci,
        "master/formulir.html",
        spek=spek,
        obj=obj,
        judul=f"Tambah {spek.judul}",
    )


@bp.route("/<kunci>/<int:id_baris>/ubah", methods=["GET", "POST"])
def ubah(kunci, id_baris):
    spek = _spek(kunci)
    obj = db.session.get(spek.model, id_baris) or abort(404)
    if request.method == "POST":
        kosong = _isi_dari_form(spek, obj, request.form)
        if kosong:
            galat("Wajib diisi: " + ", ".join(kosong))
        else:
            try:
                db.session.commit()
                sukses(f"{spek.judul} berhasil diperbarui.")
                return redirect(url_for("master.daftar", kunci=kunci))
            except IntegrityError:
                db.session.rollback()
                galat("Data serupa sudah ada. Periksa kolom yang harus unik.")
    return halaman(
        kunci,
        "master/formulir.html",
        spek=spek,
        obj=obj,
        judul=f"Ubah {spek.judul}",
    )


@bp.post("/<kunci>/<int:id_baris>/hapus")
def hapus(kunci, id_baris):
    spek = _spek(kunci)
    obj = db.session.get(spek.model, id_baris) or abort(404)
    try:
        db.session.delete(obj)
        db.session.commit()
        sukses(f"{spek.judul} berhasil dihapus.")
    except IntegrityError:
        db.session.rollback()
        galat("Tidak bisa dihapus karena masih dipakai data lain.")
    return redirect(url_for("master.daftar", kunci=kunci))


def daftarkan(app):
    app.register_blueprint(bp)

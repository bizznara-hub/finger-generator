"""CRUD data master lewat satu mesin generik, sama seperti versi Jinja."""

import re

from flask import jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from core.models import (
    Departemen,
    Dosen,
    Kelas,
    Mahasiswa,
    MataKuliah,
    Mesin,
    ProfilJam,
    Ruangan,
    db,
)

from . import GalatAPI, bp

# Gelar depan tidak ikut menentukan urutan: tanpa ini seluruh "Dr. dr." dan
# "Prof." menumpuk di atas hanya karena huruf besar diurutkan lebih dulu.
# Gelar terpanjang diuji lebih dulu, jika tidak "dr" akan termakan dari "drg."
# dan menyisakan "g." sebagai kunci urut. Lookahead menjaga nama asli yang
# kebetulan diawali huruf serupa, misalnya "Drajat", agar tidak ikut terpotong.
GELAR_DEPAN = re.compile(r"^(?:(?:prof|drg|drs|dr|apt|ns)(?:\.|(?![a-z]))\s*|\s+)+", re.I)


def urut_nama_orang(nama):
    return GELAR_DEPAN.sub("", nama or "").lower()

# kunci -> (model, judul, kolom yang boleh diisi, kolom pencarian, urutan)
# Seluruh daftar diurutkan berdasarkan NAMA. Catatan: urutan di laporan resmi
# tetap berdasarkan NIM (lihat core/laporan.py) karena begitulah bentuk baku
# daftar hadir; urutan di sini hanya untuk kemudahan mencari di layar.
SPEK = {
    "departemen": (Departemen, "Departemen", ["kode", "nama"],
                   [Departemen.nama, Departemen.kode], Departemen.nama),
    "kelas": (Kelas, "Kelas", ["nama", "angkatan", "departemen_id"],
              [Kelas.nama, Kelas.angkatan], Kelas.nama),
    "dosen": (Dosen, "Dosen", ["nip", "nama"],
              [Dosen.nama, Dosen.nip], Dosen.nama),
    "mahasiswa": (Mahasiswa, "Mahasiswa", ["nim", "nama", "id_finger"],
                  [Mahasiswa.nim, Mahasiswa.nama, Mahasiswa.id_finger], Mahasiswa.nama),
    "mata-kuliah": (MataKuliah, "Mata Kuliah", ["kode", "nama", "sks", "departemen_id"],
                    [MataKuliah.nama, MataKuliah.kode], MataKuliah.nama),
    "ruangan": (Ruangan, "Ruang Kuliah", ["kode", "nama", "kapasitas"],
                [Ruangan.nama, Ruangan.kode], Ruangan.nama),
    "mesin": (Mesin, "Mesin", ["serial", "nama", "ruangan_id", "ip_address", "port"],
              [Mesin.serial, Mesin.nama], Mesin.nama),
}

ANGKA = {"departemen_id", "kelas_id", "ruangan_id", "sks", "kapasitas"}


def _spek(kunci):
    if kunci not in SPEK:
        raise GalatAPI(f"Jenis data '{kunci}' tidak dikenal.", 404)
    return SPEK[kunci]


def _serialisasi(kunci, obj):
    model, _, bidang, _, _ = _spek(kunci)
    d = {"id": obj.id}
    for b in bidang:
        d[b] = getattr(obj, b)
    if kunci == "mahasiswa":
        d["kelas"] = obj.kelas.label if obj.kelas else None
    if kunci in ("kelas", "mata-kuliah"):
        d["departemen"] = obj.departemen.nama if obj.departemen else None
    if kunci == "kelas":
        d["jumlah_mahasiswa"] = Mahasiswa.query.filter_by(kelas_id=obj.id).count()
        d["label"] = obj.label
    if kunci == "mesin":
        d["ruangan"] = obj.ruangan.nama if obj.ruangan else None
    return d


@bp.get("/master/<kunci>")
def daftar(kunci):
    model, judul, _, cari, urut = _spek(kunci)
    kata = (request.args.get("cari") or "").strip()
    q = model.query
    if kata and cari:
        pola = f"%{kata}%"
        q = q.filter(or_(*[k.ilike(pola) for k in cari]))
    baris = q.order_by(urut).all()
    if kunci in ("dosen", "mahasiswa"):
        baris.sort(key=lambda b: urut_nama_orang(b.nama))
    return jsonify(judul=judul, baris=[_serialisasi(kunci, b) for b in baris])


def _samakan_finger_dengan_nim(kunci, obj):
    """ID Finger mahasiswa mengikuti NIM. Mesin didaftarkan dengan NIM sebagai
    User ID, jadi keduanya memang satu nilai. Tetap bisa ditimpa manual bila
    ada mesin yang memakai nomor lain."""
    if kunci == "mahasiswa" and not (obj.id_finger or "").strip():
        obj.id_finger = obj.nim


def _terapkan(kunci, obj, data):
    _, _, bidang, _, _ = _spek(kunci)
    for b in bidang:
        if b not in data:
            continue
        nilai = data[b]
        if isinstance(nilai, str):
            nilai = nilai.strip()
        if b in ANGKA:
            obj_nilai = int(nilai) if str(nilai or "").strip() else None
        else:
            obj_nilai = nilai or None
        setattr(obj, b, obj_nilai)


@bp.post("/master/<kunci>")
def tambah(kunci):
    model, judul, _, _, _ = _spek(kunci)
    obj = model()
    _terapkan(kunci, obj, request.get_json(silent=True) or {})
    _samakan_finger_dengan_nim(kunci, obj)
    try:
        db.session.add(obj)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise GalatAPI("Data serupa sudah ada. Periksa kolom yang harus unik.")
    return jsonify(baris=_serialisasi(kunci, obj), pesan=f"{judul} ditambahkan.")


@bp.put("/master/<kunci>/<int:id_baris>")
def ubah(kunci, id_baris):
    model, judul, _, _, _ = _spek(kunci)
    obj = db.session.get(model, id_baris)
    if obj is None:
        raise GalatAPI("Data tidak ditemukan.", 404)
    _terapkan(kunci, obj, request.get_json(silent=True) or {})
    _samakan_finger_dengan_nim(kunci, obj)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise GalatAPI("Data serupa sudah ada. Periksa kolom yang harus unik.")
    return jsonify(baris=_serialisasi(kunci, obj), pesan=f"{judul} diperbarui.")


@bp.delete("/master/<kunci>/<int:id_baris>")
def hapus(kunci, id_baris):
    model, judul, _, _, _ = _spek(kunci)
    obj = db.session.get(model, id_baris)
    if obj is None:
        raise GalatAPI("Data tidak ditemukan.", 404)
    try:
        db.session.delete(obj)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise GalatAPI("Tidak bisa dihapus karena masih dipakai data lain.")
    return jsonify(pesan=f"{judul} dihapus.")


@bp.get("/pilihan")
def pilihan():
    """Daftar untuk mengisi select di formulir."""
    return jsonify(
        departemen=[{"id": x.id, "label": x.nama} for x in Departemen.query.order_by(Departemen.nama)],
        kelas=[{"id": x.id, "label": x.label} for x in Kelas.query.order_by(Kelas.nama)],
        ruangan=[{"id": x.id, "label": x.nama} for x in Ruangan.query.order_by(Ruangan.nama)],
        dosen=[{"id": x.id, "label": x.nama} for x in Dosen.query.order_by(Dosen.nama)],
        mata_kuliah=[{"id": x.id, "label": x.nama} for x in MataKuliah.query.order_by(MataKuliah.nama)],
        mahasiswa=[{"id": x.id, "label": f"{x.nim} — {x.nama}"} for x in Mahasiswa.query.order_by(Mahasiswa.nim)],
        profil_jam=[{"id": x.id, "label": x.label, "bawaan": x.bawaan}
                    for x in ProfilJam.query.order_by(ProfilJam.id)],
    )

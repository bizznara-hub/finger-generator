"""API jadwal: blok -> kelas -> tanggal -> sesi, dan peserta."""

from datetime import datetime, timedelta

from flask import jsonify, request

from core.laporan import label_tanggal
from core.models import (
    Jadwal,
    JadwalDosen,
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    JadwalMahasiswa,
    Mahasiswa,
    Pengaturan,
    db,
)

from . import GalatAPI, bp


def _tanggal(t):
    try:
        return datetime.strptime(t, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _jam(t):
    for pola in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(str(t).strip(), pola).time()
        except (TypeError, ValueError):
            continue
    return None


def _blok(j):
    return {
        "id": j.id,
        "mata_kuliah_id": j.mata_kuliah_id,
        "mata_kuliah": j.mata_kuliah.nama if j.mata_kuliah else None,
        "semester": j.semester,
        "tahun_ajaran": j.tahun_ajaran,
        "kelas": [
            {
                "id": jk.id,
                "kelas_id": jk.kelas_id,
                "nama": jk.kelas.nama if jk.kelas else "?",
                "label": jk.kelas.label if jk.kelas else "?",
                "jumlah_peserta": len(jk.peserta),
                "jumlah_hari": len(jk.hari),
            }
            for jk in j.kelas_jadwal
        ],
    }


@bp.get("/jadwal")
def daftar_blok():
    return jsonify(baris=[_blok(j) for j in Jadwal.query.order_by(Jadwal.id.desc())])


@bp.post("/jadwal")
def tambah_blok():
    d = request.get_json(silent=True) or {}
    if not d.get("mata_kuliah_id"):
        raise GalatAPI("Mata kuliah wajib dipilih.")
    j = Jadwal(
        mata_kuliah_id=int(d["mata_kuliah_id"]),
        semester=(d.get("semester") or "").strip() or None,
        tahun_ajaran=(d.get("tahun_ajaran") or "").strip() or None,
    )
    db.session.add(j)
    db.session.commit()
    return jsonify(baris=_blok(j), pesan="Blok tersimpan.")


@bp.put("/jadwal/<int:id_jadwal>")
def ubah_blok(id_jadwal):
    j = db.session.get(Jadwal, id_jadwal) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    if d.get("mata_kuliah_id"):
        j.mata_kuliah_id = int(d["mata_kuliah_id"])
    j.semester = (d.get("semester") or "").strip() or None
    j.tahun_ajaran = (d.get("tahun_ajaran") or "").strip() or None
    db.session.commit()
    return jsonify(baris=_blok(j), pesan="Blok diperbarui.")


@bp.delete("/jadwal/<int:id_jadwal>")
def hapus_blok(id_jadwal):
    j = db.session.get(Jadwal, id_jadwal) or _tidak_ada()
    db.session.delete(j)
    db.session.commit()
    return jsonify(pesan="Blok dihapus beserta seluruh tanggal dan sesinya.")


def _tidak_ada():
    raise GalatAPI("Data tidak ditemukan.", 404)


@bp.post("/jadwal/<int:id_jadwal>/kelas")
def tambah_kelas(id_jadwal):
    j = db.session.get(Jadwal, id_jadwal) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    kelas_id = d.get("kelas_id")
    if not kelas_id:
        raise GalatAPI("Pilih kelas terlebih dahulu.")
    if JadwalKelas.query.filter_by(jadwal_id=j.id, kelas_id=int(kelas_id)).first():
        raise GalatAPI("Kelas itu sudah ada pada blok ini.")

    jk = JadwalKelas(jadwal_id=j.id, kelas_id=int(kelas_id))
    db.session.add(jk)
    db.session.flush()
    for m in Mahasiswa.query.filter_by(kelas_id=int(kelas_id)).all():
        db.session.add(JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=m.id))
    db.session.commit()
    return jsonify(id=jk.id, pesan="Kelas ditambahkan beserta seluruh mahasiswanya.")


@bp.delete("/jadwal/kelas/<int:id_jk>")
def hapus_kelas(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or _tidak_ada()
    db.session.delete(jk)
    db.session.commit()
    return jsonify(pesan="Kelas dikeluarkan dari blok.")


def _sesi(s, p):
    return {
        "id": s.id,
        "kegiatan": s.kegiatan,
        "jam_masuk": s.jam_masuk.strftime("%H:%M"),
        "jml_jam": s.jml_jam,
        "jam_selesai_manual": s.jam_selesai_manual.strftime("%H:%M") if s.jam_selesai_manual else "",
        "jam_selesai_hitung": s.jam_selesai(p).strftime("%H:%M"),
        "ruangan_id": s.ruangan_id,
        "dosen_id": [x.dosen_id for x in s.pengajar],
    }


@bp.get("/jadwal/kelas/<int:id_jk>")
def rinci_kelas(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or _tidak_ada()
    p = Pengaturan.ambil()
    hari = JadwalHari.query.filter_by(jadwal_kelas_id=id_jk).order_by(JadwalHari.tanggal).all()
    terdaftar = {x.mahasiswa_id for x in jk.peserta}
    return jsonify(
        blok=jk.jadwal.mata_kuliah.nama if jk.jadwal.mata_kuliah else "Blok",
        jadwal_id=jk.jadwal_id,
        kelas=jk.kelas.nama if jk.kelas else "?",
        pengaturan={
            "menit_perjam": p.menit_perjam,
            "menit_pergantian": p.menit_pergantian,
            "toleransi_awal": p.toleransi_awal,
            "toleransi_akhir": p.toleransi_akhir,
        },
        hari=[
            {
                "id": h.id,
                "tanggal": h.tanggal.strftime("%Y-%m-%d"),
                "label": label_tanggal(h.tanggal),
                "sesi": [_sesi(s, p) for s in sorted(h.sesi, key=lambda x: x.jam_masuk)],
            }
            for h in hari
        ],
        peserta=[
            {
                "id": x.id,
                "nim": x.mahasiswa.nim,
                "nama": x.mahasiswa.nama,
                "id_finger": x.mahasiswa.id_finger,
            }
            for x in sorted(jk.peserta, key=lambda x: x.mahasiswa.nim)
        ],
        belum_terdaftar=[
            {"id": m.id, "label": f"{m.nim} — {m.nama}"}
            for m in Mahasiswa.query.order_by(Mahasiswa.nim).all()
            if m.id not in terdaftar
        ],
    )


@bp.post("/jadwal/kelas/<int:id_jk>/hari")
def tambah_hari(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    awal = _tanggal(d.get("tanggal"))
    akhir = _tanggal(d.get("tanggal_akhir")) or awal
    if awal is None:
        raise GalatAPI("Tanggal tidak valid.")
    if akhir < awal:
        awal, akhir = akhir, awal

    ada = {h.tanggal for h in JadwalHari.query.filter_by(jadwal_kelas_id=jk.id).all()}
    jumlah, t = 0, awal
    while t <= akhir and jumlah < 200:
        if t not in ada:
            db.session.add(JadwalHari(jadwal_kelas_id=jk.id, tanggal=t))
            jumlah += 1
        t += timedelta(days=1)
    db.session.commit()
    return jsonify(pesan=f"{jumlah} tanggal ditambahkan." if jumlah else "Tanggal itu sudah ada.")


@bp.delete("/jadwal/hari/<int:id_hari>")
def hapus_hari(id_hari):
    h = db.session.get(JadwalHari, id_hari) or _tidak_ada()
    db.session.delete(h)
    db.session.commit()
    return jsonify(pesan="Tanggal dihapus beserta sesinya.")


def _terapkan_sesi(s, d):
    s.kegiatan = (d.get("kegiatan") or "").strip()
    s.jam_masuk = _jam(d.get("jam_masuk"))
    s.jml_jam = int(d.get("jml_jam") or 2)
    s.jam_selesai_manual = _jam(d.get("jam_selesai_manual")) if d.get("jam_selesai_manual") else None
    s.ruangan_id = int(d["ruangan_id"]) if d.get("ruangan_id") else None
    if not s.kegiatan:
        raise GalatAPI("Nama kegiatan wajib diisi.")
    if s.jam_masuk is None:
        raise GalatAPI("Jam masuk tidak valid. Gunakan format 07:30.")


def _set_dosen(s, d):
    JadwalDosen.query.filter_by(jadwal_jam_id=s.id).delete()
    for i in d.get("dosen_id") or []:
        db.session.add(JadwalDosen(jadwal_jam_id=s.id, dosen_id=int(i)))


@bp.post("/jadwal/hari/<int:id_hari>/sesi")
def tambah_sesi(id_hari):
    h = db.session.get(JadwalHari, id_hari) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    s = JadwalJam(jadwal_hari_id=h.id)
    _terapkan_sesi(s, d)
    db.session.add(s)
    db.session.flush()
    _set_dosen(s, d)
    db.session.commit()
    return jsonify(pesan="Sesi ditambahkan.")


@bp.put("/jadwal/sesi/<int:id_sesi>")
def ubah_sesi(id_sesi):
    s = db.session.get(JadwalJam, id_sesi) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    _terapkan_sesi(s, d)
    _set_dosen(s, d)
    db.session.commit()
    return jsonify(pesan="Sesi diperbarui.")


@bp.delete("/jadwal/sesi/<int:id_sesi>")
def hapus_sesi(id_sesi):
    s = db.session.get(JadwalJam, id_sesi) or _tidak_ada()
    db.session.delete(s)
    db.session.commit()
    return jsonify(pesan="Sesi dihapus.")


@bp.post("/jadwal/kelas/<int:id_jk>/peserta")
def tambah_peserta(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or _tidak_ada()
    ditambah = 0
    for i in (request.get_json(silent=True) or {}).get("mahasiswa_id") or []:
        if not JadwalMahasiswa.query.filter_by(jadwal_kelas_id=jk.id, mahasiswa_id=int(i)).first():
            db.session.add(JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=int(i)))
            ditambah += 1
    db.session.commit()
    return jsonify(pesan=f"{ditambah} mahasiswa ditambahkan.")


@bp.delete("/jadwal/peserta/<int:id_peserta>")
def hapus_peserta(id_peserta):
    p = db.session.get(JadwalMahasiswa, id_peserta) or _tidak_ada()
    db.session.delete(p)
    db.session.commit()
    return jsonify(pesan="Peserta dikeluarkan.")

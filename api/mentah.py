"""Dua jalur data mentah, log scan, dan catatan sakit/izin."""

import io
from datetime import datetime, time

from flask import jsonify, request

from core import attlog, parser
from core.models import (
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    JadwalMahasiswa,
    Ketidakhadiran,
    LogScan,
    Mahasiswa,
    Mesin,
    Pengaturan,
    db,
)

from . import GalatAPI, bp


def _tanggal(t):
    try:
        return datetime.strptime(t, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@bp.get("/mentah/ringkasan")
def ringkasan():
    p = Pengaturan.ambil()
    terakhir = LogScan.query.order_by(LogScan.tanggal.desc(), LogScan.jam.desc()).first()
    per_sumber = db.session.query(LogScan.sumber, db.func.count(LogScan.id)).group_by(LogScan.sumber).all()
    return jsonify(
        jumlah=LogScan.query.count(),
        per_sumber=[{"sumber": s, "jumlah": n} for s, n in per_sumber],
        terakhir=terakhir.tanggal.strftime("%d/%m/%Y") if terakhir else None,
        attlog_siap=bool(p.attlog_host and p.attlog_nama_db),
        attlog_host=p.attlog_host,
        attlog_nama_db=p.attlog_nama_db,
        mesin=[
            {
                "id": m.id, "serial": m.serial, "nama": m.nama,
                "ruangan": m.ruangan.nama if m.ruangan else None,
                "ip_address": m.ip_address,
            }
            for m in Mesin.query.order_by(Mesin.serial)
        ],
    )


@bp.post("/mentah/impor")
def impor():
    berkas = request.files.getlist("berkas")
    if not berkas or all(f.filename == "" for f in berkas):
        raise GalatAPI("Belum ada berkas yang dipilih.")

    isi = []
    for f in berkas:
        if not (f.filename or "").lower().endswith((".xls", ".xlsx")):
            raise GalatAPI(f"Format berkas {f.filename} tidak didukung. Gunakan .xls atau .xlsx.")
        isi.append(io.BytesIO(f.read()))

    try:
        log, format_terpakai = parser.gabung_mentah(isi)
    except parser.FormatTidakDikenali as e:
        raise GalatAPI(str(e))
    except Exception as e:  # noqa: BLE001
        raise GalatAPI(f"Gagal membaca berkas: {e}")

    awal, akhir = log.tanggal.min().date(), log.tanggal.max().date()
    ada = {
        (s.id_finger, s.tanggal, s.jam, s.serial)
        for s in LogScan.query.filter(LogScan.tanggal >= awal, LogScan.tanggal <= akhir).all()
    }
    baru = dilewati = 0
    for r in log.itertuples(index=False):
        jam = time(int(r.jam[:2]), int(r.jam[3:5]))
        kunci = (str(r.uid), r.tanggal.date(), jam, None)
        if kunci in ada:
            dilewati += 1
            continue
        ada.add(kunci)
        db.session.add(LogScan(id_finger=str(r.uid), nama_mesin=r.nama,
                               tanggal=r.tanggal.date(), jam=jam, sumber="impor"))
        baru += 1
    db.session.commit()
    return jsonify(baru=baru, dilewati=dilewati, format=format_terpakai,
                   pesan=f"Impor selesai: {baru} scan baru, {dilewati} kembar dilewati.")


@bp.post("/mentah/tarik")
def tarik():
    d = request.get_json(silent=True) or {}
    awal, akhir = _tanggal(d.get("tanggal_awal")), _tanggal(d.get("tanggal_akhir"))
    if awal is None or akhir is None:
        raise GalatAPI("Isi rentang tanggal terlebih dahulu.")
    if akhir < awal:
        awal, akhir = akhir, awal
    try:
        baru, dilewati = attlog.tarik(Pengaturan.ambil(), awal, akhir)
    except attlog.GalatAttlog as e:
        raise GalatAPI(str(e))
    return jsonify(baru=baru, dilewati=dilewati,
                   pesan=f"Tarik att_log selesai: {baru} scan baru, {dilewati} kembar dilewati.")


@bp.post("/mentah/uji-koneksi")
def uji_koneksi():
    try:
        jumlah = attlog.uji_koneksi(Pengaturan.ambil())
    except attlog.GalatAttlog as e:
        raise GalatAPI(str(e))
    return jsonify(pesan=f"Koneksi berhasil. Tabel att_log berisi {jumlah:,} baris.".replace(",", "."))


@bp.get("/mentah/log")
def log():
    hal = max(1, int(request.args.get("hal", 1) or 1))
    kata = (request.args.get("cari") or "").strip()
    q = LogScan.query
    if kata:
        q = q.filter(LogScan.id_finger.ilike(f"%{kata}%"))
    q = q.order_by(LogScan.tanggal.desc(), LogScan.jam.desc())
    per_hal, total = 100, q.count()
    baris = q.limit(per_hal).offset((hal - 1) * per_hal).all()
    return jsonify(
        total=total, hal=hal, halaman_akhir=max(1, -(-total // per_hal)),
        baris=[
            {"id": s.id, "id_finger": s.id_finger, "nama_mesin": s.nama_mesin,
             "tanggal": s.tanggal.strftime("%d/%m/%Y"), "jam": s.jam.strftime("%H:%M"),
             "serial": s.serial, "sumber": s.sumber}
            for s in baris
        ],
    )


@bp.delete("/mentah/log")
def kosongkan():
    jumlah = LogScan.query.delete()
    db.session.commit()
    return jsonify(pesan=f"{jumlah} baris log scan dihapus.")


# ----------------------------------------------------------- sakit & izin

JUDUL = {"S": "Sakit", "I": "Izin"}


@bp.get("/ketidakhadiran/<jenis>")
def daftar_izin(jenis):
    if jenis not in JUDUL:
        raise GalatAPI("Jenis tidak dikenal.", 404)
    kata = (request.args.get("cari") or "").strip()
    q = Ketidakhadiran.query.filter_by(jenis=jenis).join(Mahasiswa)
    if kata:
        pola = f"%{kata}%"
        q = q.filter((Mahasiswa.nama.ilike(pola)) | (Mahasiswa.nim.ilike(pola)))
    baris = q.order_by(Ketidakhadiran.tanggal.desc()).all()
    return jsonify(
        judul=JUDUL[jenis],
        baris=[
            {"id": k.id, "nim": k.mahasiswa.nim, "nama": k.mahasiswa.nama,
             "tanggal": k.tanggal.strftime("%d/%m/%Y"),
             "sesi": k.sesi.kegiatan if k.sesi else "seluruh sesi",
             "keterangan": k.keterangan}
            for k in baris
        ],
    )


@bp.post("/ketidakhadiran/<jenis>")
def tambah_izin(jenis):
    if jenis not in JUDUL:
        raise GalatAPI("Jenis tidak dikenal.", 404)
    d = request.get_json(silent=True) or {}
    tanggal = _tanggal(d.get("tanggal"))
    if not d.get("mahasiswa_id") or tanggal is None:
        raise GalatAPI("Mahasiswa dan tanggal wajib diisi.")
    db.session.add(Ketidakhadiran(
        mahasiswa_id=int(d["mahasiswa_id"]), jenis=jenis, tanggal=tanggal,
        jadwal_jam_id=int(d["jadwal_jam_id"]) if d.get("jadwal_jam_id") else None,
        keterangan=(d.get("keterangan") or "").strip() or None,
    ))
    db.session.commit()
    return jsonify(pesan=f"Catatan {JUDUL[jenis].lower()} ditambahkan.")


@bp.delete("/ketidakhadiran/<int:id_baris>")
def hapus_izin(id_baris):
    k = db.session.get(Ketidakhadiran, id_baris)
    if k is None:
        raise GalatAPI("Catatan tidak ditemukan.", 404)
    db.session.delete(k)
    db.session.commit()
    return jsonify(pesan="Catatan dihapus.")


@bp.get("/ketidakhadiran/sesi")
def sesi_pada_tanggal():
    tanggal = _tanggal(request.args.get("tanggal"))
    mahasiswa_id = request.args.get("mahasiswa_id")
    if tanggal is None:
        return jsonify(sesi=[])
    q = (db.session.query(JadwalJam, JadwalHari)
         .join(JadwalHari, JadwalJam.jadwal_hari_id == JadwalHari.id)
         .filter(JadwalHari.tanggal == tanggal))
    if mahasiswa_id:
        q = (q.join(JadwalKelas, JadwalHari.jadwal_kelas_id == JadwalKelas.id)
              .join(JadwalMahasiswa, JadwalMahasiswa.jadwal_kelas_id == JadwalKelas.id)
              .filter(JadwalMahasiswa.mahasiswa_id == int(mahasiswa_id)))
    return jsonify(sesi=[
        {"id": s.id, "label": f"{s.kegiatan} ({s.jam_masuk.strftime('%H.%M')})"}
        for s, _ in q.order_by(JadwalJam.jam_masuk).all()
    ])

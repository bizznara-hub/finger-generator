"""API laporan: pratinjau JSON dan unduhan .xlsx."""

import re

from flask import jsonify, request, send_file

from core import laporan as mesin
from core import rekap
from core.models import Jadwal, JadwalKelas, Pengaturan, db

from . import GalatAPI, bp


def _nama_berkas(t):
    return (re.sub(r"[^A-Za-z0-9 _-]+", "", t).strip() or "Rekapan Absensi")[:120]


def _judul_meta(jk, p):
    j = jk.jadwal
    baris1 = " ".join(x for x in ["LAPORAN ABSEN MAHASISWA SEMESTER",
                                  (j.semester or "").upper(), j.tahun_ajaran or ""] if x)
    judul = [b for b in [baris1, p.nama_institusi or "", p.nama_universitas or ""] if b]
    meta = [
        f"Blok:  {j.mata_kuliah.nama if j.mata_kuliah else '-'}",
        f"Kelas: {jk.kelas.nama if jk.kelas else '-'}",
    ]
    return judul, meta


@bp.get("/laporan/pilihan")
def pilihan_laporan():
    baris = (db.session.query(JadwalKelas)
             .join(Jadwal, JadwalKelas.jadwal_id == Jadwal.id)
             .order_by(Jadwal.id.desc()).all())
    return jsonify(pilihan=[
        {
            "id": p.id,
            "label": (f"{p.jadwal.mata_kuliah.nama if p.jadwal.mata_kuliah else 'Blok'} — "
                      f"Kelas {p.kelas.nama if p.kelas else '?'}"
                      + (f" ({p.jadwal.tahun_ajaran})" if p.jadwal.tahun_ajaran else "")),
        }
        for p in baris
    ])


def _susun(id_jk, cocokkan):
    jk = db.session.get(JadwalKelas, id_jk)
    if jk is None:
        raise GalatAPI("Blok/kelas tidak ditemukan.", 404)
    p = Pengaturan.ambil()
    sesi, baris = mesin.susun(jk.id, p, cocokkan_ruangan=cocokkan)
    return jk, p, sesi, baris


@bp.get("/laporan/pratinjau")
def pratinjau():
    id_jk = request.args.get("kelas", type=int)
    if not id_jk:
        raise GalatAPI("Pilih blok dan kelas terlebih dahulu.")
    cocokkan = request.args.get("ruangan") == "1"
    jk, _, sesi, baris = _susun(id_jk, cocokkan)
    return jsonify(
        sesi=[{k: s[k] for k in ("nama", "label_tanggal", "jam_mulai", "jam_selesai")} for s in sesi],
        baris=[{"no": b["no"], "nim": b["nim"], "nama": b["nama"],
                "sel": [{"status": x["status"], "waktu": x["waktu"], "ceklog": x["ceklog"]} for x in b["sel"]]}
               for b in baris[:80]],
        total_baris=len(baris),
        statistik=mesin.statistik(sesi, baris),
    )


@bp.get("/laporan/unduh")
def unduh():
    id_jk = request.args.get("kelas", type=int)
    if not id_jk:
        raise GalatAPI("Pilih blok dan kelas terlebih dahulu.")
    bentuk = request.args.get("bentuk", "ringkas")
    cocokkan = request.args.get("ruangan") == "1"
    jk, p, sesi, baris = _susun(id_jk, cocokkan)
    if not sesi or not baris:
        raise GalatAPI("Blok ini belum punya sesi atau peserta.")

    judul, meta = _judul_meta(jk, p)
    try:
        buf = rekap.tulis_xlsx(sesi, baris, judul, meta, bentuk=bentuk)
    except ValueError as e:
        raise GalatAPI(str(e))

    blok = jk.jadwal.mata_kuliah.nama if jk.jadwal.mata_kuliah else "Blok"
    nama = _nama_berkas(f"Rekapan Absensi {blok} Kelas {jk.kelas.nama if jk.kelas else ''}")
    return send_file(buf,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=f"{nama}.xlsx")

"""Menyusun laporan absensi satu blok untuk satu kelas.

Urutan penentuan status tiap mahasiswa pada tiap sesi:
    1. tercatat Sakit  -> S
    2. tercatat Izin   -> I
    3. ada scan dalam jendela sesi -> H
    4. selain itu      -> A
"""

from datetime import time

from .models import (
    JadwalHari,
    JadwalJam,
    JadwalKelas,
    JadwalMahasiswa,
    Ketidakhadiran,
    LogScan,
    Mahasiswa,
    Mesin,
    db,
)

HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu", "Minggu"]


def label_tanggal(tanggal):
    return f"{HARI_ID[tanggal.weekday()]}, {tanggal.strftime('%d/%m/%Y')}"


def _menit(jam):
    return jam.hour * 60 + jam.minute


def _jam(menit):
    return time((menit // 60) % 24, menit % 60)


def ambil_sesi(jadwal_kelas_id, pengaturan):
    """Semua sesi milik satu kelas pada satu blok, terurut tanggal lalu jam."""
    baris = (
        db.session.query(JadwalJam, JadwalHari)
        .join(JadwalHari, JadwalJam.jadwal_hari_id == JadwalHari.id)
        .filter(JadwalHari.jadwal_kelas_id == jadwal_kelas_id)
        .order_by(JadwalHari.tanggal, JadwalJam.jam_masuk)
        .all()
    )
    hasil = []
    for sesi, hari in baris:
        selesai = sesi.jam_selesai(pengaturan)
        hasil.append(
            {
                "id": sesi.id,
                "tanggal": hari.tanggal,
                "label_tanggal": label_tanggal(hari.tanggal),
                "nama": sesi.kegiatan,
                "jam_mulai": sesi.jam_masuk.strftime("%H.%M"),
                "jam_selesai": selesai.strftime("%H.%M"),
                "ruangan_id": sesi.ruangan_id,
                "ruangan": sesi.ruangan.nama if sesi.ruangan else None,
                "_mulai_menit": _menit(sesi.jam_masuk) - pengaturan.toleransi_awal,
                "_selesai_menit": _menit(selesai) + pengaturan.toleransi_akhir,
            }
        )
    return hasil


def ambil_peserta(jadwal_kelas_id):
    return (
        db.session.query(Mahasiswa)
        .join(JadwalMahasiswa, JadwalMahasiswa.mahasiswa_id == Mahasiswa.id)
        .filter(JadwalMahasiswa.jadwal_kelas_id == jadwal_kelas_id)
        .order_by(Mahasiswa.nim)
        .all()
    )


def _indeks_scan(id_fingers, tanggal_awal, tanggal_akhir, cocokkan_ruangan):
    """(id_finger, tanggal) -> [(menit, ruangan_id), ...] terurut."""
    if not id_fingers:
        return {}
    q = LogScan.query.filter(
        LogScan.id_finger.in_(list(id_fingers)),
        LogScan.tanggal >= tanggal_awal,
        LogScan.tanggal <= tanggal_akhir,
    )
    ruang_mesin = {}
    if cocokkan_ruangan:
        ruang_mesin = {m.serial: m.ruangan_id for m in Mesin.query.all() if m.serial}

    indeks = {}
    for s in q.all():
        kunci = (s.id_finger, s.tanggal)
        indeks.setdefault(kunci, []).append(
            (_menit(s.jam), ruang_mesin.get(s.serial) if cocokkan_ruangan else None)
        )
    for v in indeks.values():
        v.sort()
    return indeks


def _indeks_ketidakhadiran(mahasiswa_ids, tanggal_awal, tanggal_akhir):
    """(mahasiswa_id, tanggal) -> {sesi_id atau None: jenis}."""
    if not mahasiswa_ids:
        return {}
    q = Ketidakhadiran.query.filter(
        Ketidakhadiran.mahasiswa_id.in_(mahasiswa_ids),
        Ketidakhadiran.tanggal >= tanggal_awal,
        Ketidakhadiran.tanggal <= tanggal_akhir,
    )
    indeks = {}
    for k in q.all():
        indeks.setdefault((k.mahasiswa_id, k.tanggal), {})[k.jadwal_jam_id] = k.jenis
    return indeks


def susun(jadwal_kelas_id, pengaturan, cocokkan_ruangan=False):
    """Kembalikan (daftar sesi, daftar baris) siap ditulis ke .xlsx."""
    jk = db.session.get(JadwalKelas, jadwal_kelas_id)
    if jk is None:
        raise ValueError("Jadwal kelas tidak ditemukan.")

    sesi = ambil_sesi(jadwal_kelas_id, pengaturan)
    peserta = ambil_peserta(jadwal_kelas_id)
    if not sesi or not peserta:
        return sesi, []

    tanggal_awal = min(s["tanggal"] for s in sesi)
    tanggal_akhir = max(s["tanggal"] for s in sesi)

    fingers = {m.id_finger for m in peserta if m.id_finger}
    scan = _indeks_scan(fingers, tanggal_awal, tanggal_akhir, cocokkan_ruangan)
    absen = _indeks_ketidakhadiran([m.id for m in peserta], tanggal_awal, tanggal_akhir)

    baris = []
    for nomor, mhs in enumerate(peserta, 1):
        sel = []
        for s in sesi:
            catatan = absen.get((mhs.id, s["tanggal"]), {})
            jenis = catatan.get(s["id"], catatan.get(None))
            if jenis in ("S", "I"):
                sel.append({"status": jenis, "ceklog": [], "waktu": "MANUAL"})
                continue

            cocok = []
            if mhs.id_finger:
                for menit, ruangan_id in scan.get((mhs.id_finger, s["tanggal"]), []):
                    if not (s["_mulai_menit"] <= menit <= s["_selesai_menit"]):
                        continue
                    if (
                        cocokkan_ruangan
                        and s["ruangan_id"]
                        and ruangan_id
                        and ruangan_id != s["ruangan_id"]
                    ):
                        continue
                    cocok.append(menit)

            if cocok:
                sel.append(
                    {
                        "status": "H",
                        "ceklog": [_jam(m).strftime("%H:%M") for m in cocok[:2]],
                        "waktu": _jam(cocok[0]).strftime("%H:%M"),
                    }
                )
            else:
                sel.append({"status": "A", "ceklog": [], "waktu": "-"})

        baris.append(
            {
                "no": nomor,
                "nim": mhs.nim,
                "nama": mhs.nama,
                "id_finger": mhs.id_finger,
                "sel": sel,
            }
        )
    return sesi, baris


def statistik(sesi, baris):
    total = len(sesi) * len(baris)
    if not total:
        return {"peserta": len(baris), "sesi": len(sesi), "persen_hadir": 0, "tanpa_finger": 0}
    hadir = sum(1 for b in baris for s in b["sel"] if s["status"] == "H")
    return {
        "peserta": len(baris),
        "sesi": len(sesi),
        "persen_hadir": round(100 * hadir / total, 1),
        "tanpa_finger": sum(1 for b in baris if not b["id_finger"]),
    }

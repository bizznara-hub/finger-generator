"""API jadwal: blok -> kelas -> tanggal -> sesi, dan peserta."""

from datetime import datetime, timedelta

from flask import jsonify, request

from core.laporan import label_tanggal, susun
from core.models import (
    Dosen,
    ProfilJam,
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


BATAS_HARI = 200


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


def _buat_hari(jk_id, awal, akhir, lewati_akhir_pekan=True):
    """Buat tanggal sepanjang rentang. Sabtu dan Minggu dilewati, mengikuti
    aplikasi PHP lama, kecuali admin memilih satu tanggal itu sendiri."""
    ada = {h.tanggal for h in JadwalHari.query.filter_by(jadwal_kelas_id=jk_id).all()}
    jumlah, dilewati, t = 0, 0, awal
    while t <= akhir and jumlah < BATAS_HARI:
        if lewati_akhir_pekan and t.weekday() >= 5:
            dilewati += 1
        elif t not in ada:
            db.session.add(JadwalHari(jadwal_kelas_id=jk_id, tanggal=t))
            ada.add(t)
            jumlah += 1
        t += timedelta(days=1)
    return jumlah, dilewati, t <= akhir


def _blok(j):
    return {
        "id": j.id,
        "mata_kuliah_id": j.mata_kuliah_id,
        "mata_kuliah": j.mata_kuliah.nama if j.mata_kuliah else None,
        "semester": j.semester,
        "tahun_ajaran": j.tahun_ajaran,
        "koordinator_id": j.koordinator_id,
        "koordinator": j.koordinator.nama if j.koordinator else None,
        "sekretaris_id": j.sekretaris_id,
        "sekretaris": j.sekretaris.nama if j.sekretaris else None,
        "profil_jam_id": j.profil_jam_id,
        "profil_jam": j.profil_jam.label if j.profil_jam else None,
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


def _dosen_ada(id_dosen, sebutan):
    if not id_dosen:
        raise GalatAPI(f"{sebutan} wajib dipilih.")
    if db.session.get(Dosen, int(id_dosen)) is None:
        raise GalatAPI(f"{sebutan} tidak ditemukan.")
    return int(id_dosen)


@bp.post("/jadwal")
def tambah_blok():
    """Satu formulir membuat blok, kelas pesertanya, dan seluruh tanggalnya
    sekaligus - mengikuti alur aplikasi PHP lama."""
    d = request.get_json(silent=True) or {}
    if not d.get("mata_kuliah_id"):
        raise GalatAPI("Mata kuliah wajib dipilih.")
    semester = (d.get("semester") or "").strip() or None
    tahun = (d.get("tahun_ajaran") or "").strip() or None
    # Hanya dua nilai, mengikuti daftar pilihan aplikasi PHP.
    if semester not in ("Awal", "Akhir"):
        raise GalatAPI("Semester harus Awal atau Akhir.")
    if not tahun:
        raise GalatAPI("Tahun ajaran wajib diisi.")

    koordinator = _dosen_ada(d.get("koordinator_id"), "Koordinator")
    sekretaris = _dosen_ada(d.get("sekretaris_id"), "Sekretaris")

    kelas_ids = [int(x) for x in (d.get("kelas_id") or []) if x]
    if not kelas_ids:
        raise GalatAPI("Pilih sedikitnya satu kelas.")

    awal = _tanggal(d.get("tanggal_mulai"))
    akhir = _tanggal(d.get("tanggal_selesai"))
    if awal is None or akhir is None:
        raise GalatAPI("Tanggal mulai dan tanggal selesai wajib diisi.")
    if awal >= akhir:
        raise GalatAPI("Tanggal selesai harus sesudah tanggal mulai.")

    profil_id = d.get("profil_jam_id")
    if not profil_id or db.session.get(ProfilJam, int(profil_id)) is None:
        raise GalatAPI("Pengaturan jam wajib dipilih.")

    if Jadwal.query.filter_by(mata_kuliah_id=int(d["mata_kuliah_id"]),
                              semester=semester, tahun_ajaran=tahun).first():
        raise GalatAPI("Jadwal tersebut sudah ada.")

    j = Jadwal(
        mata_kuliah_id=int(d["mata_kuliah_id"]),
        semester=semester,
        tahun_ajaran=tahun,
        koordinator_id=koordinator,
        sekretaris_id=sekretaris,
        profil_jam_id=int(profil_id),
    )
    db.session.add(j)
    db.session.flush()

    hari = dilewati = 0
    kepenuhan = False
    for kid in dict.fromkeys(kelas_ids):
        jk = JadwalKelas(jadwal_id=j.id, kelas_id=kid)
        db.session.add(jk)
        db.session.flush()
        for m in Mahasiswa.query.filter_by(kelas_id=kid).all():
            db.session.add(JadwalMahasiswa(jadwal_kelas_id=jk.id, mahasiswa_id=m.id))
        n, lewat, penuh = _buat_hari(jk.id, awal, akhir)
        hari, dilewati, kepenuhan = hari + n, lewat, kepenuhan or penuh
    db.session.commit()

    pesan = (f"Blok tersimpan: {len(set(kelas_ids))} kelas, {hari} tanggal dibuat, "
             f"{dilewati} akhir pekan dilewati.")
    if kepenuhan:
        pesan += f" Berhenti di batas {BATAS_HARI} tanggal per kelas."
    return jsonify(baris=_blok(j), pesan=pesan)


@bp.put("/jadwal/<int:id_jadwal>")
def ubah_blok(id_jadwal):
    j = db.session.get(Jadwal, id_jadwal) or _tidak_ada()
    d = request.get_json(silent=True) or {}
    if d.get("mata_kuliah_id"):
        j.mata_kuliah_id = int(d["mata_kuliah_id"])
    j.semester = (d.get("semester") or "").strip() or None
    j.tahun_ajaran = (d.get("tahun_ajaran") or "").strip() or None
    if "koordinator_id" in d:
        j.koordinator_id = _dosen_ada(d.get("koordinator_id"), "Koordinator")
    if "sekretaris_id" in d:
        j.sekretaris_id = _dosen_ada(d.get("sekretaris_id"), "Sekretaris")
    if d.get("profil_jam_id"):
        if db.session.get(ProfilJam, int(d["profil_jam_id"])) is None:
            raise GalatAPI("Pengaturan jam tidak ditemukan.")
        j.profil_jam_id = int(d["profil_jam_id"])
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

    # Saat blok dibuat, seluruh kelas mendapat rentang tanggal yang sama. Kelas
    # yang menyusul harus ikut rentang itu juga, kalau tidak ia lahir kosong dan
    # admin harus mengetik ulang seluruh tanggalnya.
    saudara = next((x for x in j.kelas_jadwal if x.id != jk.id and x.hari), None)
    disalin = 0
    if saudara:
        for h in saudara.hari:
            db.session.add(JadwalHari(jadwal_kelas_id=jk.id, tanggal=h.tanggal))
            disalin += 1
    db.session.commit()

    pesan = "Kelas ditambahkan beserta seluruh mahasiswanya."
    if disalin:
        pesan += f" {disalin} tanggal disalin dari kelas {saudara.kelas.nama}."
    return jsonify(id=jk.id, pesan=pesan)


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
        "jam_selesai_hitung": s.jam_selesai().strftime("%H:%M"),
        # Rentang per jam seperti tampilan PHP: 08:00-08:50, 09:00-09:50, ...
        "slot": [f"{a.strftime('%H:%M')}-{b.strftime('%H:%M')}" for a, b in s.slot()],
        "ruangan_id": s.ruangan_id,
        "ruangan": s.ruangan.nama if s.ruangan else None,
        "departemen_id": s.departemen_id,
        "departemen": s.departemen.nama if s.departemen else None,
        "dosen_id": [x.dosen_id for x in s.pengajar],
        "dosen": [x.dosen.nama for x in s.pengajar if x.dosen],
    }


@bp.get("/jadwal/kelas/<int:id_jk>")
def rinci_kelas(id_jk):
    jk = db.session.get(JadwalKelas, id_jk) or _tidak_ada()
    p = Pengaturan.ambil()
    j = jk.jadwal
    hari = JadwalHari.query.filter_by(jadwal_kelas_id=id_jk).order_by(JadwalHari.tanggal).all()
    terdaftar = {x.mahasiswa_id for x in jk.peserta}

    # Rekap kehadiran per mahasiswa, dipakai kolom Masuk / Tidak Masuk pada
    # daftar mahasiswa per kelas - sama seperti tampilan aplikasi PHP.
    rekap = {}
    try:
        _, baris = susun(id_jk, p)
        for b in baris:
            masuk = sum(1 for x in b["sel"] if x["status"] == "H")
            rekap[b["nim"]] = (masuk, len(b["sel"]) - masuk)
    except ValueError:
        pass

    return jsonify(
        blok=j.mata_kuliah.nama if j.mata_kuliah else "Blok",
        jadwal_id=jk.jadwal_id,
        kelas=jk.kelas.nama if jk.kelas else "?",
        semester=j.semester,
        tahun_ajaran=j.tahun_ajaran,
        koordinator=j.koordinator.nama if j.koordinator else None,
        sekretaris=j.sekretaris.nama if j.sekretaris else None,
        profil_jam=j.profil_jam.label if j.profil_jam else "—",
        # Daftar kelas yang sudah dipilih pada blok ini, untuk pemilih kelas.
        daftar_kelas=[
            {"id": x.id, "nama": x.kelas.nama if x.kelas else "?",
             "jumlah_peserta": len(x.peserta), "jumlah_hari": len(x.hari)}
            for x in sorted(j.kelas_jadwal, key=lambda x: (x.kelas.nama if x.kelas else ""))
        ],
        pengaturan={
            "toleransi_awal": p.toleransi_awal,
            "toleransi_akhir": p.toleransi_akhir,
            "jam_kuliah": p.jam_kuliah.strftime("%H:%M") if p.jam_kuliah else "07:00",
            "profil_jam": jk.jadwal.profil_jam.label if jk.jadwal.profil_jam else "—",
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
                "masuk": rekap.get(x.mahasiswa.nim, (0, 0))[0],
                "tidak_masuk": rekap.get(x.mahasiswa.nim, (0, 0))[1],
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

    # Satu tanggal yang dipilih sendiri tetap dibuat walau jatuh di akhir pekan;
    # penyaringan akhir pekan hanya berlaku saat membuat serentetan tanggal.
    satu_hari = awal == akhir
    jumlah, dilewati, penuh = _buat_hari(jk.id, awal, akhir, lewati_akhir_pekan=not satu_hari)
    db.session.commit()

    if not jumlah:
        return jsonify(pesan="Tidak ada tanggal baru: semuanya sudah ada atau jatuh di akhir pekan.")
    pesan = f"{jumlah} tanggal ditambahkan."
    if dilewati:
        pesan += f" {dilewati} akhir pekan dilewati."
    if penuh:
        pesan += f" Berhenti di batas {BATAS_HARI} tanggal."
    return jsonify(pesan=pesan)


@bp.delete("/jadwal/hari/<int:id_hari>")
def hapus_hari(id_hari):
    h = db.session.get(JadwalHari, id_hari) or _tidak_ada()
    db.session.delete(h)
    db.session.commit()
    return jsonify(pesan="Tanggal dihapus beserta sesinya.")


def _terapkan_sesi(s, d):
    s.kegiatan = (d.get("kegiatan") or "").strip()
    s.jam_masuk = _jam(d.get("jam_masuk"))
    s.jam_selesai_manual = _jam(d.get("jam_selesai_manual")) if d.get("jam_selesai_manual") else None
    s.ruangan_id = int(d["ruangan_id"]) if d.get("ruangan_id") else None
    s.departemen_id = int(d["departemen_id"]) if d.get("departemen_id") else None

    if not s.kegiatan:
        raise GalatAPI("Nama kegiatan wajib diisi.")
    if s.jam_masuk is None:
        raise GalatAPI("Jam masuk tidak valid. Gunakan format 07:00.")
    # Ruangan wajib seperti pada aplikasi PHP: tanpa itu scan mesin tidak bisa
    # dicocokkan ke sesi mana pun.
    if not s.ruangan_id:
        raise GalatAPI("Ruangan wajib dipilih.")

    # Dibedakan antara tidak dikirim (pakai bawaan 2) dan dikirim bernilai 0,
    # supaya nol ditolak alih-alih diam-diam berubah jadi 2.
    mentah = d.get("jml_jam")
    try:
        s.jml_jam = 2 if mentah in (None, "") else int(mentah)
    except (TypeError, ValueError):
        raise GalatAPI("Jumlah jam harus berupa angka.")
    if not 1 <= s.jml_jam <= 12:
        raise GalatAPI("Jumlah jam harus antara 1 dan 12.")

    if s.jam_selesai_manual and s.jam_selesai_manual <= s.jam_masuk:
        raise GalatAPI("Jam selesai manual harus sesudah jam masuk.")

    if not s.jam_selesai_manual and s.slot()[-1][1] <= s.jam_masuk:
        raise GalatAPI("Sesi sepanjang itu melewati tengah malam. Kurangi jumlah jam.")


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

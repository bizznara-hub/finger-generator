"""Skema basis data.

Mengikuti rancangan aplikasi PHP lama (db_absenfkuh) karena struktur jadwalnya
sudah terbukti dipakai, dengan tiga tambahan: tabel ketidakhadiran (sakit/izin),
kolom sumber pada log scan, dan pengaturan koneksi att_log.
"""

from datetime import date, datetime, time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Pengguna(db.Model):
    __tablename__ = "pengguna"
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False)
    sandi_hash = db.Column(db.String(255), nullable=False)
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    dibuat = db.Column(db.DateTime, default=datetime.utcnow)

    def set_sandi(self, sandi):
        # pbkdf2 dipilih secara eksplisit: scrypt (baku Werkzeug) tidak tersedia
        # pada sebagian pemasangan Python, termasuk Python 3.9 bawaan macOS.
        self.sandi_hash = generate_password_hash(sandi, method="pbkdf2:sha256")

    def cek_sandi(self, sandi):
        return check_password_hash(self.sandi_hash, sandi)


class Departemen(db.Model):
    __tablename__ = "departemen"
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True)
    nama = db.Column(db.String(150), nullable=False)


class Dosen(db.Model):
    """Dosen hanya dicatat sebagai pengampu jadwal, bukan peserta absensi:
    yang discan mesin adalah mahasiswa. Karena itu tidak ada ID Finger di sini.
    """

    __tablename__ = "dosen"
    id = db.Column(db.Integer, primary_key=True)
    nip = db.Column(db.String(40))
    nama = db.Column(db.String(150), nullable=False)


class Kelas(db.Model):
    __tablename__ = "kelas"
    id = db.Column(db.Integer, primary_key=True)
    departemen_id = db.Column(db.Integer, db.ForeignKey("departemen.id"))
    nama = db.Column(db.String(60), nullable=False)
    angkatan = db.Column(db.String(10))

    departemen = db.relationship("Departemen")

    @property
    def label(self):
        return f"{self.nama} ({self.angkatan})" if self.angkatan else self.nama


class Mahasiswa(db.Model):
    __tablename__ = "mahasiswa"
    id = db.Column(db.Integer, primary_key=True)
    kelas_id = db.Column(db.Integer, db.ForeignKey("kelas.id"))
    id_finger = db.Column(db.String(20), index=True)
    nim = db.Column(db.String(30), unique=True, nullable=False)
    nama = db.Column(db.String(150), nullable=False)

    kelas = db.relationship("Kelas")


class Ruangan(db.Model):
    __tablename__ = "ruangan"
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20))
    nama = db.Column(db.String(120), nullable=False)
    kapasitas = db.Column(db.Integer)


class Mesin(db.Model):
    """Mesin fingerprint. Serial dipakai mencocokkan att_log.sn -> ruangan."""

    __tablename__ = "mesin"
    id = db.Column(db.Integer, primary_key=True)
    ruangan_id = db.Column(db.Integer, db.ForeignKey("ruangan.id"))
    serial = db.Column(db.String(60), unique=True, nullable=False)
    nama = db.Column(db.String(120))
    ip_address = db.Column(db.String(40))
    port = db.Column(db.String(10))

    ruangan = db.relationship("Ruangan")


class MataKuliah(db.Model):
    """Satu mata kuliah = satu Blok."""

    __tablename__ = "mata_kuliah"
    id = db.Column(db.Integer, primary_key=True)
    departemen_id = db.Column(db.Integer, db.ForeignKey("departemen.id"))
    kode = db.Column(db.String(30))
    nama = db.Column(db.String(150), nullable=False)
    sks = db.Column(db.Integer)

    departemen = db.relationship("Departemen")


class Pengaturan(db.Model):
    """Satu baris saja - dipakai menghitung jam selesai sesi."""

    __tablename__ = "pengaturan"
    id = db.Column(db.Integer, primary_key=True)
    toleransi_awal = db.Column(db.Integer, default=15, nullable=False)
    toleransi_akhir = db.Column(db.Integer, default=15, nullable=False)
    # Jam masuk perkuliahan - dipakai sebagai isian awal saat menambah sesi.
    jam_kuliah = db.Column(db.Time, default=time(7, 30))
    nama_institusi = db.Column(db.String(150), default="FAKULTAS KEDOKTERAN")
    nama_universitas = db.Column(db.String(150), default="UNIVERSITAS MEGA BUANA PALOPO")

    # koneksi opsional ke basis data software Fingerspot
    attlog_host = db.Column(db.String(120))
    attlog_port = db.Column(db.Integer, default=3306)
    attlog_nama_db = db.Column(db.String(80))
    attlog_user = db.Column(db.String(80))
    attlog_sandi = db.Column(db.String(120))

    @classmethod
    def ambil(cls):
        baris = cls.query.first()
        if baris is None:
            baris = cls()
            db.session.add(baris)
            db.session.commit()
        return baris


class ProfilJam(db.Model):
    """Satu aturan pembagian waktu kuliah, dipilih per blok.

    Aplikasi PHP menyimpan beberapa profil sekaligus - misalnya 55 menit per
    jam untuk kuliah biasa dan 30 menit tanpa jeda untuk kegiatan padat - lalu
    tiap jadwal menunjuk salah satunya. Karena itu angkanya tidak bisa
    diletakkan di Pengaturan yang hanya satu baris.
    """

    __tablename__ = "profil_jam"
    id = db.Column(db.Integer, primary_key=True)
    menit_perjam = db.Column(db.Integer, nullable=False)
    menit_pergantian = db.Column(db.Integer, default=0, nullable=False)
    istirahat_mulai = db.Column(db.Time)
    istirahat_selesai = db.Column(db.Time)
    bawaan = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def label(self):
        ist = "-"
        if self.istirahat_mulai and self.istirahat_selesai:
            ist = f"{self.istirahat_mulai.strftime('%H:%M')}-{self.istirahat_selesai.strftime('%H:%M')}"
        return (f"Perjam = {self.menit_perjam} Menit | Selisih = {self.menit_pergantian} Menit"
                f" | Jam Istirahat = {ist}")

    @classmethod
    def bawaan_atau_pertama(cls):
        return cls.query.filter_by(bawaan=True).first() or cls.query.order_by(cls.id).first()


class Jadwal(db.Model):
    """Satu penawaran Blok pada satu semester."""

    __tablename__ = "jadwal"
    id = db.Column(db.Integer, primary_key=True)
    mata_kuliah_id = db.Column(db.Integer, db.ForeignKey("mata_kuliah.id"), nullable=False)
    semester = db.Column(db.String(30))
    tahun_ajaran = db.Column(db.String(20))
    koordinator_id = db.Column(db.Integer, db.ForeignKey("dosen.id"))
    sekretaris_id = db.Column(db.Integer, db.ForeignKey("dosen.id"))
    profil_jam_id = db.Column(db.Integer, db.ForeignKey("profil_jam.id"))

    mata_kuliah = db.relationship("MataKuliah")
    profil_jam = db.relationship("ProfilJam")
    # foreign_keys wajib disebut: dua kolom ini menunjuk tabel yang sama,
    # sehingga SQLAlchemy tidak bisa menebak sendiri pasangannya.
    koordinator = db.relationship("Dosen", foreign_keys=[koordinator_id])
    sekretaris = db.relationship("Dosen", foreign_keys=[sekretaris_id])
    kelas_jadwal = db.relationship(
        "JadwalKelas", back_populates="jadwal", cascade="all, delete-orphan"
    )

    @property
    def label(self):
        bagian = [self.mata_kuliah.nama if self.mata_kuliah else "-"]
        if self.semester:
            bagian.append(self.semester)
        if self.tahun_ajaran:
            bagian.append(self.tahun_ajaran)
        return " - ".join(bagian)


class JadwalKelas(db.Model):
    """Kelas yang mengambil sebuah blok."""

    __tablename__ = "jadwal_kelas"
    id = db.Column(db.Integer, primary_key=True)
    jadwal_id = db.Column(db.Integer, db.ForeignKey("jadwal.id"), nullable=False)
    kelas_id = db.Column(db.Integer, db.ForeignKey("kelas.id"), nullable=False)

    jadwal = db.relationship("Jadwal", back_populates="kelas_jadwal")
    kelas = db.relationship("Kelas")
    hari = db.relationship(
        "JadwalHari", back_populates="jadwal_kelas", cascade="all, delete-orphan"
    )
    peserta = db.relationship(
        "JadwalMahasiswa", back_populates="jadwal_kelas", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("jadwal_id", "kelas_id", name="uq_jadwal_kelas"),)


class JadwalHari(db.Model):
    __tablename__ = "jadwal_hari"
    id = db.Column(db.Integer, primary_key=True)
    jadwal_kelas_id = db.Column(db.Integer, db.ForeignKey("jadwal_kelas.id"), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)

    jadwal_kelas = db.relationship("JadwalKelas", back_populates="hari")
    sesi = db.relationship(
        "JadwalJam", back_populates="hari", cascade="all, delete-orphan"
    )


class JadwalJam(db.Model):
    """Satu sesi. Dibuat manual oleh admin dan bisa diubah kapan saja."""

    __tablename__ = "jadwal_jam"
    id = db.Column(db.Integer, primary_key=True)
    jadwal_hari_id = db.Column(db.Integer, db.ForeignKey("jadwal_hari.id"), nullable=False)
    ruangan_id = db.Column(db.Integer, db.ForeignKey("ruangan.id"))
    departemen_id = db.Column(db.Integer, db.ForeignKey("departemen.id"))
    kegiatan = db.Column(db.String(120), nullable=False)
    jam_masuk = db.Column(db.Time, nullable=False)
    jml_jam = db.Column(db.Integer, default=2, nullable=False)
    jam_selesai_manual = db.Column(db.Time)  # bila diisi, menimpa hasil hitungan

    hari = db.relationship("JadwalHari", back_populates="sesi")
    ruangan = db.relationship("Ruangan")
    departemen = db.relationship("Departemen")
    pengajar = db.relationship(
        "JadwalDosen", back_populates="sesi", cascade="all, delete-orphan"
    )

    def profil(self):
        """Profil jam milik blok tempat sesi ini bernaung."""
        j = self.hari.jadwal_kelas.jadwal if self.hari and self.hari.jadwal_kelas else None
        return (j.profil_jam if j and j.profil_jam else None) or ProfilJam.bawaan_atau_pertama()

    def slot(self, profil=None):
        """Pecah sesi menjadi rentang per jam, seperti tampilan aplikasi PHP.

        Sesi 2 jam dengan 50 menit per jam dan jeda 10 menit menghasilkan
        08:00-08:50 lalu 09:00-09:50. Jam istirahat dilompati: slot yang akan
        bertabrakan dengannya digeser mulai setelah istirahat selesai.
        """

        def ke_menit(t):
            return t.hour * 60 + t.minute

        def ke_jam(m):
            return time((m // 60) % 24, m % 60)

        profil = profil or self.profil()
        pengaturan = profil
        ist_awal = ke_menit(pengaturan.istirahat_mulai) if pengaturan.istirahat_mulai else None
        ist_akhir = ke_menit(pengaturan.istirahat_selesai) if pengaturan.istirahat_selesai else None
        pakai_istirahat = ist_awal is not None and ist_akhir is not None and ist_akhir > ist_awal

        hasil = []
        for i in range(max(self.jml_jam, 1)):
            if not i:
                mulai = ke_menit(self.jam_masuk)
            elif pakai_istirahat and hasil[-1][1] == ist_awal:
                # Persis seperti PHP: hanya slot yang berhenti tepat saat
                # istirahat dimulai yang dilompati, dan sambungannya mulai tepat
                # saat istirahat usai tanpa jeda pergantian. Sesi yang kebetulan
                # melintasi istirahat tanpa berhenti pas di angkanya dibiarkan -
                # itulah sebabnya jadwal nyata memuat sesi 11:20-12:05.
                mulai = ist_akhir
            else:
                mulai = hasil[-1][1] + pengaturan.menit_pergantian
            hasil.append((mulai, mulai + pengaturan.menit_perjam))
        return [(ke_jam(a), ke_jam(b)) for a, b in hasil]

    def jam_selesai(self, profil=None):
        """Akhir slot terakhir, kecuali admin mengisi jam selesai manual."""
        if self.jam_selesai_manual:
            return self.jam_selesai_manual
        return self.slot(profil)[-1][1]


class JadwalDosen(db.Model):
    __tablename__ = "jadwal_dosen"
    id = db.Column(db.Integer, primary_key=True)
    jadwal_jam_id = db.Column(db.Integer, db.ForeignKey("jadwal_jam.id"), nullable=False)
    dosen_id = db.Column(db.Integer, db.ForeignKey("dosen.id"), nullable=False)

    sesi = db.relationship("JadwalJam", back_populates="pengajar")
    dosen = db.relationship("Dosen")


class JadwalMahasiswa(db.Model):
    __tablename__ = "jadwal_mahasiswa"
    id = db.Column(db.Integer, primary_key=True)
    jadwal_kelas_id = db.Column(db.Integer, db.ForeignKey("jadwal_kelas.id"), nullable=False)
    mahasiswa_id = db.Column(db.Integer, db.ForeignKey("mahasiswa.id"), nullable=False)

    jadwal_kelas = db.relationship("JadwalKelas", back_populates="peserta")
    mahasiswa = db.relationship("Mahasiswa")

    __table_args__ = (
        UniqueConstraint("jadwal_kelas_id", "mahasiswa_id", name="uq_jadwal_mahasiswa"),
    )


class Ketidakhadiran(db.Model):
    """Sakit (S) dan Izin (I). Menimpa hasil pembacaan mesin."""

    __tablename__ = "ketidakhadiran"
    id = db.Column(db.Integer, primary_key=True)
    mahasiswa_id = db.Column(db.Integer, db.ForeignKey("mahasiswa.id"), nullable=False)
    jenis = db.Column(db.String(1), nullable=False)  # "S" atau "I"
    tanggal = db.Column(db.Date, nullable=False, index=True)
    jadwal_jam_id = db.Column(db.Integer, db.ForeignKey("jadwal_jam.id"))  # kosong = sehari penuh
    keterangan = db.Column(db.String(255))
    dibuat = db.Column(db.DateTime, default=datetime.utcnow)

    mahasiswa = db.relationship("Mahasiswa")
    sesi = db.relationship("JadwalJam")


class LogScan(db.Model):
    """Satu sentuhan jari. Diisi dari impor .xls maupun tarikan att_log."""

    __tablename__ = "log_scan"
    id = db.Column(db.Integer, primary_key=True)
    id_finger = db.Column(db.String(20), nullable=False, index=True)
    nama_mesin = db.Column(db.String(150))
    serial = db.Column(db.String(60))
    tanggal = db.Column(db.Date, nullable=False, index=True)
    jam = db.Column(db.Time, nullable=False)
    sumber = db.Column(db.String(20), default="impor")  # "impor" atau "att_log"

    __table_args__ = (
        UniqueConstraint("id_finger", "tanggal", "jam", "serial", name="uq_log_scan"),
    )


def semai_awal():
    """Buat akun admin dan baris pengaturan bila database masih kosong."""
    Pengaturan.ambil()
    if Pengguna.query.count() == 0:
        admin = Pengguna(nama="Administrator", username="admin")
        admin.set_sandi("admin")
        db.session.add(admin)
        db.session.commit()
        return True
    return False

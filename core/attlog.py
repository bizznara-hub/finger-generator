"""Jalur A - menarik data mentah langsung dari basis data software Fingerspot.

Koneksi dibuka baca-saja dan hanya menyentuh tabel att_log.
"""

import pymysql

from .models import LogScan, db


class GalatAttlog(Exception):
    pass


def _bulatkan(waktu):
    """Mesin menulis 07:33:59.941 untuk pukul 07:34."""
    menit = waktu.hour * 60 + waktu.minute
    if waktu.second >= 30:
        menit += 1
    return menit


def _sambung(pengaturan):
    if not pengaturan.attlog_host or not pengaturan.attlog_nama_db:
        raise GalatAttlog(
            "Koneksi att_log belum diatur. Isi dulu di menu Pengaturan."
        )
    try:
        return pymysql.connect(
            host=pengaturan.attlog_host,
            port=pengaturan.attlog_port or 3306,
            user=pengaturan.attlog_user or "",
            password=pengaturan.attlog_sandi or "",
            database=pengaturan.attlog_nama_db,
            connect_timeout=8,
            read_default_group=None,
            cursorclass=pymysql.cursors.SSCursor,
        )
    except pymysql.Error as e:
        raise GalatAttlog(f"Gagal menyambung ke basis data Fingerspot: {e}") from e


def uji_koneksi(pengaturan):
    """Kembalikan jumlah baris att_log bila koneksi berhasil."""
    sambungan = _sambung(pengaturan)
    try:
        with sambungan.cursor() as kursor:
            kursor.execute("SELECT COUNT(*) FROM att_log")
            (jumlah,) = kursor.fetchone()
        return int(jumlah)
    except pymysql.Error as e:
        raise GalatAttlog(f"Tabel att_log tidak terbaca: {e}") from e
    finally:
        sambungan.close()


def tarik(pengaturan, tanggal_awal, tanggal_akhir):
    """Ambil att_log pada rentang tanggal, simpan ke log_scan.

    Kembalikan (jumlah_baru, jumlah_dilewati).
    """
    sambungan = _sambung(pengaturan)
    baru = dilewati = 0
    try:
        with sambungan.cursor() as kursor:
            kursor.execute(
                "SELECT pin, scan_date, sn FROM att_log "
                "WHERE DATE(scan_date) BETWEEN %s AND %s ORDER BY scan_date",
                (tanggal_awal, tanggal_akhir),
            )
            ada = {
                (s.id_finger, s.tanggal, s.jam, s.serial)
                for s in LogScan.query.filter(
                    LogScan.tanggal >= tanggal_awal, LogScan.tanggal <= tanggal_akhir
                ).all()
            }
            for pin, scan_date, sn in kursor:
                if scan_date is None or pin is None:
                    continue
                from datetime import time as _t

                menit = _bulatkan(scan_date)
                jam = _t((menit // 60) % 24, menit % 60)
                kunci = (str(pin), scan_date.date(), jam, sn)
                if kunci in ada:
                    dilewati += 1
                    continue
                ada.add(kunci)
                db.session.add(
                    LogScan(
                        id_finger=str(pin),
                        tanggal=scan_date.date(),
                        jam=jam,
                        serial=sn,
                        sumber="att_log",
                    )
                )
                baru += 1
        db.session.commit()
    except pymysql.Error as e:
        db.session.rollback()
        raise GalatAttlog(f"Gagal membaca att_log: {e}") from e
    finally:
        sambungan.close()
    return baru, dilewati

"""Masuk, keluar, status sesi, dan akun."""

from flask import jsonify, request, session

from core.models import Pengguna, db

from . import GalatAPI, bp, pengguna_aktif


def _ringkas(p):
    return {"id": p.id, "nama": p.nama, "username": p.username}


@bp.post("/masuk")
def masuk():
    d = request.get_json(silent=True) or {}
    username = (d.get("username") or "").strip()
    p = Pengguna.query.filter_by(username=username).first()
    if not p or not p.aktif or not p.cek_sandi(d.get("sandi") or ""):
        raise GalatAPI("Username atau sandi salah.", 401)
    session.clear()
    session["pengguna"] = p.id
    session.permanent = True
    return jsonify(pengguna=_ringkas(p))


@bp.post("/keluar")
def keluar():
    session.clear()
    return jsonify(ok=True)


@bp.get("/status")
def status():
    p = pengguna_aktif()
    return jsonify(pengguna=_ringkas(p) if p else None)


@bp.get("/akun")
def akun():
    return jsonify(pengguna=_ringkas(pengguna_aktif()))


@bp.put("/akun")
def ubah_akun():
    p = pengguna_aktif()
    d = request.get_json(silent=True) or {}
    nama = (d.get("nama") or "").strip()
    username = (d.get("username") or "").strip()
    lama, baru, ulang = d.get("sandi_lama") or "", d.get("sandi_baru") or "", d.get("sandi_ulang") or ""

    if not nama or not username:
        raise GalatAPI("Nama dan username wajib diisi.")
    if Pengguna.query.filter(Pengguna.username == username, Pengguna.id != p.id).first():
        raise GalatAPI("Username itu sudah dipakai.")
    if baru:
        if not p.cek_sandi(lama):
            raise GalatAPI("Sandi lama salah.")
        if baru != ulang:
            raise GalatAPI("Sandi baru dan ulangannya tidak sama.")
        if len(baru) < 6:
            raise GalatAPI("Sandi baru minimal 6 karakter.")
        p.set_sandi(baru)

    p.nama, p.username = nama, username
    db.session.commit()
    return jsonify(pengguna=_ringkas(p))

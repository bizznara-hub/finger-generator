"""Perkakas bersama untuk semua modul tampilan."""

from flask import flash, g, render_template


def halaman(nama_menu, template, **konteks):
    """Render halaman sambil menandai menu mana yang sedang aktif."""
    g.menu_aktif = nama_menu
    return render_template(template, menu_aktif=nama_menu, **konteks)


def sukses(pesan):
    flash(pesan, "sukses")


def galat(pesan):
    flash(pesan, "galat")


def ambil_int(nilai, baku=None):
    try:
        return int(nilai)
    except (TypeError, ValueError):
        return baku


def ambil_teks(form, nama, baku=""):
    return (form.get(nama) or baku).strip()

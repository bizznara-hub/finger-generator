"""Menulis laporan absensi ke .xlsx dengan tata letak berkas rujukan."""

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

TIPIS = Side(style="thin")
TEBAL = Side(style="medium")
KOTAK_TIPIS = Border(left=TIPIS, right=TIPIS, top=TIPIS, bottom=TIPIS)
KOTAK_TEBAL = Border(left=TEBAL, right=TEBAL, top=TEBAL, bottom=TEBAL)
TENGAH = Alignment(horizontal="center", vertical="center", wrap_text=True)
KIRI = Alignment(horizontal="left", vertical="center", wrap_text=True)
ARSIR_HEADER = PatternFill("solid", fgColor="DDEBF7")
ARSIR_ALPA = PatternFill("solid", fgColor="FCE4E4")

KOLOM_MULAI = 4  # kolom D

# Judul sub-kolom untuk tiap bentuk laporan
SUBKOLOM = {
    "ringkas": ["Status", "Waktu"],
    "lengkap": ["Status", "Ceklog 1", "Ceklog 2", "Durasi\n(jam)"],
}


def _durasi(ceklog):
    if len(ceklog) < 2:
        return None
    awal = int(ceklog[0][:2]) * 60 + int(ceklog[0][3:5])
    akhir = int(ceklog[1][:2]) * 60 + int(ceklog[1][3:5])
    return round((akhir - awal) / 60, 2)


def _nilai_sel(sel, bentuk):
    """Ubah satu sel hasil laporan menjadi daftar nilai kolom."""
    if bentuk == "ringkas":
        return [sel["status"], sel["waktu"]]
    ceklog = sel.get("ceklog") or []
    if sel["status"] in ("S", "I"):
        return [sel["status"], "MANUAL", "MANUAL", None]
    return [
        sel["status"],
        ceklog[0] if ceklog else "-",
        ceklog[1] if len(ceklog) > 1 else "-",
        _durasi(ceklog),
    ]


def tulis_xlsx(sesi, baris, judul, meta, bentuk="ringkas", nama_sheet="Laporan_Absen"):
    """Susun berkas .xlsx.

    sesi   : [{label_tanggal, nama, jam_mulai, jam_selesai}, ...]
    baris  : [{no, nim, nama, sel: [{status, waktu, ceklog}, ...]}, ...]
    bentuk : "ringkas" (Status|Waktu, seperti berkas rujukan) atau "lengkap"
    """
    if bentuk not in SUBKOLOM:
        raise ValueError(f"Bentuk laporan tidak dikenal: {bentuk}")

    subkolom = SUBKOLOM[bentuk]
    per_sesi = len(subkolom)
    n_sesi = len(sesi)
    lengkap = bentuk == "lengkap"

    wb = Workbook()
    ws = wb.active
    ws.title = nama_sheet[:31]

    kol_h = KOLOM_MULAI + per_sesi * n_sesi
    kol_a, kol_s, kol_i = kol_h + 1, kol_h + 2, kol_h + 3
    kol_total = kol_h + 4
    kol_jam = kol_total + 1 if lengkap else None
    kol_persen = (kol_jam or kol_total) + 1
    kol_akhir = kol_persen

    # --- judul ---
    for r, teks in enumerate(judul, 1):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=kol_akhir)
        sel = ws.cell(r, 1, teks)
        sel.font = Font(bold=True, size=13.5)
        sel.alignment = Alignment(horizontal="center", vertical="center")

    baris_meta = len(judul) + 2
    for i, teks in enumerate(meta):
        ws.cell(baris_meta + i, 1, teks).font = Font(bold=True, size=12)

    # --- header empat tingkat ---
    h0 = baris_meta + len(meta) + 1
    h1, h2, h3 = h0 + 1, h0 + 2, h0 + 3

    for kol, teks in ((1, "No."), (2, "NIM"), (3, "Nama")):
        ws.merge_cells(start_row=h0, start_column=kol, end_row=h3, end_column=kol)
        ws.cell(h0, kol, teks).font = Font(bold=True, size=9)

    for k, s in enumerate(sesi):
        c1 = KOLOM_MULAI + per_sesi * k
        c2 = c1 + per_sesi - 1
        for r, teks in (
            (h0, s["label_tanggal"]),
            (h1, s["nama"]),
            (h2, f"{s['jam_mulai']} - {s['jam_selesai']}"),
        ):
            if per_sesi > 1:
                ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
            ws.cell(r, c1, teks).font = Font(bold=True, size=8)
        for off, teks in enumerate(subkolom):
            ws.cell(h3, c1 + off, teks).font = Font(bold=True, size=8)

    ws.merge_cells(start_row=h0, start_column=kol_h, end_row=h2, end_column=kol_i)
    ws.cell(h0, kol_h, "Jumlah Kehadiran").font = Font(bold=True, size=8)
    for kol, huruf in ((kol_h, "H"), (kol_a, "A"), (kol_s, "S"), (kol_i, "I")):
        ws.cell(h3, kol, huruf).font = Font(bold=True, size=8)

    tegak = [(kol_total, "Total Kehadiran"), (kol_persen, "Persentasi (%)")]
    if lengkap:
        tegak.insert(1, (kol_jam, "Total Jam"))
    for kol, teks in tegak:
        ws.merge_cells(start_row=h0, start_column=kol, end_row=h3, end_column=kol)
        ws.cell(h0, kol, teks).font = Font(bold=True, size=8)

    for r in range(h0, h3 + 1):
        for c in range(1, kol_akhir + 1):
            sel = ws.cell(r, c)
            sel.alignment = TENGAH
            sel.border = KOTAK_TEBAL
            sel.fill = ARSIR_HEADER

    # --- isi ---
    L = get_column_letter
    r0 = h3 + 1
    for i, b in enumerate(baris):
        r = r0 + i
        ws.cell(r, 1, b["no"]).alignment = TENGAH
        ws.cell(r, 2, b["nim"]).alignment = TENGAH
        ws.cell(r, 3, b["nama"]).alignment = KIRI

        kolom_durasi = []
        for k, sel_data in enumerate(b["sel"]):
            c1 = KOLOM_MULAI + per_sesi * k
            nilai = _nilai_sel(sel_data, bentuk)
            for off, isi in enumerate(nilai):
                sel = ws.cell(r, c1 + off, isi)
                sel.alignment = TENGAH
                if off == 0:
                    sel.font = Font(bold=True, size=8)
                    if isi == "A":
                        sel.fill = ARSIR_ALPA
            if lengkap:
                ws.cell(r, c1 + 3).number_format = "0.00"
                kolom_durasi.append(f"{L(c1 + 3)}{r}")

        rentang = f"{L(KOLOM_MULAI)}{r}:{L(kol_h - 1)}{r}"
        for kol, huruf in ((kol_h, "H"), (kol_a, "A"), (kol_s, "S"), (kol_i, "I")):
            ws.cell(r, kol, f'=COUNTIF({rentang},"{huruf}")')
        ws.cell(r, kol_total, f"={L(kol_h)}{r}+{L(kol_s)}{r}+{L(kol_i)}{r}")
        if lengkap:
            jam = ws.cell(r, kol_jam, f"=SUM({','.join(kolom_durasi)})" if kolom_durasi else 0)
            jam.number_format = "0.00"
        persen = ws.cell(r, kol_persen, f"={L(kol_total)}{r}/{n_sesi}" if n_sesi else 0)
        persen.number_format = "0%"

        for c in range(1, kol_akhir + 1):
            sel = ws.cell(r, c)
            sel.border = KOTAK_TIPIS
            if sel.font.size != 8:
                sel.font = Font(size=8)
            if c >= KOLOM_MULAI:
                sel.alignment = TENGAH

    # --- lebar kolom ---
    ws.column_dimensions["A"].width = 4.5
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 28
    lebar = (6, 8, 8, 7) if lengkap else (6, 8)
    for k in range(n_sesi):
        c1 = KOLOM_MULAI + per_sesi * k
        for off, w in enumerate(lebar):
            ws.column_dimensions[L(c1 + off)].width = w
    for kol in (kol_h, kol_a, kol_s, kol_i):
        ws.column_dimensions[L(kol)].width = 4.5
    ws.column_dimensions[L(kol_total)].width = 9
    if lengkap:
        ws.column_dimensions[L(kol_jam)].width = 9
    ws.column_dimensions[L(kol_persen)].width = 10
    ws.freeze_panes = ws.cell(r0, KOLOM_MULAI)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

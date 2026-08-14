"""Aplikasi web: ubah data mentah fingerprint menjadi rekap absensi siap pakai."""

import io
import os

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from core import parser, rekap, sesi as modul_sesi

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

JAM_MULAI_BAKU = "07.30"

# Aplikasi ini sengaja tidak menyimpan apa pun di server: log scan hasil
# pembacaan dikirim balik ke browser, lalu disertakan lagi pada tiap permintaan.
# Dengan begitu aplikasi tetap benar walau tiap request dilayani instance berbeda.


def _muat_log(data):
    return parser.dari_muatan(data.get("log"))


@app.route("/")
def beranda():
    return render_template("index.html")


@app.post("/api/unggah")
def unggah():
    berkas = request.files.getlist("berkas")
    if not berkas or all(f.filename == "" for f in berkas):
        return jsonify(error="Belum ada file yang dipilih."), 400

    isi = []
    for f in berkas:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in (".xls", ".xlsx"):
            return jsonify(error=f"Format {ext} tidak didukung. Gunakan .xls atau .xlsx."), 400
        isi.append(io.BytesIO(f.read()))

    try:
        log, format_terpakai = parser.gabung_mentah(isi)
    except parser.FormatTidakDikenali as e:
        return jsonify(error=str(e)), 400
    except Exception as e:  # noqa: BLE001 - tampilkan pesan apa adanya ke pengguna
        return jsonify(error=f"Gagal membaca file: {e}"), 400

    daftar_sesi = modul_sesi.deteksi_sesi(log, jam_mulai=JAM_MULAI_BAKU)
    peserta = (
        log.groupby("uid").nama.agg(lambda s: s.mode().iat[0]).reset_index().sort_values("uid")
    )
    jumlah_scan = log.groupby("uid").size()

    return jsonify(
        log=parser.ke_muatan(log),
        format=format_terpakai,
        jam_mulai_baku=JAM_MULAI_BAKU,
        ringkasan={
            "total_scan": int(len(log)),
            "jumlah_peserta": int(log.uid.nunique()),
            "tanggal_awal": log.tanggal.min().strftime("%d/%m/%Y"),
            "tanggal_akhir": log.tanggal.max().strftime("%d/%m/%Y"),
            "jumlah_hari_aktif": int(log.tanggal.nunique()),
        },
        sesi=daftar_sesi,
        peserta=[
            {
                "uid": int(r.uid),
                "nama": r.nama,
                "nim": "",
                "scan": int(jumlah_scan.get(r.uid, 0)),
            }
            for r in peserta.itertuples(index=False)
        ],
    )


@app.post("/api/deteksi-ulang")
def deteksi_ulang():
    data = request.get_json(force=True)
    try:
        log = _muat_log(data)
    except parser.FormatTidakDikenali as e:
        return jsonify(error=str(e)), 400
    try:
        daftar = modul_sesi.deteksi_sesi(
            log,
            jeda_menit=int(data.get("jeda", 45)),
            min_peserta=int(data.get("min_peserta", 4)),
            mode=data.get("mode", "harian"),
            jam_mulai=data.get("jam_mulai", JAM_MULAI_BAKU),
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(sesi=daftar)


@app.post("/api/roster-template")
def roster_template():
    data = request.get_json(force=True)
    try:
        log = _muat_log(data)
    except parser.FormatTidakDikenali as e:
        return jsonify(error=str(e)), 400

    peserta = log.groupby("uid").nama.agg(lambda s: s.mode().iat[0]).reset_index()
    peserta["nim"] = ""
    peserta["nama_lengkap"] = ""
    keluaran = peserta[["uid", "nama", "nim", "nama_lengkap"]].rename(
        columns={"nama": "nama_di_mesin"}
    )
    buf = io.BytesIO(keluaran.to_csv(index=False).encode("utf-8-sig"))
    return send_file(
        buf, mimetype="text/csv", as_attachment=True, download_name="template_roster.csv"
    )


@app.post("/api/unggah-roster")
def unggah_roster():
    f = request.files.get("berkas")
    if not f:
        return jsonify(error="File roster belum dipilih."), 400
    try:
        if f.filename.lower().endswith(".csv"):
            df = pd.read_csv(f, dtype=str)
        else:
            df = pd.read_excel(f, dtype=str)
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Gagal membaca roster: {e}"), 400

    df.columns = [str(c).strip().lower() for c in df.columns]
    if "uid" not in df.columns:
        return jsonify(error="Roster wajib punya kolom 'uid'."), 400

    kol_nama = next((c for c in ("nama_lengkap", "nama", "nama_di_mesin") if c in df.columns), None)
    hasil = []
    for d in df.to_dict("records"):
        try:
            uid = int(float(d["uid"]))
        except (TypeError, ValueError):
            continue
        nim = str(d.get("nim") or "").strip()
        nama = str(d.get(kol_nama) or "").strip() if kol_nama else ""
        hasil.append({"uid": uid, "nim": nim, "nama": nama})
    if not hasil:
        return jsonify(error="Roster tidak berisi baris yang valid."), 400
    return jsonify(peserta=hasil)


@app.post("/api/buat")
def buat():
    data = request.get_json(force=True)
    try:
        log = _muat_log(data)
    except parser.FormatTidakDikenali as e:
        return jsonify(error=str(e)), 400

    daftar_sesi = data.get("sesi") or []
    if not daftar_sesi:
        return jsonify(error="Belum ada sesi yang dipilih."), 400

    peserta = data.get("peserta") or []
    if not peserta:
        return jsonify(error="Daftar peserta kosong."), 400

    roster = pd.DataFrame(
        [
            {
                "uid": int(p["uid"]),
                "nim": p.get("nim") or "",
                "nama": p.get("nama") or "",
            }
            for p in peserta
        ]
    )

    override = pd.DataFrame(data.get("override") or [], columns=["uid", "sesi_ke", "status"])

    try:
        baris = rekap.susun_rekap(
            log,
            daftar_sesi,
            roster,
            toleransi_awal=int(data.get("toleransi_awal", 15)),
            toleransi_akhir=int(data.get("toleransi_akhir", 15)),
            override=override,
        )
        buf = rekap.tulis_xlsx(
            baris,
            daftar_sesi,
            judul=[b for b in (data.get("judul") or []) if b.strip()],
            meta=[b for b in (data.get("meta") or []) if b.strip()],
        )
    except ValueError as e:
        return jsonify(error=str(e)), 400

    nama_file = (data.get("nama_file") or "rekap-absensi").strip() or "rekap-absensi"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{nama_file}.xlsx",
    )


@app.post("/api/pratinjau")
def pratinjau():
    data = request.get_json(force=True)
    try:
        log = _muat_log(data)
    except parser.FormatTidakDikenali as e:
        return jsonify(error=str(e)), 400

    daftar_sesi = data.get("sesi") or []
    peserta = data.get("peserta") or []
    if not daftar_sesi or not peserta:
        return jsonify(baris=[], statistik={})

    roster = pd.DataFrame(
        [{"uid": int(p["uid"]), "nim": p.get("nim") or "", "nama": p.get("nama") or ""} for p in peserta]
    )
    override = pd.DataFrame(data.get("override") or [], columns=["uid", "sesi_ke", "status"])
    baris = rekap.susun_rekap(
        log,
        daftar_sesi,
        roster,
        toleransi_awal=int(data.get("toleransi_awal", 15)),
        toleransi_akhir=int(data.get("toleransi_akhir", 15)),
        override=override,
    )
    total_sel = len(baris) * len(daftar_sesi) or 1
    hadir = sum(1 for b in baris for s in b["sel"] if s[0] == "H")
    total_jam = sum(b["total_jam"] for b in baris)
    return jsonify(
        baris=baris[:200],
        statistik={
            "jumlah_baris": len(baris),
            "jumlah_sesi": len(daftar_sesi),
            "persen_hadir": round(100 * hadir / total_sel, 1),
            "rata_jam": round(total_jam / (len(baris) or 1), 2),
        },
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=False)

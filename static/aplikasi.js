const $ = (s) => document.querySelector(s);
const state = { log: null, sesi: [], peserta: [] };

/* ---------- utilitas ---------- */
function pesan(teks, jenis = "") {
  const el = document.createElement("div");
  el.className = "pesan " + jenis;
  el.textContent = teks;
  $("#notifikasi").append(el);
  setTimeout(() => el.remove(), 4200);
}

async function kirimJson(url, data) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "Terjadi kesalahan.");
  return r.json();
}

const tampil = (id) => $(id).classList.remove("sembunyi");

/* ---------- langkah 1: unggah ---------- */
const zona = $("#jatuhkan");
zona.onclick = () => $("#berkas").click();
zona.ondragover = (e) => { e.preventDefault(); zona.classList.add("aktif"); };
zona.ondragleave = () => zona.classList.remove("aktif");
zona.ondrop = (e) => {
  e.preventDefault();
  zona.classList.remove("aktif");
  unggah(e.dataTransfer.files);
};
$("#berkas").onchange = (e) => unggah(e.target.files);

async function unggah(daftar) {
  if (!daftar || !daftar.length) return;
  const fd = new FormData();
  for (const f of daftar) fd.append("berkas", f);
  zona.querySelector("p").innerHTML = "<b>Membaca file…</b>";
  try {
    const r = await fetch("/api/unggah", { method: "POST", body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Gagal membaca file.");

    state.log = d.log;
    state.sesi = d.sesi;
    state.peserta = d.peserta;
    if (d.jam_mulai_baku) $("#jamMulai").value = d.jam_mulai_baku;

    const s = d.ringkasan;
    $("#ringkasan").innerHTML = `
      <div><b>${s.total_scan.toLocaleString("id")}</b>total scan</div>
      <div><b>${s.jumlah_peserta}</b>peserta</div>
      <div><b>${s.jumlah_hari_aktif}</b>hari ada aktivitas</div>
      <div><b>${d.sesi.length}</b>sesi terdeteksi</div>
      <div><b style="font-size:14px">${s.tanggal_awal} – ${s.tanggal_akhir}</b>periode</div>`;
    $("#ringkasan").classList.remove("sembunyi");
    zona.querySelector("p").innerHTML = "<b>Klik di sini</b> atau seret file ke area ini";

    gambarSesi();
    gambarPeserta();
    ["#langkah2", "#langkah3", "#langkah4", "#langkah5"].forEach(tampil);
    pesan(`Berhasil membaca ${daftar.length} file (format: ${d.format.join(", ")}).`, "sukses");
  } catch (e) {
    zona.querySelector("p").innerHTML = "<b>Klik di sini</b> atau seret file ke area ini";
    pesan(e.message, "galat");
  }
}

/* ---------- langkah 2: sesi ---------- */
function gambarSesi() {
  const tb = $("#tabelSesi tbody");
  tb.innerHTML = "";
  state.sesi.forEach((s, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" ${s.aktif === false ? "" : "checked"} data-k="aktif"></td>
      <td><input type="date" value="${s.tanggal}" data-k="tanggal"></td>
      <td><input value="${s.nama || ""}" data-k="nama" placeholder="mis. PBL 1 (MODUL 1)"></td>
      <td><input class="sempit" value="${s.jam_mulai}" data-k="jam_mulai"></td>
      <td><input class="sempit" value="${s.jam_selesai}" data-k="jam_selesai"></td>
      <td style="color:var(--redup)">${s.jam_data || "-"}</td>
      <td style="color:var(--redup)">${s.peserta ?? "-"} orang</td>
      <td><button class="hapus" title="Hapus sesi">&times;</button></td>`;
    tr.querySelectorAll("input").forEach((inp) => {
      inp.oninput = () => {
        const k = inp.dataset.k;
        state.sesi[i][k] = inp.type === "checkbox" ? inp.checked : inp.value;
        if (k === "tanggal") state.sesi[i].label_tanggal = null;
      };
    });
    tr.querySelector(".hapus").onclick = () => {
      state.sesi.splice(i, 1);
      gambarSesi();
    };
    tb.append(tr);
  });
}

$("#deteksiUlang").onclick = async () => {
  try {
    const d = await kirimJson("/api/deteksi-ulang", {
      log: state.log,
      jeda: +$("#jeda").value,
      min_peserta: +$("#minPeserta").value,
      mode: $("#mode").value,
      jam_mulai: $("#jamMulai").value,
    });
    state.sesi = d.sesi;
    gambarSesi();
    pesan(`${d.sesi.length} sesi terdeteksi.`, "sukses");
  } catch (e) { pesan(e.message, "galat"); }
};

$("#tambahSesi").onclick = () => {
  const acuan = state.sesi[state.sesi.length - 1];
  state.sesi.push({
    tanggal: acuan ? acuan.tanggal : new Date().toISOString().slice(0, 10),
    nama: `SESI ${state.sesi.length + 1}`,
    jam_mulai: $("#jamMulai").value || "07.30",
    jam_selesai: "09.05", jam_data: null, peserta: null, aktif: true,
  });
  gambarSesi();
};

/* ---------- langkah 3: peserta ---------- */
function gambarPeserta() {
  const tb = $("#tabelPeserta tbody");
  const sembunyi = $("#sembunyikanTanpaNim").checked;
  tb.innerHTML = "";
  state.peserta.forEach((p, i) => {
    if (sembunyi && !p.nim) return;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" ${p.aktif === false ? "" : "checked"} data-k="aktif"></td>
      <td style="color:var(--redup)">${p.uid}</td>
      <td>${p.nama_mesin || p.nama || ""}</td>
      <td><input value="${p.nim || ""}" data-k="nim" placeholder="C011241006"></td>
      <td><input value="${p.nama || ""}" data-k="nama"></td>
      <td style="color:var(--redup)">${p.scan ?? "-"}</td>
      <td><button class="hapus" title="Hapus peserta">&times;</button></td>`;
    tr.querySelectorAll("input").forEach((inp) => {
      inp.oninput = () => {
        state.peserta[i][inp.dataset.k] = inp.type === "checkbox" ? inp.checked : inp.value;
      };
    });
    tr.querySelector(".hapus").onclick = () => {
      state.peserta.splice(i, 1);
      gambarPeserta();
    };
    tb.append(tr);
  });
}
$("#sembunyikanTanpaNim").onchange = gambarPeserta;

$("#unduhTemplate").onclick = async () => {
  const r = await fetch("/api/roster-template", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ log: state.log }),
  });
  if (!r.ok) return pesan("Gagal membuat template.", "galat");
  simpanBlob(await r.blob(), "template_roster.csv");
};

$("#pilihRoster").onclick = () => $("#berkasRoster").click();
$("#berkasRoster").onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const fd = new FormData();
  fd.append("berkas", f);
  const r = await fetch("/api/unggah-roster", { method: "POST", body: fd });
  const d = await r.json();
  if (!r.ok) return pesan(d.error, "galat");

  const peta = new Map(d.peserta.map((p) => [p.uid, p]));
  let cocok = 0;
  state.peserta.forEach((p) => {
    const m = peta.get(p.uid);
    if (!m) return;
    cocok++;
    p.nama_mesin = p.nama_mesin || p.nama;
    if (m.nim) p.nim = m.nim;
    if (m.nama) p.nama = m.nama;
  });
  gambarPeserta();
  pesan(`${cocok} peserta diperbarui dari roster.`, "sukses");
};

/* ---------- langkah 5: pratinjau & unduh ---------- */
function muatan() {
  return {
    log: state.log,
    sesi: state.sesi.filter((s) => s.aktif !== false),
    peserta: state.peserta.filter((p) => p.aktif !== false),
    toleransi_awal: +$("#tolAwal").value,
    toleransi_akhir: +$("#tolAkhir").value,
    judul: [$("#judul1").value, $("#judul2").value, $("#judul3").value],
    meta: [$("#meta1").value, $("#meta2").value],
    nama_file: $("#namaFile").value,
  };
}

$("#pratinjau").onclick = async () => {
  try {
    const d = await kirimJson("/api/pratinjau", muatan());
    const sesi = muatan().sesi;
    const kepala = sesi
      .map((s) => `<th colspan="4">${s.nama || "SESI"}<br><span class="kecil">${s.tanggal} &middot; ${s.jam_mulai}-${s.jam_selesai}</span></th>`)
      .join("");
    const subkepala = sesi
      .map(() => `<th>Status</th><th>Ceklog 1</th><th>Ceklog 2</th><th>Durasi</th>`)
      .join("");
    const badan = d.baris
      .map(
        (b) =>
          `<tr><td>${b.no}</td><td>${b.nim}</td><td>${b.nama}</td>` +
          b.sel
            .map(([st, c1, c2, dur]) =>
              `<td class="sel-${st}">${st}</td><td>${c1}</td><td>${c2}</td>` +
              `<td>${dur === null ? "-" : dur.toFixed(2)}</td>`)
            .join("") +
          `<td class="tebal">${(b.total_jam ?? 0).toFixed(2)}</td></tr>`
      )
      .join("");
    $("#wadahPratinjau").innerHTML =
      `<table><thead>` +
      `<tr><th rowspan="2">No</th><th rowspan="2">NIM</th><th rowspan="2">Nama</th>${kepala}` +
      `<th rowspan="2">Total Jam</th></tr><tr>${subkepala}</tr></thead><tbody>${badan}</tbody></table>`;
    const s = d.statistik;
    $("#statistik").textContent =
      `${s.jumlah_baris} peserta × ${s.jumlah_sesi} sesi — kehadiran ${s.persen_hadir}%` +
      `, rata-rata ${s.rata_jam} jam/orang` +
      (d.baris.length < s.jumlah_baris ? ` (pratinjau ${d.baris.length} baris pertama)` : "");
  } catch (e) { pesan(e.message, "galat"); }
};

$("#unduh").onclick = async () => {
  const data = muatan();
  if (!data.sesi.length) return pesan("Pilih minimal satu sesi.", "galat");
  if (!data.peserta.length) return pesan("Daftar peserta kosong.", "galat");
  const r = await fetch("/api/buat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) return pesan((await r.json()).error || "Gagal membuat file.", "galat");
  simpanBlob(await r.blob(), `${data.nama_file}.xlsx`);
  pesan("Berhasil dibuat.", "sukses");
};

function simpanBlob(blob, nama) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nama;
  a.click();
  URL.revokeObjectURL(url);
}

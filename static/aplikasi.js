// Formulir sakit/izin: tawarkan sesi yang benar-benar ada pada tanggal terpilih.
(function () {
  const mhs = document.querySelector("#pilihMahasiswa");
  const tgl = document.querySelector("#pilihTanggal");
  const sesi = document.querySelector("#pilihSesi");
  if (!mhs || !tgl || !sesi) return;

  async function muat() {
    if (!tgl.value) return;
    const url = `/ketidakhadiran/sesi-pada-tanggal?tanggal=${tgl.value}&mahasiswa_id=${mhs.value || ""}`;
    try {
      const r = await fetch(url);
      const d = await r.json();
      sesi.innerHTML =
        '<option value="">seluruh sesi hari itu</option>' +
        d.sesi.map((s) => `<option value="${s.id}">${s.label}</option>`).join("");
    } catch (e) {
      /* biarkan pilihan apa adanya bila gagal */
    }
  }
  tgl.addEventListener("change", muat);
  mhs.addEventListener("change", muat);
})();

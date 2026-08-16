#!/bin/sh
# Titik masuk wadah. Berjalan sebagai root hanya untuk membereskan kepemilikan
# /data, lalu menurunkan hak ke pengguna aplikasi sebelum menjalankan gunicorn.
#
# Alasannya: berkas yang masuk ke volume dari luar - lewat `docker compose cp`
# atau bind mount - membawa UID mesin asal, biasanya bukan 1000. Akibatnya
# aplikasi masih bisa membaca sehingga tampak sehat, tetapi setiap penyimpanan
# gagal dengan "attempt to write a readonly database". Lebih baik dibereskan
# sekali saat start daripada menunggu admin menemukannya sendiri di produksi.
set -e

if [ "$(id -u)" = "0" ]; then
    chown -R aplikasi:aplikasi /data 2>/dev/null || true
    exec setpriv --reuid=aplikasi --regid=aplikasi --init-groups "$@"
fi

exec "$@"

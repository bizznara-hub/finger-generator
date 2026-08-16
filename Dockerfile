# Dua tahap: Node hanya dipakai membangun antarmuka, tidak ikut ke citra akhir.
# Hasilnya citra Python berisi Flask plus web/dist yang sudah jadi.

# ---------- tahap 1: bangun antarmuka Vue ----------
FROM node:22-alpine AS antarmuka
WORKDIR /web

# package.json disalin lebih dulu supaya lapisan npm ci ikut ter-cache
# selama daftar dependensinya tidak berubah.
COPY web/package.json web/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY web/ ./
RUN npm run build


# ---------- tahap 2: aplikasi Flask ----------
FROM python:3.12-slim AS aplikasi

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py seed.py ./
COPY masuk-wadah.sh /usr/local/bin/masuk-wadah
COPY api/ ./api/
COPY core/ ./core/
COPY --from=antarmuka /web/dist ./web/dist

# Basis data SQLite ditaruh di /data agar bisa dipasangi volume dan selamat
# dari pembangunan ulang citra. Diabaikan bila DATABASE_URL menunjuk Postgres.
# --create-home wajib: control server gunicorn menulis ke $HOME saat start, dan
# tanpa direktori itu ia menggagalkan diri dengan "Permission denied".
RUN mkdir -p /data \
    && useradd --system --uid 1000 --create-home --home-dir /home/aplikasi aplikasi \
    && chown -R aplikasi /data /app \
    && chmod +x /usr/local/bin/masuk-wadah

# Tetap root di sini; masuk-wadah yang menurunkan hak ke pengguna aplikasi
# setelah kepemilikan /data dibereskan.
ENTRYPOINT ["masuk-wadah"]

ENV DATABASE_URL=sqlite:////data/data.db
EXPOSE 5057

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5057/api/status', timeout=4).status < 500 else 1)"

# --preload memuat aplikasi sekali di proses induk, sehingga db.create_all()
# dan pembuatan akun awal tidak dijalankan bersamaan oleh beberapa worker.
CMD ["gunicorn", "--bind", "0.0.0.0:5057", "--workers", "3", "--timeout", "120", "--preload", "app:app"]

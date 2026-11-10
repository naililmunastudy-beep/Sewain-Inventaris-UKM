# Sewain — Sistem Penyewaan Inventaris UKM

Aplikasi berbasis Streamlit untuk mencatat inventaris, kategori, mahasiswa/penyewa, penyewaan, pengembalian, dan laporan.

## Menjalankan di VS Code

1. Ekstrak ZIP ini.
2. Buka folder `Sewain-main` di VS Code, yaitu folder yang langsung berisi
   `app.py`, `core/`, dan `views/`. Jangan membuka folder induknya.
3. Pastikan Python 3.10+ terpasang.
4. Buka Terminal di VS Code, lalu jalankan:

   ```bash
   python -m venv sewainvenv
   ```

   Aktifkan environment:
   - Windows PowerShell: `.\sewainvenv\Scripts\Activate.ps1`
   - Windows CMD: `sewainvenv\Scripts\activate.bat`
   - macOS/Linux: `source sewainvenv/bin/activate`

5. Instal dependensi:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Jalankan aplikasi:

   ```bash
   streamlit run app.py
   ```

   Jika terminal berada di folder induk `Sewain`, masuk dahulu ke folder proyek:

   ```powershell
   Set-Location .\Sewain-main
   .\sewainvenv\Scripts\Activate.ps1
   streamlit run app.py
   ```

Di VS Code, buka terminal baru setelah folder proyek dibuka. Workspace akan memilih `sewainvenv` dan mengaktifkannya otomatis, sehingga perintah `streamlit` tersedia. Jika terminal yang sedang terbuka belum mengaktifkan environment, jalankan aktivasi secara manual:

```powershell
.\sewainvenv\Scripts\Activate.ps1
```

Aplikasi akan terbuka di browser. Pengaturan otomatis ini berlaku untuk terminal terintegrasi VS Code; di terminal lain, aktifkan `sewainvenv` terlebih dahulu.

Aplikasi langsung membuka Dashboard. Database SQLite berada di `core/sewain.db` dan dibuat otomatis dari data contoh jika belum tersedia.

Halaman Pengembalian mencatat tanggal kembali aktual dan kondisi setiap barang. Keterlambatan dikenai denda Rp1.500 per hari; lama keterlambatan, tarif, dan total denda disimpan bersama riwayat pengembalian.

## Deploy ke Streamlit Community Cloud

1. Buat repositori GitHub baru, lalu unggah folder proyek ini. Jangan unggah
   `sewainvenv`; folder tersebut sudah dicantumkan di `.gitignore`.
2. Buka <https://share.streamlit.io>, masuk dengan GitHub, lalu pilih
   **Create app**.
3. Pilih repositori dan cabang GitHub proyek, isi:
   - **Main file path:** `app.py`
   - **App URL:** pilih nama aplikasi yang tersedia
4. Pilih **Deploy**. Streamlit akan memasang dependency dari `requirements.txt`.

Database SQLite tidak dipakai sebagai penyimpanan produksi permanen pada
Streamlit Community Cloud. Perubahan data dapat hilang ketika aplikasi direstart
atau container dibuat ulang. Untuk demo, aplikasi membuat database baru secara
otomatis dari data contoh. Untuk penggunaan produksi, gunakan hosting dengan
volume disk persisten atau pindahkan penyimpanan ke database eksternal seperti
PostgreSQL.

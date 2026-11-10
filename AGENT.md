# AGENT INSTRUCTIONS — SEWAIN SYSTEM

Dokumen ini adalah aturan dasar buat AI Agent dalam mengembangkan dan merawat aplikasi Sewain.

## 1. Identitas Sistem
- Nama Aplikasi: Sewain (Sistem Penyewaan Inventaris UKM).
- Bahasa Tampilan: Bahasa Indonesia baku (Penyewaan, Pengembalian, Inventaris, Riwayat, Laporan).

## 2. Tech Stack & Environment
- Framework: Python & Streamlit.
- Virtual Environment: Wajib pakai `sewainvenv`.
- UI Styling: Pakai custom CSS (header tabel rata tengah, tanpa background gelap di header).

## 3. Database
- Database Engine: SQLite (`sewain.db`) di dalam folder `core/`.
- Menggunakan modul `sqlite3` bawaan Python untuk menyimpan data barang, peminjam, transaksi penyewaan, dan pengembalian.

## 4. Akses Pengguna
- Tanpa Halaman Login (No Login Page).
- Single User / Single Role (Langsung masuk ke aplikasi utama).

## 5. Acuan Perancangan
- Seluruh alur dan fitur merujuk pada dokumen PDF perancangan di folder project.

## 6. Aturan Tampilan Tabel (UI Rules)
- Judul kolom wajib KAPITAL (UPPERCASE).
- Posisi Tengah (Center): Kode barang/transaksi, tanggal sewa/kembali, dan status.
- Posisi Kiri (Left): Nama barang, nama peminjam, kategori, dan catatan.

## 7. Aturan Pengembalian & Denda
- Denda keterlambatan: Rp1.500 per hari (konstanta `DENDA_PER_HARI` di `core/utils.py`).
- Terlambat = status Disewa dan tanggal kembali aktual melebihi tanggal rencana kembali; tepat di tanggal rencana belum dikenai denda.
- Pengembalian dicatat pada tabel `pengembalian` (1 transaksi maksimal 1 catatan), lengkap dengan tanggal kembali aktual, lama terlambat, dan total denda yang disalin saat diproses.
- Kondisi barang dicatat per barang pada `detail_peminjaman.kondisi_barang`.
- Pengembalian sebagian dan riwayat mutasi stok belum didukung.

# Tycoon Empire

Game tycoon berbasis browser, tanpa proses build dan tanpa dependensi JavaScript tambahan.

## Menjalankan game

1. Buka `index.html` langsung di browser modern.
2. Progres disimpan otomatis ke `localStorage` setiap 15 detik, setelah aksi penting, dan saat halaman ditinggalkan.
3. Gunakan tombol **Simpan** untuk menyimpan kapan saja atau **Game Baru** untuk reset.

Koneksi internet hanya diperlukan untuk memuat font dan ikon eksternal; mekanik game tetap berjalan jika aset CDN tidak tersedia.

## Siklus permainan

- **Akhiri Hari** menjalankan produksi, penjualan otomatis, biaya operasional, pasar, bunga utang, dan event risiko.
- **Pasar** memungkinkan penjualan stok manual dan pengaturan harga jual otomatis.
- **Bisnis** membeli fasilitas; **Produksi** meningkatkan output; **Riset** membuka bonus permanen.
- **Keuangan** menampilkan transaksi dan pembayaran utang.
- Menangkan permainan dengan mencapai valuasi **US$180.000** dalam 150 hari.
- Perusahaan pailit jika kas negatif selama dua hari berturut-turut; gagal mencapai target sampai tenggat juga mengakhiri permainan.

## Verifikasi

`test_game.py` adalah smoke/regression test berbasis Playwright. Test mencakup startup, semua tab, validasi harga, tick harian, save/load, payload XSS pada save, simulasi strategi dari awal sampai menang, kondisi pailit, batas waktu, dan layout mobile 360 px serta 320 px.

Test membutuhkan Python dengan paket `playwright` dan browser Chromium. Dependensi tersebut hanya untuk pengujian, bukan untuk menjalankan game.

```bash
python test_game.py
```

## Struktur

- `index.html` — aplikasi lengkap (HTML, CSS, JavaScript) agar dapat dibuka langsung.
- `test_game.py` — pengujian browser otomatis.

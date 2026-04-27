# 🌸 Panduan Teknis Syaqila (Dashboard & Home)

Halo Syaqila! Sesuai dengan desain (mockup) terbaru, tugasmu adalah membangun **Dashboard Utama** yang terlihat cantik dan interaktif.

## 🎯 Target Tampilan (Dashboard):
1. **Bagian Atas (Ringkasan Data):** 4 kotak putih (kartu) berisi angka besar (Total produk, Jumlah merek, dll).
2. **Bagian Tengah (Pilih Kategori):** 5 tombol kotak bergambar ikon (Serum, Moisturizer, dll) sejajar ke samping.
3. **Bagian Bawah Kiri (Produk Terakhir Dilihat):** Daftar 3 produk yang tersusun ke bawah.
4. **Bagian Bawah Kanan (Rating per tipe kulit):** Grafik batang horizontal sederhana.

---

## 🛠 Panduan & Kode Contoh untuk Misi Kamu

Berikut adalah kerangka kode (*boilerplate*) yang bisa kamu jadikan *copy-paste* di dalam file `home_page.py`. Kamu tinggal menyesuaikan isi teks dan logikanya!

### 1. Membuat 4 Kartu Ringkasan Data
Gunakan `ui.row()` agar berjajar ke samping, dan `ui.card()` untuk tiap kotaknya.

```python
ui.label('RINGKASAN DATA').classes('text-sm font-bold text-gray-500 mb-2')
with ui.row().classes('w-full gap-4 mb-8'):
    # Kartu 1
    with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
        ui.label('Total produk').classes('text-xs text-gray-500')
        ui.label('312').classes('text-3xl font-black')
        ui.label('dari 3 sumber').classes('text-xs text-green-500')
    
    # Kartu 2
    with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
        ui.label('Jumlah merek').classes('text-xs text-gray-500')
        ui.label('48').classes('text-3xl font-black')
        ui.label('lokal & internasional').classes('text-xs text-green-500')
    
    # (Lanjutkan buat Kartu 3 dan 4 sendiri ya!)
```

### 2. Membuat Tombol Kategori
Kita buat berjajar lagi dengan `ui.row()`. Jika tombol sedang aktif (misal Serum), kita beri warna *background* pink.

```python
ui.label('PILIH KATEGORI').classes('text-sm font-bold text-gray-500 mb-2')
with ui.row().classes('w-full gap-4 mb-8'):
    # Contoh Kategori Aktif (Pink)
    with ui.card().classes('w-24 items-center cursor-pointer bg-pink-50 border border-pink-200'):
        ui.label('💧').classes('text-2xl') # Ikon emoji
        ui.label('Serum').classes('text-xs text-pink-500 font-bold')
        
    # Contoh Kategori Tidak Aktif (Putih)
    with ui.card().classes('w-24 items-center cursor-pointer'):
        ui.label('🧴').classes('text-2xl')
        ui.label('Moisturizer').classes('text-xs text-gray-500')
```

### 3. Membuat Daftar Produk (Kiri) & Grafik (Kanan)
Kita bagi layar menjadi 2 kolom menggunakan `ui.row()` dan `flex` system.

```python
with ui.row().classes('w-full gap-8 items-stretch'):
    
    # KOLOM KIRI (Produk Terakhir)
    with ui.card().classes('flex-[2] p-6 shadow-sm'):
        ui.label('Produk terakhir dilihat').classes('font-bold mb-4')
        # Produk 1
        with ui.row().classes('w-full items-center justify-between border-b pb-2'):
            ui.label('💧').classes('text-3xl bg-pink-50 rounded-lg p-2')
            with ui.column().classes('gap-0 flex-1 ml-4'):
                ui.label('Niacinamide 10% + Zinc 1%').classes('font-bold text-sm')
                ui.label('The Ordinary').classes('text-xs text-gray-500')
            with ui.column().classes('items-end gap-0'):
                ui.label('Rp145k').classes('text-pink-500 font-bold text-sm')
                ui.label('★★★★★').classes('text-yellow-400 text-xs')
                
    # KOLOM KANAN (Grafik Tipe Kulit)
    with ui.card().classes('flex-1 p-6 shadow-sm'):
        ui.label('Rating per tipe kulit (Serum)').classes('font-bold mb-4')
        # Baris Oily
        with ui.row().classes('w-full items-center justify-between mb-2'):
            ui.label('Oily').classes('text-sm text-gray-600 w-20')
            ui.linear_progress(value=0.88, color='pink').classes('w-20') # 4.4 dari 5 = 88%
            ui.label('4.4').classes('text-sm font-bold')
```

**Misi Syaqila:** Silakan rangkai kode-kode di atas ke dalam file `home_page.py` milikmu. Selamat mencoba!


## 🎨 Ingin Membuat Desain Sendiri?
Jika kamu memiliki ide desain yang lebih bagus, kamu **SANGAT DIPERBOLEHKAN** untuk membuat desainmu sendiri dan tidak harus mengikuti contoh di atas! Silakan bereksperimen dengan berbagai komponen NiceGUI sebebas mungkin.

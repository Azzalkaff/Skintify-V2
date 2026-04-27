# 🔍 Panduan Teknis Syahid (Cari Produk)

Halo Syahid! Tugas utamamu adalah merombak halaman **Cari Produk** agar sesuai dengan desain (mockup) terbaru yang lebih elegan.

## 🎯 Target Tampilan:
1. **Pencarian & Filter (Kiri/Atas):** Ada *Search Bar* (Input) dan 4 buah pilihan Dropdown (Kategori, Tipe Kulit, Harga, Urutkan).
2. **Katalog Produk (Bawah/Kanan):** Teks "12 PRODUK DITEMUKAN" dan kumpulan kartu produk berjejer rapi (Grid). Tiap kartu memiliki nama, harga, rating, dan dua tombol ("Detail" dan "+ Wishlist").

---

## 🛠 Panduan & Kode Contoh untuk Misi Kamu

Berikut adalah kerangka kode (*boilerplate*) yang bisa kamu letakkan di file `search_page.py`. Kamu tinggal memodifikasi dan menyambungkannya dengan data sungguhan!

### 1. Membuat Form Filter (Search Bar & Dropdowns)
Gunakan `ui.column()` agar inputannya tersusun rapi ke bawah.

```python
with ui.card().classes('w-full p-4 shadow-sm mb-6'):
    # Kotak Pencarian
    with ui.row().classes('w-full gap-2 items-center'):
        pencarian = ui.input(placeholder='hydrating').classes('flex-1')
        ui.button('Cari', color='white', text_color='black').classes('border')
    
    # 4 Dropdown Filter
    kategori = ui.select(['Moisturizer', 'Serum', 'Toner'], value='Moisturizer').classes('w-full mt-2')
    tipe_kulit = ui.select(['Dry', 'Oily', 'Normal'], value='Dry').classes('w-full mt-2')
    harga = ui.select(['Harga: < Rp200k', 'Harga: > Rp200k'], value='Harga: < Rp200k').classes('w-full mt-2')
    urutkan = ui.select(['Urutkan: Rating', 'Urutkan: Harga Terendah'], value='Urutkan: Rating').classes('w-full mt-2')
```

### 2. Membuat Katalog Kartu Produk (Grid)
Gunakan `ui.grid(columns=3)` agar produk tampil sejajar 3 kotak, lalu ke baris bawahnya.

```python
ui.label('12 PRODUK DITEMUKAN').classes('text-xs font-bold text-gray-500 mb-4')

with ui.grid(columns=3).classes('w-full gap-6'):
    
    # --- KARTU PRODUK 1 ---
    with ui.card().classes('p-4 shadow-sm hover:shadow-md items-center'):
        # Gambar Placeholder (Atas)
        with ui.column().classes('w-full h-32 bg-pink-50 rounded-lg items-center justify-center mb-4'):
            ui.label('💧').classes('text-5xl') # Ganti dengan ui.image() nanti
            
        # Info Produk
        ui.label('Niacinamide 10% + Zinc').classes('font-bold text-sm text-center line-clamp-1')
        ui.label('The Ordinary').classes('text-xs text-gray-500 mb-2')
        ui.label('Rp145.000').classes('text-pink-500 font-bold')
        ui.label('★★★★★ 4.9').classes('text-yellow-400 text-xs font-bold mb-4')
        
        # Tombol Aksi (Detail & Wishlist)
        with ui.row().classes('w-full gap-2'):
            ui.button('Detail', color='white', text_color='black').classes('flex-1 border text-xs')
            ui.button('+ Wishlist', color='white', text_color='black').classes('flex-1 border text-xs')
            
    # Copy paste Kartu Produk 1 untuk membuat kartu lainnya!
```

**Misi Syahid:** Tuliskan dan bereksperimen dengan kode di atas ke dalam file `search_page.py`. Pastikan kamu meng-import NiceGUI (`from nicegui import ui`) ya! Semangat!


## 🎨 Ingin Membuat Desain Sendiri?
Jika kamu memiliki ide desain yang lebih bagus, kamu **SANGAT DIPERBOLEHKAN** untuk membuat desainmu sendiri dan tidak harus mengikuti contoh di atas! Silakan bereksperimen dengan berbagai komponen NiceGUI sebebas mungkin.

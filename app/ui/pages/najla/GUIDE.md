# 📊 Panduan Teknis Najla (Bandingkan & Statistik)

Halo Najla! Sesuai desain (mockup) terbaru, kamu harus membuat 2 halaman yang menantang namun sangat memukau secara visual.

## 🎯 Target Tampilan:
1. **Halaman Statistik:** Memiliki 2 *dropdown* kontrol di atas. Di bawahnya terdapat 3 jenis grafik: *Bar Chart* warna pink, *Scatter Plot* (Titik-titik), dan *Pie Chart*.
2. **Halaman Bandingkan:** Terdapat 3 *dropdown* untuk memilih produk. Di bawahnya, terdapat layout menyerupai **Matriks/Tabel** di mana kolom pertama adalah spesifikasi (Harga, Volume, Rating), dan kolom sebelahnya adalah produk yang dibandingkan (lengkap dengan gambar).

---

## 🛠 Panduan & Kode Contoh

### 1. Halaman Statistik (`stats_page.py`)
Kita akan menggunakan library bawaan NiceGUI `ui.chart` (berbasis Highcharts) untuk menampilkan visualisasi data.

```python
with ui.row().classes('w-full gap-8'):
    # GRAFIK 1: Bar Chart (Rata-rata harga per kategori)
    with ui.card().classes('flex-1 p-4 shadow-sm'):
        ui.label('Rata-rata harga per kategori').classes('font-bold mb-4')
        ui.chart({
            'chart': {'type': 'column'},
            'title': {'text': None}, # Sembunyikan judul bawaan
            'xAxis': {'categories': ['Serum', 'Moist', 'Sunsc', 'Toner', 'Clean']},
            'yAxis': {'title': {'text': ''}},
            'series': [{'name': 'Harga', 'data': [150, 120, 90, 80, 75], 'color': '#fbcfe8'}], # Warna Pink
            'legend': {'enabled': False} # Sembunyikan legenda
        }).classes('w-full h-64')

    # GRAFIK 2: Scatter Plot (Harga vs Rating)
    with ui.card().classes('flex-1 p-4 shadow-sm'):
        ui.label('Scatter: harga vs rating').classes('font-bold mb-4')
        ui.chart({
            'chart': {'type': 'scatter'},
            'title': {'text': None},
            'xAxis': {'title': {'text': 'Harga (Rp)'}},
            'yAxis': {'title': {'text': 'Rating'}},
            'series': [{
                'name': 'Produk',
                'data': [[50000, 4.2], [150000, 4.8], [200000, 4.5], [80000, 3.9], [120000, 4.6]],
                'color': '#f472b6' # Pink Tua
            }]
        }).classes('w-full h-64')
```

### 2. Halaman Bandingkan (`compare_page.py`)
Karena `ui.table()` standar tidak mengizinkan kita menaruh gambar dan tombol besar dengan mudah, kita akan **"Membangun Tabel Palsu"** menggunakan kombinasi `ui.grid` dan garis pembatas (`border`).

```python
# Tiga Dropdown Pemilih Produk
with ui.row().classes('w-full gap-4 mb-8'):
    ui.select(['Niacinamide 10%'], value='Niacinamide 10%').classes('flex-1')
    ui.select(['Niacinamide Toner 5%'], value='Niacinamide Toner 5%').classes('flex-1')
    ui.select(['Pilih Produk...']).classes('flex-1')

# Membuat "Tabel" Kustom dengan Grid 4 Kolom
with ui.card().classes('w-full p-0 shadow-sm'):
    with ui.grid(columns=4).classes('w-full items-center p-4 gap-0'):
        
        # --- BARIS HEADER (Gambar Produk) ---
        ui.label('').classes('p-4') # Kosong untuk pojok kiri atas
        
        # Produk 1
        with ui.column().classes('p-4 items-center border-l'):
            ui.label('💧').classes('text-4xl bg-pink-50 p-2 rounded')
            ui.label('Niacinamide 10%').classes('font-bold text-center mt-2')
            ui.label('The Ordinary').classes('text-xs text-gray-500')
            
        # Produk 2
        with ui.column().classes('p-4 items-center border-l'):
            ui.label('🧴').classes('text-4xl bg-pink-50 p-2 rounded')
            ui.label('Niacinamide Toner 5%').classes('font-bold text-center mt-2')
            ui.label('Wardah').classes('text-xs text-gray-500')
            
        # Placeholder Produk 3
        with ui.column().classes('p-4 items-center border-l h-full justify-center'):
            ui.button('+', color='gray-200', text_color='black').classes('text-2xl')
            ui.label('Tambah produk').classes('text-xs mt-2')

        # --- BARIS 1: HARGA ---
        # Gunakan border-t untuk membuat garis tabel
        ui.label('Harga').classes('p-4 border-t font-bold text-sm text-gray-600')
        ui.label('Rp145.000').classes('p-4 border-t border-l font-bold')
        ui.label('Rp89.000').classes('p-4 border-t border-l font-bold')
        ui.label('—').classes('p-4 border-t border-l text-gray-400')
        
        # --- BARIS 2: VOLUME ---
        ui.label('Volume').classes('p-4 border-t font-bold text-sm text-gray-600')
        ui.label('30 ml').classes('p-4 border-t border-l')
        ui.label('30 ml').classes('p-4 border-t border-l')
        ui.label('—').classes('p-4 border-t border-l text-gray-400')
```

**Misi Najla:** Gunakan kerangka kode di atas. Tantangannya adalah menampilkan data asli dari `state.routine` (rutinitas pengguna) ke dalam layout tersebut. Semangat!


## 🎨 Ingin Membuat Desain Sendiri?
Jika kamu memiliki ide desain yang lebih bagus, kamu **SANGAT DIPERBOLEHKAN** untuk membuat desainmu sendiri dan tidak harus mengikuti contoh di atas! Silakan bereksperimen dengan berbagai komponen NiceGUI sebebas mungkin.

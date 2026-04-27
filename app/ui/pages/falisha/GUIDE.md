# 👤 Panduan Teknis Falisha (Profil)

Halo Falisha! Sesuai dengan desain (mockup) terbaru, tugasmu adalah merangkai **Halaman Profil** yang terlihat modern dan rapi.

## 🎯 Target Tampilan:
1. **Kartu Utama (Atas):** Terdapat foto profil (Avatar) berbentuk bulat di tengah, disusul dengan Nama Lengkap dan gelar ("Pengguna Skintify"). Di bawahnya terdapat deretan "Badge" warna pink penanda identitas kulit (Kulit: Oily, Hindari: Alcohol).
2. **Data Profil (Bawah Kiri):** Sebuah kartu berisi tabel teks sederhana untuk Nama, Tipe Kulit, Bahan dihindari, dan *Range Harga*. Ada tombol "Edit Profil".
3. **Riwayat Aktivitas (Bawah Kanan):** Sebuah kartu berisi riwayat (*timeline*) yang dihiasi dengan titik warna-warni (pink, hijau) untuk menandakan aktivitas.

---

## 🛠 Panduan & Kode Contoh untuk Misi Kamu

Berikut adalah kerangka kode (*boilerplate*) yang bisa kamu jadikan acuan di file `profile_page.py` milikmu.

### 1. Kartu Identitas Utama (Atas)
Gunakan `ui.card()`, lalu posisikan item di tengah dengan `.classes('items-center')`.

```python
# Kartu Avatar & Nama
with ui.card().classes('w-full items-center p-8 shadow-sm mb-6'):
    # Avatar Bulat (Bisa pakai ikon bawaan)
    ui.icon('person', size='4rem').classes('bg-pink-100 text-indigo-900 rounded-full p-4 mb-4')
    
    # Nama dan Gelar
    ui.label('Falisha Reyhana').classes('text-2xl font-bold')
    ui.label('Pengguna Skintify').classes('text-sm text-gray-500 mb-4')
    
    # Deretan Badge Pink
    with ui.row().classes('gap-4'):
        ui.badge('Kulit: Oily', color='pink-100', text_color='pink-600').classes('px-4 py-2 font-bold')
        ui.badge('Hindari: Alcohol', color='pink-100', text_color='pink-600').classes('px-4 py-2 font-bold')
        ui.badge('Budget: <Rp200k', color='pink-100', text_color='pink-600').classes('px-4 py-2 font-bold')
```

### 2. Kartu Data Profil & Riwayat Aktivitas (Bawah)
Kita membagi layar jadi 2 kolom (kiri dan kanan) menggunakan `ui.row()` dengan sistem proporsi (menggunakan `flex-1`).

```python
with ui.row().classes('w-full gap-6 items-stretch'):
    
    # KARTU KIRI: Data Profil
    with ui.card().classes('flex-1 p-6 shadow-sm'):
        ui.label('Data profil').classes('font-bold text-lg mb-4')
        
        # Baris data (Label Kiri, Isi Kanan)
        with ui.row().classes('w-full justify-between mb-2'):
            ui.label('Nama').classes('text-gray-500')
            ui.label('Falisha Reyhana').classes('font-bold')
            
        with ui.row().classes('w-full justify-between mb-2'):
            ui.label('Tipe Kulit').classes('text-gray-500')
            ui.label('Oily').classes('font-bold')
            
        with ui.row().classes('w-full justify-between mb-4'):
            ui.label('Bahan dihindari').classes('text-gray-500')
            ui.label('Alcohol, Fragrance').classes('font-bold')
            
        # Tombol Edit
        ui.button('Edit profil', color='white', text_color='black').classes('border mt-4 px-6')

    # KARTU KANAN: Riwayat Aktivitas
    with ui.card().classes('flex-[1.5] p-6 shadow-sm'): # flex-[1.5] agar sedikit lebih lebar
        ui.label('Riwayat aktivitas').classes('font-bold text-lg mb-4')
        
        # Aktivitas 1 (Titik Pink)
        with ui.row().classes('w-full items-start mb-4 border-b pb-4'):
            ui.label('●').classes('text-pink-500 mr-2 mt-1')
            with ui.column().classes('gap-0'):
                ui.label('Membandingkan 2 produk').classes('font-bold')
                ui.label('The Ordinary vs Wardah • 2 jam lalu').classes('text-xs text-gray-500')

        # Aktivitas 2 (Titik Hijau)
        with ui.row().classes('w-full items-start mb-4 border-b pb-4'):
            ui.label('●').classes('text-green-500 mr-2 mt-1')
            with ui.column().classes('gap-0'):
                ui.label('Mencari "niacinamide"').classes('font-bold')
                ui.label('12 hasil ditemukan • 3 hari lalu').classes('text-xs text-gray-500')
```

**Misi Falisha:** Silakan *copy-paste* rancangan kode di atas ke dalam `profile_page.py`. Pastikan kamu mengatur letaknya agar rapi dan sesuai! Semangat!


## 🎨 Ingin Membuat Desain Sendiri?
Jika kamu memiliki ide desain yang lebih bagus, kamu **SANGAT DIPERBOLEHKAN** untuk membuat desainmu sendiri dan tidak harus mengikuti contoh di atas! Silakan bereksperimen dengan berbagai komponen NiceGUI sebebas mungkin.

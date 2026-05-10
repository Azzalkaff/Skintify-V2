from nicegui import ui
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager


def show_page():

    # --- JANGAN DIUBAH (Wajib untuk Navigasi) ---
    auth_redirect = AuthManager.require_auth()
    if auth_redirect: return auth_redirect
    UIComponents.navbar()
    UIComponents.sidebar()
    # -------------------------------------------

    if 'recent_products' not in state.__dict__:
        state.__dict__['recent_products'] = []

    data = data_mgr.get_paginated_products(page=1, items_per_page=1000, category_filter="All")
    products = data["items"]

    total_produk = len(products)

    brands = set(p.get("brand") for p in products if p.get("brand"))
    jumlah_merek = len(brands)

    rating_list = [
        p.get("rating") or p.get("average_rating") or 0
        for p in products
    ]

    rating_tertinggi = max(rating_list) if rating_list else 0

    produk_rating_tertinggi = (
        max(products, key=lambda x: x.get("rating") or 0)
        if products else {}
    )

    harga_termurah = (
        min((p.get("min_price") or 999999) for p in products)
        if products else 0
    )

    recent_products = state.__dict__.get('recent_products', [])

    # --- SET DEFAULT CATEGORY ---
    if not hasattr(state, 'category'):
        state.category = 'Serum'

    # --- FUNCTION PILIH KATEGORI ---
    def pilih_kategori(kategori):
        state.category = kategori
        state.page = 1   # reset halaman biar mulai dari awal
        ui.navigate.to('/search')   # pindah ke halaman search


    with ui.column().classes('w-full p-8'):

    # 📊 RINGKASAN DATA 
        ui.label('RINGKASAN DATA').classes('text-sm font-bold text-gray-500 mb-2')

        with ui.row().classes('w-full gap-4 mb-8'):

            # Total Produk
            with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
                ui.label('Total produk').classes('text-xs text-gray-500')
                ui.label(str(total_produk)).classes('text-3xl font-black')
                ui.label('dari database & scraping').classes('text-xs text-green-500')

            # Jumlah Merek
            with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
                ui.label('Jumlah merek').classes('text-xs text-gray-500')
                ui.label(str(jumlah_merek)).classes('text-3xl font-black')
                ui.label('lokal & internasional').classes('text-xs text-green-500')

            # Rating Tertinggi
            with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
                ui.label('Rating tertinggi').classes('text-xs text-gray-500')
                ui.label(f"{rating_tertinggi:.1f}").classes('text-3xl font-black')
                ui.label(
                    produk_rating_tertinggi.get("product_name", "-")
                ).classes('text-xs text-green-500')

            # Harga Termurah
            with ui.card().classes('flex-1 items-center justify-center p-4 shadow-sm'):
                ui.label('Harga terjangkau').classes('text-xs text-gray-500')
                ui.label(f"Rp{int(harga_termurah/1000)}k").classes('text-3xl font-black')
                ui.label('harga terendah').classes('text-xs text-green-500')


        # 🧴 PILIH KATEGORI 
        ui.label('PILIH KATEGORI').classes('text-sm font-bold text-gray-500 mb-2')

        with ui.row().classes('w-full justify-between gap-4 mb-8'):

            def card_kategori(nama, emoji):
                aktif = state.category == nama

                with ui.card().classes(
                    f'w-48 items-center cursor-pointer transition transform duration-150 '
                    f'active:scale-95 hover:shadow-md '
                    + ('bg-pink-50 border border-pink-200' if aktif else '')
                ).on('click', lambda: pilih_kategori(nama)):

                    ui.label(emoji).classes('text-2xl')
                    ui.label(nama).classes(
                        'text-xs font-bold text-pink-500'
                        if aktif else 'text-xs text-gray-500'
                    )

            # Daftar kategori
            card_kategori('Serum', '💧')
            card_kategori('Moisturizer', '🧴')
            card_kategori('Sunscreen', '☀️')
            card_kategori('Toner', '🌊')
            card_kategori('Cleanser', '🫧')

        with ui.row().classes('w-full gap-8 items-stretch'):
            
            # KOLOM KIRI (Produk Terakhir)
            with ui.card().classes('flex-[2] p-6 shadow-sm'):
                ui.label('Produk terakhir dilihat').classes('font-bold mb-4')

                for p in recent_products:
                    with ui.row().classes('w-full items-center justify-between border-b pb-2'):

                        with ui.element('div').classes('w-12 h-12 rounded-lg overflow-hidden bg-pink-50 flex items-center justify-center shrink-0'):
                            if p.get('image_url') and str(p.get('image_url')).startswith('http'):
                                ui.image(p['image_url']).classes('w-full h-full object-contain')
                            else:
                                icon_map = {'Serum': '💧', 'Moisturizer': '🧴', 'Toner': '🌊', 'Sunscreen': '☀️'}
                                cat_icon = icon_map.get(p.get('category', ''), '🧴')
                                ui.label(cat_icon).classes('text-xl')

                        with ui.column().classes('gap-0 flex-1 ml-4'):
                            ui.label(p.get("product_name", "-")).classes('font-bold text-sm')
                            ui.label(p.get("brand", "-")).classes('text-xs text-gray-500')

                        with ui.column().classes('items-end gap-0'):
                            ui.label(
                                f"Rp{int((p.get('min_price') or 0)/1000)}k"
                            ).classes('text-pink-500 font-bold text-sm')
                            ui.label(
                                f"{p.get('rating', 0):.1f}⭐"
                            ).classes('text-yellow-400 text-xs')
                        
            # KOLOM KANAN (Grafik Tipe Kulit)
            with ui.card().classes('flex-1 p-6 shadow-sm'):
                ui.label('Rating per tipe kulit (Serum)').classes('font-bold mb-4')
                # Baris Oily
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Oily').classes('text-sm text-gray-600 w-20')
                    ui.linear_progress(value=0.88, color='pink').classes('w-20') # 4.4 dari 5 = 88%
                    ui.label('4.4').classes('text-sm font-bold')

                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Dry').classes('text-sm text-gray-600 w-20')
                    ui.linear_progress(value=0.81, color='pink').classes('w-20') # 4.4 dari 5 = 80%
                    ui.label('4.1').classes('text-sm font-bold')

                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Combination').classes('text-sm text-gray-600 w-20')
                    ui.linear_progress(value=0.91, color='pink').classes('w-20') # 4.4 dari 5 = 80%
                    ui.label('4.5').classes('text-sm font-bold')

                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Sensitive').classes('text-sm text-gray-600 w-20')
                    ui.linear_progress(value=0.78, color='pink').classes('w-20') # 4.4 dari 5 = 80%
                    ui.label('3.7').classes('text-sm font-bold')

                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Normal').classes('text-sm text-gray-600 w-20')
                    ui.linear_progress(value=0.85, color='pink').classes('w-20') # 4.4 dari 5 = 80%
                    ui.label('4.3').classes('text-sm font-bold')


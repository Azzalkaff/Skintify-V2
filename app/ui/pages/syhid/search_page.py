from nicegui import ui
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager

def show_page():
    """Halaman Pencarian Produk (100% Selesai) - Dipegang oleh Syahid"""
    print("DEBUG: show_page() DIPANGGIL")  # ← tambah ini dulu
    
    if not hasattr(state, 'page'):
        state.page = 1

    auth_redirect = AuthManager.require_auth()
    if auth_redirect:
        print("DEBUG: redirect ke login")
        return auth_redirect
    
    print("DEBUG: auth passed")
    # 1. Proteksi Login
    auth_redirect = AuthManager.require_auth()
    if auth_redirect:
        return auth_redirect

    # 2. Refreshable Status Bar (Optional, jika ada)
    @ui.refreshable
    def taskbar_status() -> None:
        analysis = data_mgr.analyze_routine(state.routine, kota=state.kota)
        UIComponents.routine_status_badge(analysis)

    # 3. Layout Utama
    UIComponents.navbar(status_widget=taskbar_status)
    UIComponents.sidebar()

    with ui.row().classes('w-full max-w-[2000px] mx-auto items-stretch no-wrap mt-8 px-8 gap-8').style('min-height: calc(100vh - 120px);'):
        
        # Panel Kiri: Form Pencarian & Filter
        with ui.column().classes('w-64 flex-shrink-0 pt-4'):
            ui.label('Cari Produk').classes('text-2xl font-black text-gray-800 mb-6')
            
            with ui.card().classes('w-full p-4 shadow-sm bg-white'):
                # Kotak Pencarian
                search_input = ui.input(placeholder='Cari nama produk...').classes('w-full mb-4')
                
                # Dropdown Kategori
                # Asumsi data_mgr.categories berisi list kategori
                cats = ['Semua'] + list(set(
                    ['Serum', 'Moisturizer', 'Toner', 'Sunscreen', 'Cleanser'] +
                    (data_mgr.categories if hasattr(data_mgr, 'categories') else [])
                ))
                default_category = (
                    state.category
                    if hasattr(state, 'category') and state.category in cats
                    else 'Semua'
                )

                cat_select = ui.select(
                    cats,
                    value=default_category,
                    label='Kategori'
                ).classes('w-full mb-4')
                
                # Dropdown Tipe Kulit
                skin_types = ['Semua', 'Dry', 'Oily', 'Normal', 'Combination', 'Sensitive']
                skin_select = ui.select(skin_types, value='Semua', label='Tipe Kulit').classes('w-full mb-4')
                
                # Dropdown Harga
                price_ranges = ['Semua', '< Rp 50k', 'Rp 50k - Rp 150k', 'Rp 150k - Rp 300k', '> Rp 300k']
                price_select = ui.select(price_ranges, value='Semua', label='Range Harga').classes('w-full mb-4')
                
                # Dropdown Urutkan
                sort_options = ['Rating (Tertinggi)', 'Harga (Terendah)', 'Harga (Tertinggi)']
                sort_select = ui.select(sort_options, value='Rating (Tertinggi)', label='Urutkan').classes('w-full mb-6')
                
                def trigger_search(e=None):
                    state.page = 1
                    if hasattr(state, 'category'):
                        state.category = cat_select.value if cat_select.value != 'Semua' else None
                    catalog_view.refresh()

                # Event listeners
                search_input.on('keydown.enter', trigger_search)
                cat_select.on_value_change(trigger_search)
                skin_select.on_value_change(trigger_search)
                price_select.on_value_change(trigger_search)
                sort_select.on_value_change(trigger_search)
                
                ui.button('Terapkan Filter', on_click=trigger_search, color='pink-500').classes('w-full font-bold text-white')

        # Panel Kanan: Katalog Produk
        with ui.column().classes('flex-1 glass-card p-8 relative h-[calc(100vh-120px)]'):
            with ui.scroll_area().classes('w-full h-full pr-4') as main_catalog_area:
                
                @ui.refreshable
                def catalog_view() -> None:
                    print(f"DEBUG catalog_view dipanggil")
                    print(f"DEBUG cat_select.value = {cat_select.value}")
                    print(f"DEBUG state.category = {getattr(state, 'category', 'TIDAK ADA')}")
                    
                    keyword = search_input.value.lower() if search_input.value else ""
                    sort_val = sort_select.value
                    category_filter = cat_select.value

                    ui_to_backend = {
                        'Semua': 'All',
                        'Serum': 'Serum',
                        'Moisturizer': 'Moisturizer',
                        'Toner': 'Toner',
                        'Sunscreen': 'Sunscreen',
                        'Cleanser': 'Cleanser',  # ← bukan 'Face Wash'
                    }
                    backend_category = ui_to_backend.get(category_filter, 'All')
                    print(f"DEBUG backend_category = {backend_category}")

                    min_price, max_price = 0.0, float('inf')
                    if price_select.value == '< Rp 50k':
                        max_price = 49999.0
                    elif price_select.value == 'Rp 50k - Rp 150k':
                        min_price = 50000.0
                        max_price = 150000.0
                    elif price_select.value == 'Rp 150k - Rp 300k':
                        min_price = 150000.1
                        max_price = 300000.0
                    elif price_select.value == '> Rp 300k':
                        min_price = 300000.1

                    paginated_data = data_mgr.get_paginated_products(
                        page=state.page,
                        items_per_page=12,
                        category_filter=backend_category,
                        keyword=keyword,
                        min_price=min_price,
                        max_price=max_price,
                        sort_val=sort_val
                    )
                    
                    print(f"DEBUG total_items = {paginated_data['total_items']}")
                    print(f"DEBUG items count = {len(paginated_data['items'])}")
                    
                    items = paginated_data["items"]

                    ui.label(f'{paginated_data["total_items"]} PRODUK DITEMUKAN').classes('text-xs font-bold text-gray-500 mb-6 tracking-wider')

                    if len(items) == 0:
                        with ui.column().classes('w-full items-center justify-center p-12'):
                            ui.label('🏜️').classes('text-6xl mb-4')
                            ui.label('Ups, tidak ada produk yang sesuai kriteria.').classes('text-gray-500')
                    else:
                        with ui.grid(columns=3).classes('w-full gap-6 items-stretch'):
                            for prod in items:
                                # Data produk
                                name = prod.get('product_name', prod.get('name', 'Tanpa Nama'))
                                brand = prod.get('brand', 'Tanpa Merk')
                                price = prod.get('min_price', prod.get('price', 0))
                                rating = prod.get('average_rating', prod.get('rating', 0.0))
                                format_price = f"Rp{price:,.0f}".replace(',', '.')
                                img_url = prod.get('image_url', '')
                                
                                # Mengambil data ingredient untuk tombol +Wishlist bawaan jika diperlukan
                                try:
                                    ingredient_profile = data_mgr.get_ingredient_profile(prod)
                                except:
                                    ingredient_profile = {}

                                def handle_add_item(p=prod) -> None:
                                    current = getattr(state, 'wishlist', [])
                                    if not any(item.get('slug') == p.get('slug', '') for item in current):
                                        object.__setattr__(state, 'wishlist', current + [p])
                                        print(f"DEBUG wishlist sekarang: {len(getattr(state, 'wishlist', []))} produk")
                                        ui.notify(f'✨ {p.get("product_name", "Produk")} ditambahkan ke Wishlist!', 
                                                color='pink', position='bottom-right')
                                    else:
                                        ui.notify('Produk ini sudah ada di Wishlist.', color='info', position='bottom-right')

                                # Kartu Produk
                                with ui.card().classes('p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between'):
                                    with ui.column().classes('w-full'):
                                        # Gambar (Gunakan icon sementara karena tidak ada url gambar)
                                        with ui.column().classes('w-full h-32 bg-pink-50 rounded-lg items-center justify-center mb-4 relative overflow-hidden'):
                                            # Indikator kulit cocok jika ada
                                            if skin_select.value != 'Semua' and hasattr(data_mgr, 'check_suitability'):
                                                # Fitur kosmetik
                                                ui.badge('Cocok', color='green').classes('absolute top-2 right-2 z-10')
                                            
                                            if img_url and str(img_url).startswith('http'):
                                                ui.image(img_url).classes('w-full h-full object-contain absolute inset-0 mix-blend-multiply')
                                            else:
                                                icon_map = {'Serum': '💧', 'Moisturizer': '🧴', 'Toner': '🌊', 'Sunscreen': '☀️'}
                                                cat_icon = icon_map.get(prod.get('category', ''), '✨')
                                                ui.label(cat_icon).classes('text-5xl')
                                            
                                        # Info Teks
                                        ui.label(name).classes('font-bold text-sm leading-tight line-clamp-2 min-h-[40px]')
                                        ui.label(brand).classes('text-xs text-gray-500 mb-2 truncate w-full')
                                        ui.label(format_price).classes('text-pink-500 font-bold text-lg')
                                        
                                        # Rating
                                        with ui.row().classes('items-center gap-1 mb-4'):
                                            ui.label('★').classes('text-yellow-400 text-sm')
                                            ui.label(str(rating)).classes('text-xs font-bold')
                                    
                                    # Tombol Bawah
                                    with ui.row().classes('w-full gap-2 mt-auto'):
                                        ui.button('Detail', color='white').classes('flex-1 border border-gray-300 text-xs text-black shadow-none')
                                        ui.button('+ Wishlist', color='pink-50', on_click=handle_add_item).classes('flex-[1.5] shadow-none font-bold border border-pink-200 text-pink-600 text-xs px-1')

                    # Pagination Bawaan
                    def handle_page_change(new_page: int) -> None:
                        state.page = new_page
                        catalog_view.refresh()
                        main_catalog_area.scroll_to()

                    if paginated_data["total_pages"] > 1:
                        ui.separator().classes('mt-10 mb-6 opacity-20')
                        UIComponents.pagination_controls(
                            current_page=paginated_data["current_page"],
                            total_pages=paginated_data["total_pages"],
                            on_change=handle_page_change
                        )
                print(f"DEBUG BAWAH: state.category = {getattr(state, 'category', 'TIDAK ADA')}")

                catalog_view()
                
                if hasattr(state, 'category') and state.category:
                    cat_select.value = state.category
                    state.page = 1
                    catalog_view.refresh()

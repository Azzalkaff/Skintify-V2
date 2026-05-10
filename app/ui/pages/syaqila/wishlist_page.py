from nicegui import ui, app
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager

def show_page():
    """MISI SYAQILA: Membuat Galeri Wishlist"""
    
    # --- JANGAN DIUBAH (Wajib untuk Navigasi) ---
    auth_redirect = AuthManager.require_auth()
    if auth_redirect: return auth_redirect
    UIComponents.navbar()
    UIComponents.sidebar()
    # -------------------------------------------

    # --- 🚀 MULAI KERJAKAN DI SINI (AREA BELAJAR SYAQILA) ---
    
    # Data produk wishlist (nanti bisa diganti dari data_mgr)
    # --- 🚀 AREA WISHLIST DINAMIS ---

    wishlist_products = getattr(state, 'wishlist', [])

    print(f"DEBUG wishlist isi: {state.wishlist}")
    print(f"DEBUG jumlah: {len(state.wishlist)}")


    def hapus_produk(slug: str):
        current = getattr(state, 'wishlist', [])
        object.__setattr__(state, 'wishlist', [p for p in current if p.get('slug') != slug])
        ui.notify('Produk dihapus dari Wishlist')
        ui.navigate.to('/wishlist')


    with ui.column().classes('w-full p-8 bg-rose-50/30 min-h-screen gap-4'):

        # HEADER
        with ui.row().classes('w-full items-center justify-between pb-2 border-b border-gray-200'):
            ui.label('Wishlist').classes('text-2xl font-bold text-gray-800')
            with ui.element('div').classes('bg-pink-100 px-4 py-1.5 rounded-full'):
                skin_type = app.storage.user.get('skin_type', 'Belum diisi')
                ui.label(f'Kulit: {skin_type}').classes('text-pink-600 text-sm font-medium')

        # jumlah produk
        ui.label(f'{len(wishlist_products)} PRODUK TERSIMPAN').classes(
            'text-xs font-semibold text-gray-500 tracking-wider mt-2'
        )

        # EMPTY STATE
        if not wishlist_products:
            ui.label("Belum ada produk di wishlist 😢").classes(
                "text-gray-400 mt-6 text-center"
            )

        # LIST PRODUK
        with ui.grid(columns=1).classes('w-full gap-3'):
            for product in wishlist_products:

                with ui.card().classes(
                    'w-full p-4 rounded-xl shadow-none border border-gray-100 '
                    'hover:shadow-md transition-shadow bg-white'
                ):
                    with ui.row().classes('w-full items-center justify-between no-wrap'):

                        # KIRI
                        with ui.row().classes('items-center gap-4 no-wrap flex-1'):

                            with ui.element('div').classes('w-14 h-14 rounded-xl overflow-hidden bg-pink-50 flex items-center justify-center'):
                                if product.get('image_url') and str(product.get('image_url')).startswith('http'):
                                    ui.image(product['image_url']).classes('w-full h-full object-contain')
                                else:
                                    icon_map = {'Serum': '💧', 'Moisturizer': '🧴', 'Toner': '🌊', 'Sunscreen': '☀️'}
                                    cat_icon = icon_map.get(product.get('category', ''), '🧴')
                                    ui.label(cat_icon).classes('text-2xl')

                            with ui.column().classes('gap-0'):
                                ui.label(product.get('product_name', product.get('name', '-'))).classes(
                                    'text-base font-bold text-gray-800'
                                )
                                ui.label(
                                    f'{product.get("brand", "-")} · {product.get("category", "-")}'
                                ).classes('text-sm text-gray-500')

                        # TENGAH
                        with ui.column().classes('items-end gap-0 mr-4'):
                            ui.label(f"Rp{product.get('min_price', 0):,.0f}".replace(',', '.')).classes(
                                'text-base font-bold text-pink-500'
                            )
                            ui.label(f'★ {product.get("average_rating", "-")}').classes(
                                'text-sm text-yellow-500 font-medium'
                            )

                        # KANAN
                        ui.button(
                            'Hapus',
                            on_click=lambda p=product: hapus_produk(p.get('slug'))
                        ).props('outline no-caps').classes(
                            'text-pink-500 border-pink-300 rounded-lg px-6'
                        )

from nicegui import ui
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

# init state wishlist
if 'wishlist' not in state.__dict__:
    state.__dict__['wishlist'] = []

wishlist_products = state.__dict__.get('wishlist', [])


def hapus_produk(product_name: str):
    state.__dict__['wishlist'] = [
        p for p in state.__dict__.get('wishlist', [])
        if p.get("name") != product_name
    ]
    ui.notify(f'Produk "{product_name}" dihapus')
    ui.navigate.to('/wishlist')


with ui.column().classes('w-full p-8 bg-rose-50/30 min-h-screen gap-4'):

    # HEADER
    with ui.row().classes('w-full items-center justify-between pb-2 border-b border-gray-200'):
        ui.label('Wishlist').classes('text-2xl font-bold text-gray-800')
        with ui.element('div').classes('bg-pink-100 px-4 py-1.5 rounded-full'):
            ui.label('Kulit: Oily').classes('text-pink-600 text-sm font-medium')

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

                        with ui.element('div').classes(
                            f'{product.get("bg_color", "bg-pink-50")} w-14 h-14 rounded-xl '
                            'flex items-center justify-center text-2xl'
                        ):
                            ui.label(product.get('icon', '🧴'))

                        with ui.column().classes('gap-0'):
                            ui.label(product.get('name', '-')).classes(
                                'text-base font-bold text-gray-800'
                            )
                            ui.label(
                                f'{product.get("brand", "-")} · {product.get("category", "-")}'
                            ).classes('text-sm text-gray-500')

                    # TENGAH
                    with ui.column().classes('items-end gap-0 mr-4'):
                        ui.label(product.get('price', '-')).classes(
                            'text-base font-bold text-pink-500'
                        )
                        ui.label(f'★ {product.get("rating", "-")}').classes(
                            'text-sm text-yellow-500 font-medium'
                        )

                    # KANAN
                    ui.button(
                        'Hapus',
                        on_click=lambda p=product: hapus_produk(p.get('name'))
                    ).props('outline no-caps').classes(
                        'text-pink-500 border-pink-300 rounded-lg px-6'
                    )


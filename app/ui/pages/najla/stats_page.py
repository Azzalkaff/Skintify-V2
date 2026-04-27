from nicegui import ui
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager

def show_page():
    """MISI NAJLA: Membuat Visualisasi Statistik"""
    
    # --- JANGAN DIUBAH (Wajib untuk Navigasi) ---
    auth_redirect = AuthManager.require_auth()
    if auth_redirect: return auth_redirect
    UIComponents.navbar()
    UIComponents.sidebar()
    # -------------------------------------------

    # --- 🚀 MULAI KERJAKAN DI SINI (AREA BELAJAR NAJLA) ---
    
    with ui.row().classes('w-full gap-8'):
    # GRAFIK 1: Bar Chart (Rata-rata harga per kategori)
        with ui.card().classes('flex-1 p-4 shadow-sm'):
            ui.label('Rata-rata harga per kategori').classes('font-bold mb-4')
            ui.echart({
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
        ui.echart({
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
    # --- AKHIR AREA BELAJAR ---

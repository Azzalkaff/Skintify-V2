from nicegui import ui, app
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager
 
 
def show_page():
    """MISI FALISHA: Membuat Pengaturan Profil"""
 
    # --- JANGAN DIUBAH (Wajib untuk Navigasi) ---
    auth_redirect = AuthManager.require_auth()
    if auth_redirect: return auth_redirect
    UIComponents.navbar()
    UIComponents.sidebar()
    # -------------------------------------------
 
    # --- 🚀 MULAI KERJAKAN DI SINI (AREA BELAJAR FALISHA) ---
 
    # AMBIL DATA DARI STORAGE
    # Mengambil data dari storage yang diisi saat onboarding
    email = app.storage.user.get('email', 'User@skintify.com')
    username = app.storage.user.get('username', email.split('@')[0])
    skin_type = app.storage.user.get('skin_type', 'Belum diisi')
    budget_range = app.storage.user.get('budget_range', 'mid')
    
    # Label budget agar lebih rapi
    budget_label = {
        'budget': '< Rp 100k',
        'mid': 'Rp 100k–300k',
        'premium': 'Rp 300k–500k',
        'luxury': '> Rp 500k',
    }.get(budget_range, budget_range)

    hindari_list = app.storage.user.get('avoid_ingredients', [])
    hindari_text = ", ".join(hindari_list) if hindari_list else 'Tidak ada'

    # ── LAYOUT UTAMA ──
    with ui.column().classes('w-full p-8 gap-6 bg-pink-50 min-h-screen'):

        # --- BAGIAN 1: KARTU IDENTITAS (ATAS) ---
        with ui.card().classes('w-full items-center p-8 shadow-sm mb-2 rounded-2xl'):
            ui.icon('person', size='5rem').classes(
                'bg-pink-100 text-pink-600 rounded-full p-4 mb-4'
            )
            ui.label(username).classes('text-3xl font-bold text-gray-800')
            ui.label('Pengguna Skintify').classes('text-sm text-gray-500 mb-4')

            # Deretan badge (Sesuai desain di Tutorial)
            with ui.row().classes('gap-3 flex-wrap justify-center'):
                ui.badge(f'Kulit: {skin_type}', color='pink-100').classes('text-pink-600 px-4 py-2 font-bold')
                ui.badge(f'Budget: {budget_label}', color='pink-100').classes('text-pink-600 px-4 py-2 font-bold')

        # DATA PROFIL (KIRI) & RIWAYAT (KANAN) ---
        with ui.row().classes('w-full gap-6 items-stretch'):

            # KARTU KIRI: Informasi Detail
            with ui.card().classes('flex-1 p-8 shadow-sm rounded-2xl'):
                ui.label('Data Profil').classes('font-bold text-xl mb-6 text-pink-500')
                
                with ui.column().classes('w-full gap-4'):
                    with ui.row().classes('w-full justify-between border-b pb-2'):
                        ui.label('Email').classes('text-gray-500')
                        ui.label(email).classes('font-bold')

                    with ui.row().classes('w-full justify-between border-b pb-2'):
                        ui.label('Tipe Kulit').classes('text-gray-500')
                        ui.label(skin_type).classes('font-bold')

                    with ui.row().classes('w-full justify-between border-b pb-2'):
                        ui.label('Bahan dihindari').classes('text-gray-500')
                        ui.label(hindari_text).classes('font-bold')

                    with ui.row().classes('w-full justify-between border-b pb-2'):
                        ui.label('Range Harga').classes('text-gray-500')
                        ui.label(budget_label).classes('font-bold')

            # Riwayat Aktivitas
            with ui.card().classes('flex-1 p-8 shadow-sm rounded-2xl'):
                ui.label('Riwayat Aktivitas').classes('font-bold text-xl mb-6 text-gray-800')
                
                # Contoh riwayat statis agar tidak kosong
                with ui.row().classes('items-center gap-4 mb-4'):
                    ui.icon('check_circle', color='green-400')
                    with ui.column().classes('gap-0'):
                        ui.label('Berhasil Mengisi Onboarding').classes('font-bold text-sm')
                        ui.label('Baru saja').classes('text-xs text-gray-400')
 
    # --- AKHIR AREA BELAJAR ---
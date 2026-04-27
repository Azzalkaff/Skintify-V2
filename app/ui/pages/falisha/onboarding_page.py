from nicegui import ui, app
from app.context import data_mgr, state

def show_page():
    """MISI FALISHA: Membuat Setup Awal (Onboarding)"""

    with ui.column().classes('w-full h-screen items-center justify-center bg-pink-50'):
        # --- Header ---
        ui.label('✨ SELAMAT DATANG DI SKINTIFY').classes(
                'text-3xl font-extrabold tracking-widest text-pink-500'
            )
        ui.label('Jawab 3 pertanyaan singkat agar kami bisa merekomendasikan\n'
                'produk skincare yang paling cocok untukmu.').classes('text-gray-500 mb-6')

        with ui.card().classes('w-full max-w-md p-8 shadow-lg rounded-2xl'):
            ui.label('1. Apa tipe kulitmu?').classes('font-bold text-lg')
            
            # Pilihan Tipe Kulit
            skin_options = ['Normal', 'Berminyak', 'Kering', 'Kombinasi', 'Sensitif']
            selected_skin = ui.select(skin_options, label='Pilih tipe kulit').classes('w-full')

            # Pertanyaan Budget
            ui.label('2. Budget per produk?').classes('font-bold text-lg mt-4')
            budget_map = {
                'budget': '< Rp 100.000',
                'mid': 'Rp 100.000 - 300.000',
                'premium': 'Rp 300.000 - 500.000',
                'luxury': '> Rp 500.000'
            }
            selected_budget = ui.select(budget_map, label='Pilih budget').classes('w-full')

            ui.label('3. Bahan yang ingin kamu hindari?').classes('font-bold text-lg mt-4')
            ui.label('Pilih bahan yang membuat kulitmu sensitif.').classes('text-xs text-gray-400 -mt-2')

            avoid_options = ['Alcohol', 'Fragrance', 'Paraben', 'Sulfate']
            selected_avoid = ui.select(avoid_options, multiple=True, label='Pilih bahan (opsional)').classes('w-full')

            # --- PERBAIKAN INDENTASI DI SINI ---
            def simpan_dan_lanjut():
                tipe_kulit = selected_skin.value
                budget_key = selected_budget.value
                hindari_kandungan = selected_avoid.value 

                if not tipe_kulit or not budget_key:
                    ui.notify('Tipe kulit dan budget wajib diisi ya! 🌸', color='warning')
                    return

                try:
                    # Simpan ke storage 
                    app.storage.user['skin_type'] = tipe_kulit
                    app.storage.user['budget_range'] = budget_key
                    app.storage.user['avoid_ingredients'] = hindari_kandungan
                    
                    email = app.storage.user.get('email')
                    if email:
                        data_mgr.update_user_profile(
                            email=email,
                            skin_type=tipe_kulit,
                            budget_range=budget_key
                        )

                    ui.notify('Profil berhasil disimpan! ✨', color='positive')
                    ui.navigate.to('/') 

                except Exception as e:
                    ui.notify(f'Gagal menyimpan: {e}', color='negative')
                    print(f"Error Detail: {e}")

            # Tombol harus sejajar dengan isi 'with ui.card()'
            ui.button('Mulai Eksplorasi →', on_click=simpan_dan_lanjut).classes(
                'w-full mt-6 bg-pink-500 text-white font-bold py-3 rounded-xl'
            )
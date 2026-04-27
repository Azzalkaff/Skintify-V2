from nicegui import ui
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager
import re

def show_page():
    """MISI NAJLA: Membuat Logika Perbandingan Produk"""
    
    # --- JANGAN DIUBAH (Wajib untuk Navigasi) ---
    auth_redirect = AuthManager.require_auth()
    if auth_redirect: return auth_redirect
    UIComponents.navbar()
    UIComponents.sidebar()
    # -------------------------------------------

    # --- 🚀 MULAI KERJAKAN DI SINI (AREA BELAJAR NAJLA) ---
    # ambil data produk dari data manager (maks 1000 biar banyak pilihan)
    data = data_mgr.get_paginated_products(page=1, items_per_page=1000)
    products = data['items']

    # bikin mapping: "Brand - Nama Produk (Kategori)" buat data produk
    # biar gampang dipanggil dari dropdown
    products_map = {
        f"{p['brand']} - {p['product_name']} ({p.get('category', '-')})": p
        for p in products
    }

    # isi dropdown
    options = list(products_map.keys())

    # state sementara produk yang dipilih user
    selected_products = []

    # judul halaman
    ui.label("Bandingkan Produk").classes("text-2xl font-bold")
    ui.label("Pilih hingga 3 produk untuk membandingkan spesifikasi, harga, dan bahan aktif")\
        .classes("text-gray-500 mb-3")

    # dropdown search (bisa diketik)
    dropdown = ui.select(
        options=options,
        label="Cari produk...",
        with_input=True
    ).classes("w-96")

    # fungsi buat fokus ke search (dipake di empty state)
    dropdown.props("use-input input-debounce=0")
    def focus_dropdown():
        dropdown.run_method('focus')

    # logic tambah produk ke perbandingan
    def add_product():
        value = dropdown.value

        # validasi 
        if not value:
            ui.notify("Pilih produk dulu")
            return

        if value in selected_products:
            ui.notify("Sudah dipilih")
            return

        if len(selected_products) >= 3:
            ui.notify("Maksimal 3 produk")
            return

        new_product = products_map[value]

        # validasi kategori harus sama
        if selected_products:
            first_product = products_map[selected_products[0]]

            if new_product.get("category") != first_product.get("category"):
                ui.notify("Produk harus dari kategori yang sama!", color="red")
                return
            
        selected_products.append(value)
        render()

    # hapus produk dari perbandingan
    def remove_product(value):
        if value in selected_products:
            selected_products.remove(value)
            render()

    # add to wishlist (sementara cuma notif)
    def add_to_wishlist(item):
        ui.notify(
            "✨ Produk berhasil ditambahkan ke Wishlist!",
            position="bottom-right",
            classes="bg-pink-500 text-white rounded-lg shadow-lg px-4 py-3"
        )

    # ambil volume dari variant (misal: "30 ml")
    def get_volume(p):
        try:
            variants = p.get("variants", [])
            if not variants:
                return "-"

            text = variants[0].get("variant_name", "")
            match = re.search(r'\d+', text)

            return f"{match.group()} ml" if match else "-"
        except:
            return "-"
    
    # hitung harga per ml (biar bisa bandingin value)
    def safe_price_per_ml(p):
        try:
            variants = p.get("variants", [])
            if not variants:
                return "-"

            text = variants[0].get("variant_name", "")
            match = re.search(r'\d+', text)

            if not match:
                return "-"

            volume = int(match.group())
            if volume == 0:
                return "-"

            return f"Rp{int(p['min_price']/volume):,}"
        except:
            return "-"

    # format rating + jumlah review
    def format_rating(p):
                rating = p.get("average_rating")
                reviews = p.get("total_reviews")

                if rating:
                    if reviews:
                        return f"⭐ {rating} ({reviews})"
                    return f"⭐ {rating}"
                return "-"
    
    with ui.row().classes("gap-3"):
        # tombol tambah produk ke perbandingan
        add_btn = ui.button("+ TAMBAH PRODUK", on_click=add_product)\
            .props("color=none")\
            .classes("bg-pink-500 text-white hover:bg-pink-600")

        # fungsi reset semua produk yang dipilih
        def reset_all():
            selected_products.clear()
            render()

        # tombol reset
        ui.button("Bersihkan Semua", on_click=reset_all)\
            .props("color=none")\
            .classes("bg-pink-300")

    container = ui.column().classes(
        "w-full bg-white p-6 rounded-xl shadow-md gap-4 overflow-x-auto"
    )

    def render():
        container.clear()

        # disable tombol kalau sudah 3 produk
        if len(selected_products) >= 3:
            add_btn.props("disable")
            add_btn.classes("opacity-50")
        else:
            add_btn.props(remove="disable")
            add_btn.classes(remove="opacity-50")

        if not selected_products:
            with container:
                with ui.card().classes("w-full p-10 items-center text-center border border-pink-200 bg-white"):

                    ui.icon("shopping_cart").classes("text-5xl text-gray-400 mb-4")

                    ui.label("Belum ada produk untuk dibandingkan")\
                        .classes("text-lg font-semibold mb-2")

                    ui.label("Mulai dengan menambahkan produk dari halaman pencarian atau beranda")\
                        .classes("text-gray-500 mb-4")

                    ui.button(
                        "Mulai Cari Produk",
                        on_click=focus_dropdown
                    ).props("color=none")\
                    .classes("bg-pink-500 text-white px-4 py-2 rounded-lg hover:bg-pink-600")
    

            return

        selected_data = [products_map[x] for x in selected_products]

        def format_rp(x):
            return f"Rp{x:,}" if x else "-"
        
        cheapest = min(selected_data, key=lambda x: x.get("min_price") or 999999)
        
        with container:

            with ui.row().classes("items-center gap-6 flex-nowrap"):
                ui.label("Spesifikasi").classes("w-40 flex font-semibold")

                for item in selected_products:
                    p = products_map[item]

                    with ui.column().classes("w-48 items-center relative shrink-0"):

                        # ❌ tombol hapus
                        ui.button("✕",
                            on_click=lambda e, x=item: remove_product(x)
                        ).props("flat").classes("absolute right-0 top-0 text-red-500")

                        if p.get("image_url"):
                            ui.image(p["image_url"]).classes("w-24 h-24 object-contain")

                        ui.label(p["brand"]).classes("text-xs text-gray-500")
                        ui.label(p["product_name"]).classes("text-sm font-bold text-center")

                        ui.button(
                            "+ Wishlist",
                            on_click=lambda e, x=item: add_to_wishlist(x)
                        ).props("flat color=none").classes(
                            'flex-[1.5] border border-pink-200 !text-pink-600 bg-pink-50 text-xs px-2 py-1 rounded-lg font-semibold'
                        )
            ui.separator()

            def row(label, values):
                with ui.row().classes("items-center gap-6 flex-nowrap"):
                    ui.label(label).classes("w-40 shrink-0")

                    for v in values:
                        ui.label(v).classes("w-48 text-center shrink-0")

            with ui.row().classes("items-start gap-6 flex-nowrap"):
                ui.label("Harga").classes("w-40")

                for p in selected_data:
                    with ui.column().classes("w-48 text-center gap-1"):

                        prices = {
                            "Sociolla": p.get("min_price"),
                            "Tokopedia": p.get("price_tokopedia"),
                            "Lazada": p.get("price_lazada"),
                        }

                        # ambil yang ada aja
                        valid = {k: v for k, v in prices.items() if v}

                        if valid:
                            cheapest_market = min(valid, key=valid.get)
                            cheapest_price = valid[cheapest_market]

                            # 🔥 harga utama
                            ui.label(f"🔥 {format_rp(cheapest_price)} ({cheapest_market})")\
                                .classes("font-bold text-pink-500")
                        else:
                            ui.label("-")

                        # 👇 tampilkan SEMUA marketplace (termasuk yang kosong)
                        for name, price in prices.items():
                            if name != cheapest_market:
                                if price:
                                    ui.label(f"{name}: {format_rp(price)}")\
                                        .classes("text-xs text-gray-400")
                                else:
                                    ui.label(f"{name}: -")\
                                        .classes("text-xs text-gray-300")

            row("Harga/ml", [safe_price_per_ml(p) for p in selected_data])

            row("Volume", [get_volume(p) for p in selected_data])

            row("Rating", [format_rating(p) for p in selected_data])

            row("Kategori", [
                p.get("category") or "-"
                for p in selected_data
            ])

            with ui.row().classes("items-center gap-6 flex-nowrap"):
                ui.label("Jenis Kulit").classes("w-40")

                for p in selected_data:
                    with ui.column().classes("w-48 items-center gap-1"):

                        skins = p.get("skin_type") or p.get("skin_types") or []

                        if skins:
                            for skin in skins:
                                ui.label(skin).classes(
                                    "px-2 py-1 text-xs border rounded-full bg-gray-100"
                                )
                        else:
                            ui.label("-")
            
            with ui.row().classes("items-center gap-6 flex-nowrap"):
                ui.label("Bahan Aktif").classes("w-40")

                for p in selected_data:
                    with ui.column().classes("w-48 items-center gap-1"):

                        raw = p.get("ingredients_raw") or p.get("ingredients") or ""
                        text = re.sub(r'<[^>]+>', '', raw)
                        ingredients = [i.strip() for i in text.split(",") if i.strip()]

                        if not ingredients:
                            ui.label("-")
                        else:
                            for ing in ingredients[:3]:
                                ui.label(ing).classes(
                                    "px-2 py-1 text-xs border rounded-full bg-gray-100"
                                )

                            if len(ingredients) > 3:
                                ui.label(f"+{len(ingredients)-3}").classes(
                                    "px-2 py-1 text-xs border rounded-full"
                                )
            # ================= VISUALISASI =================
            with ui.card().classes("w-full p-4 mt-4"):
                ui.label("Perbandingan Visual Produk").classes("font-semibold mb-3")

                names = [p['brand'] for p in selected_data]
                prices = [p.get('min_price') or 0 for p in selected_data]
                ratings = [p.get('average_rating') or 0 for p in selected_data]

                # ===== CHART HARGA =====
                ui.label("Harga Produk").classes("text-sm text-gray-500")

                ui.echart({
                    'xAxis': {'type': 'category', 'data': names},
                    'yAxis': {'type': 'value'},
                    'series': [{
                        'type': 'bar',
                        'data': prices
                    }]
                }).classes("w-full h-48 mb-4")

                # ===== CHART RATING =====
                ui.label("Rating Produk").classes("text-sm text-gray-500")

                ui.echart({
                    'xAxis': {'type': 'category', 'data': names},
                    'yAxis': {'type': 'value'},
                    'series': [{
                        'type': 'bar',
                        'data': ratings
                    }]
                }).classes("w-full h-48")

    render()
    # --- AKHIR AREA BELAJAR ---

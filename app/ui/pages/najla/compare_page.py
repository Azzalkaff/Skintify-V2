from nicegui import ui
from app.context import data_mgr, state
from app.ui.components import UIComponents
from app.auth.auth import AuthManager
from app.database.engine import SessionLocal
from app.database.models import Produk
from sqlalchemy import or_
import re


def get_marketplace_price(p, platform):
    name = p.get("product_name", "") or ""
    brand = p.get("brand", "") or ""
    if not name and not brand:
        return None

    terms = [name.strip()]
    if name:
        terms.append(" ".join(name.split()[:3]))
    if brand:
        terms.append(brand.strip())

    filters = []
    for term in terms:
        if term:
            filters.extend([
                Produk.nama.ilike(f"%{term}%"),
                Produk.keyword.ilike(f"%{term}%")
            ])

    if not filters:
        return None

    with SessionLocal() as session:
        rows = session.query(Produk.harga).filter(
            Produk.platform == platform,
            or_(*filters)
        ).all()

        prices = [r[0] for r in rows if r[0]]
        return min(prices) if prices else None


def get_tokopedia_price(p):
    return get_marketplace_price(p, "tokopedia")


def get_lazada_price(p):
    return get_marketplace_price(p, "lazada")
    
def show_all_ingredients(ingredients):
    with ui.dialog() as dialog, ui.card():
        ui.label("Kandungan & Fungsinya").classes("font-bold mb-2")

        for ing in ingredients:
            label = ing.lower()

            if "niacinamide" in label:
                desc = "Brightening ✨"
            elif "hyaluronic" in label:
                desc = "Hydrating 💧"
            elif "centella" in label:
                desc = "Soothing 🌿"
            elif "salicylic" in label:
                desc = "Acne care 🔥"
            else:
                desc = ""

            ui.label(f"{ing} {desc}")

    dialog.open()

def infer_skin_types(p):
    # Coba ambil langsung field yang sudah ada dulu.
    if isinstance(p.get("skin_type"), (list, tuple)) and p.get("skin_type"):
        return list(p.get("skin_type"))
    if isinstance(p.get("skin_types"), (list, tuple)) and p.get("skin_types"):
        return list(p.get("skin_types"))
    if isinstance(p.get("skin_type"), str) and p.get("skin_type").strip():
        return [p.get("skin_type").strip()]
    if isinstance(p.get("skin_types"), str) and p.get("skin_types").strip():
        return [p.get("skin_types").strip()]

    text_parts = []
    for field in ["product_name", "description_raw", "ingredients", "how_to_use_raw"]:
        value = p.get(field)
        if value:
            text_parts.append(str(value))

    for review in p.get("reviews", []):
        if isinstance(review, dict):
            comment = review.get("comment") or review.get("text") or ""
            text_parts.append(str(comment))

    text = " ".join(text_parts).lower()
    patterns = {
        "Oily": ["berminyak", "oily", "oiliness", "minyak"],
        "Dry": ["kering", "dry", "dehydrated"],
        "Sensitive": ["sensitif", "sensitive", "kemerahan", "redness", "iritasi", "irritated"],
        "Combination": ["kombinasi", "combination"],
        "Normal": ["normal"]
    }

    found = []
    for label, keywords in patterns.items():
        if any(keyword in text for keyword in keywords):
            found.append(label)

    return list(dict.fromkeys(found))


def get_best_price(p):
    prices = [
        p.get("min_price"),              # Sociolla
        get_tokopedia_price(p),          # Tokopedia
        get_lazada_price(p)              # Lazada
    ]

    valid = [x for x in prices if x]
    return min(valid) if valid else 0

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

                        tokped_price = get_tokopedia_price(p)
                        lazada_price = get_lazada_price(p)

                        prices = {
                            "Sociolla": p.get("min_price"),
                            "Tokopedia": tokped_price,
                            "Lazada": lazada_price,
                        }

                        valid = {k: v for k, v in prices.items() if v}

                        if valid:
                            cheapest_market = min(valid, key=valid.get)
                            cheapest_price = valid[cheapest_market]
                            ui.label(f"🔥 {format_rp(cheapest_price)} ({cheapest_market})")\
                                .classes("font-bold text-pink-500")
                        else:
                            ui.label("-")

                        ui.label("Detail harga:").classes("text-xs font-semibold text-gray-500")
                        for name, price in prices.items():
                            ui.label(f"{name}: {format_rp(price)}")\
                                .classes("text-xs text-gray-400")

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

                        skins = infer_skin_types(p)

                        if skins:
                            for skin in skins:
                                ui.label(skin).classes(
                                    "px-2 py-1 text-xs border rounded-full bg-gray-100"
                                )
                        else:
                            ui.label("-")
            
            with ui.row().classes("items-center gap-6 flex-nowrap"):
                ui.label("Kandungan Utama").classes("w-40")

                for p in selected_data:
                    with ui.column().classes("w-48 items-center gap-1"):

                        raw = p.get("ingredients_raw") or p.get("ingredients") or ""
                        text = re.sub(r'<[^>]+>', '', raw)
                        skip = [
                            "aqua", "water", "parfum", "fragrance",
                            "butylene glycol", "propylene glycol",
                            "glycerin"
                        ]

                        ingredients = [
                            i.strip() for i in text.split(",")
                            if i.strip() and i.lower() not in skip
                        ]

                        for ing in ingredients[:2]:
                            if len(ingredients) > 2:
                                 ui.label("...").classes("text-xs text-gray-400")

                        if not ingredients:
                            ui.label("-")
                        else:
                            for ing in ingredients[:3]:
                                ui.label(ing).classes(
                                    "px-2 py-1 text-xs border rounded-full bg-gray-100"
                                )

                            if len(ingredients) > 3:
                                ui.button(
                                    f"+{len(ingredients)-3} lainnya",
                                    on_click=lambda e, ing=ingredients: show_all_ingredients(ing)
                                ).classes("text-xs bg-gray-100 px-2 py-1 rounded-full")
            # ================= VISUALISASI =================
            with ui.card().classes("w-full p-4 mt-4"):
                ui.label("Perbandingan Visual Produk").classes("font-semibold mb-3")

                def get_score(p):
                    price = get_best_price(p)
                    rating = p.get('average_rating') or 0

                    if not price:
                        return 0

                    return rating / price


                # cari best
                best_value = max(selected_data, key=get_score)
                best_price = min(selected_data, key=lambda x: get_best_price(x) or 999999)
                best_rating = max(selected_data, key=lambda x: x.get('average_rating') or 0)

                names = [p['brand'] for p in selected_data]
                prices = [get_best_price(p) for p in selected_data]
                ratings = [p.get('average_rating') or 0 for p in selected_data]

                # ===== CHART HARGA =====
                ui.label("💰 Perbandingan Harga (lebih murah lebih baik)").classes("text-sm text-gray-500")
                min_price = min(prices)

                ui.echart({
                    'xAxis': {
                        'type': 'category',
                        'data': names
                    },
                    'yAxis': {'type': 'value'},
                    'series': [{
                        'type': 'bar',
                        'data': [
                            {
                                'value': v,
                                'itemStyle': {
                                    'color': '#22c55e' if v == min_price else '#f472b6'
                                }
                            }
                            for v in prices
                        ],
                        'label': {
                            'show': True,
                            'position': 'top'
                        }
                    }]
                }).classes("w-full h-64")

                # ===== CHART RATING =====
                ui.label("⭐ Perbandingan Rating (lebih tinggi lebih baik)").classes("text-sm text-gray-500")

                max_rating = max(ratings)

                chart_data = []
                for v in ratings:
                    if v == max_rating:
                        chart_data.append({
                            'value': v,
                            'itemStyle': {'color': '#facc15'}  # kuning (best)
                        })
                    else:
                        chart_data.append({
                            'value': v,
                            'itemStyle': {'color': '#60a5fa'}  # biru biasa
                        })

                ui.echart({
                    'xAxis': {'type': 'category', 'data': names},
                    'yAxis': {
                        'type': 'value',
                        'max': 5
                    },
                    'series': [{
                        'type': 'bar',
                        'data': chart_data,
                        'label': {
                            'show': True,
                            'position': 'top',
                            'formatter': '{c} ⭐'
                        }
                    }]
                }).classes("w-full h-64")

                ui.label("📊 Ringkasan Perbandingan").classes("text-lg font-semibold mt-4")

                with ui.row().classes("gap-4"):

                    # 🏆 BEST VALUE
                    with ui.card().classes("p-4 w-72"):
                        ui.label(f"🏆 Paling Worth It: {best_value['brand']}")\
                            .classes("font-bold text-green-600")

                        ui.label("✔ Kombinasi harga & rating terbaik")\
                            .classes("text-sm text-gray-600")

                    # 💰 TERMURAH
                    with ui.card().classes("p-4 w-72"):
                        ui.label(f"💰 Paling Murah: {best_price['brand']}")\
                            .classes("font-bold text-pink-500")

                        ui.label("✔ Cocok kalau budget minim")\
                            .classes("text-sm text-gray-600")

                    # ⭐ RATING
                    with ui.card().classes("p-4 w-72"):
                        ui.label(f"⭐ Rating Tertinggi: {best_rating['brand']}")\
                            .classes("font-bold text-yellow-500")

                        ui.label("✔ Kualitas paling bagus dari review")\
                            .classes("text-sm text-gray-600")

    render()
    # --- AKHIR AREA BELAJAR ---

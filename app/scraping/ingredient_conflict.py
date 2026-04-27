import json

def load_data():
    with open('data/products_sociolla.json', 'r', encoding='utf-8') as f:
        produk = json.load(f)['products']
    with open('data/bahan.json', 'r', encoding='utf-8') as f:
        bahan = json.load(f)['bahan']
    return produk, bahan

def cek_konflik_rutin(daftar_produk_pilihan, db_bahan):
    """
    Fungsi ini mensimulasikan user yang memilih beberapa produk untuk dipakai bersamaan.
    Mengembalikan list berisi konflik yang terdeteksi dengan Smart Keyword Matching.
    """
    # 1. Kumpulkan semua nama bahan dari produk (jadikan huruf kecil semua)
    bahan_terpakai_lower = []
    for produk in daftar_produk_pilihan:
        ing_string = produk.get("ingredients", "")
        ing_list = [b.strip().lower() for b in ing_string.split(",") if b.strip()]
        bahan_terpakai_lower.extend(ing_list)
    
    # 2. Kamus Alias Skincare (USP Proyek!)
    # Ini membantu mendeteksi nama turunan dari bahan aktif utama
    kamus_kategori = {
        "vitamin c": ["ascorbic", "vcs", "ascorbyl"],
        "aha": ["glycolic", "lactic", "mandelic", "citric"],
        "bha": ["salicylic", "betaine salicylate"],
        "retinol": ["retinol", "retinoid", "retinyl"]
    }

    # 3. Cek apakah ada bahan yang berkonflik
    peringatan_konflik = []
    dict_bahan = {b['nama_bahan'].lower(): b for b in db_bahan}

    for bahan_produk in bahan_terpakai_lower:
        data_db = dict_bahan.get(bahan_produk)
        
        # Jika bahan ada di database dan punya daftar 'musuh'
        if data_db and data_db.get("konflik_dengan"):
            for musuh in data_db["konflik_dengan"]:
                musuh_lower = musuh.lower()
                
                # Ambil daftar kata kunci alias (jika musuh ada di kamus, gunakan aliasnya. Jika tidak, gunakan nama aslinya)
                keywords_pencarian = kamus_kategori.get(musuh_lower, [musuh_lower])
                
                # Cek apakah ada keyword musuh di dalam daftar bahan yang dipakai user
                for bahan_cek in bahan_terpakai_lower:
                    for keyword in keywords_pencarian:
                        if keyword in bahan_cek and bahan_produk != bahan_cek:
                            peringatan = f"⚠️ AWAS: '{data_db['nama_bahan']}' berpotensi bentrok dengan '{bahan_cek}' (Keturunan {musuh}). Dapat memicu iritasi!"
                            if peringatan not in peringatan_konflik:
                                peringatan_konflik.append(peringatan)

    return peringatan_konflik

if __name__ == "__main__":
    produk_db, bahan_db = load_data()
    
    # Simulasi: User memilih 2 produk dari database secara acak (ganti indexnya untuk tes produk lain)
    if len(produk_db) >= 2:
        produk_1 = produk_db[5]
        produk_2 = produk_db[9] # Coba cari index produk yang mengandung Retinol dan AHA
        
        print("="*50)
        print("SIMULASI ROUTINE BUILDER SKINTIFY")
        print("="*50)
        print(f"Produk 1: {produk_1['brand']} - {produk_1['product_name']}")
        print(f"Produk 2: {produk_2['brand']} - {produk_2['product_name']}")
        print("-"*50)
        
        hasil_konflik = cek_konflik_rutin([produk_1, produk_2], bahan_db)
        
        if hasil_konflik:
            print("HASIL ANALISIS: DETEKSI BAHAYA!")
            for h in hasil_konflik:
                print(h)
        else:
            print("HASIL ANALISIS: AMAN ✅")
            print("Kombinasi produk ini tidak mendeteksi bahan yang bertabrakan.")
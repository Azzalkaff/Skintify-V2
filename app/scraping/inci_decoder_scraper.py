import json
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import glob

# Konfigurasi Path
DATA_DIR = "data"
FILE_BAHAN = "data/bahan.json"
BASE_URL = "https://incidecoder.com/ingredients/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Konflik antar bahan aktif — berbasis konsensus dermatologi
# (sumber: British Journal of Dermatology, Paula's Choice ingredient research)
CONFLICT_MAP: dict = {
    "retinol":          ["aha", "bha", "vitamin c", "benzoyl peroxide"],
    "aha":              ["retinol", "vitamin c", "bha"],
    "bha":              ["retinol", "vitamin c", "aha"],
    "vitamin c":        ["retinol", "aha", "bha", "niacinamide"],
    "niacinamide":      ["vitamin c"],
    "benzoyl peroxide": ["retinol", "vitamin c"],
}

# Keyword → kategori: menentukan kategori suatu bahan agar bisa di-assign konflik_dengan
INGREDIENT_CATEGORY_MAP: dict = {
    "retinol":              "retinol",
    "retinoid":             "retinol",
    "retinyl":              "retinol",
    "hydroxypinacolone":    "retinol",
    "glycolic":             "aha",
    "lactic":               "aha",
    "mandelic":             "aha",
    "citric":               "aha",
    "salicylic":            "bha",
    "betaine salicylate":   "bha",
    "capryloyl salicylic":  "bha",
    "ascorbic":             "vitamin c",
    "ascorbyl":             "vitamin c",
    "niacinamide":          "niacinamide",
    "benzoyl peroxide":     "benzoyl peroxide",
}

def format_slug(ingredient_name):
    """Mengubah nama bahan jadi format URL INCIDecoder (contoh: 'Titanium Dioxide' -> 'titanium-dioxide')"""
    # Ubah ke lowercase, hilangkan karakter aneh, ganti spasi dengan strip
    clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', ingredient_name.lower())
    return "-".join(clean_name.split())

def scrape_incidecoder(slug, original_name):
    """Mengambil data fungsi dan tingkat keamanan dari INCIDecoder"""
    url = f"{BASE_URL}{slug}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None # Bahan tidak ditemukan di database INCIDecoder

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Inisialisasi struktur data per bahan
        data_bahan = {
            "nama_bahan": original_name,
            "fungsi": [],
            "irritancy": "0",
            "comedogenicity": "0",
            "konflik_dengan": [] # Ini akan kita isi manual nanti untuk algoritma rutin
        }

        # Ekstrak Fungsi (Mencari semua link yang mengarah ke /ingredient-functions/)
        for a_tag in soup.find_all('a', href=re.compile(r'/ingredient-functions/')):
            fungsi = a_tag.get_text(strip=True)
            if fungsi not in data_bahan["fungsi"]:
                data_bahan["fungsi"].append(fungsi)

        # Ekstrak Irritancy & Comedogenicity dari seluruh teks halaman
        text_content = soup.get_text()
        
        irr_match = re.search(r'Irritancy:\s*([\d\-]+)', text_content, re.IGNORECASE)
        if irr_match:
            data_bahan["irritancy"] = irr_match.group(1)

        com_match = re.search(r'Comedogenicity:\s*([\d\-]+)', text_content, re.IGNORECASE)
        if com_match:
            data_bahan["comedogenicity"] = com_match.group(1)

        return data_bahan

    except Exception as e:
        print(f"  [ERROR] Gagal scrape {slug}: {e}")
        return None

def _kategorikan_bahan(nama_bahan: str) -> str | None:
    """Menentukan kategori aktif suatu bahan berdasarkan keyword matching O(K)."""
    nama_lower = nama_bahan.lower()
    return next(
        (cat for keyword, cat in INGREDIENT_CATEGORY_MAP.items() if keyword in nama_lower),
        None
    )


def main():
    print("=" * 60)
    print("  Scrape Database Bahan — INCIDecoder")
    print("=" * 60)

    # 1. Baca SEMUA file produk di data/ — konsisten dengan DataManager.glob()
    all_json_files = glob.glob(f"{DATA_DIR}/products_sociolla*.json")
    if not all_json_files:
        print(f"[ERROR] Tidak ada file products_sociolla*.json di folder '{DATA_DIR}'!")
        return

    kumpulan_bahan: set = set()
    for filepath in all_json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for prod in data.get("products", []):
                raw_ing = prod.get("ingredients", "")
                if raw_ing:
                    for item in raw_ing.split(','):
                        item = item.strip()
                        # Skip entri kotor: terlalu pendek atau mengandung seluruh ingredient list
                        if item and 2 < len(item) < 80:
                            kumpulan_bahan.add(item)
        except json.JSONDecodeError:
            print(f"  [SKIP] JSON korup: {filepath}")

    print(f"[INFO] {len(kumpulan_bahan)} bahan unik dari {len(all_json_files)} file produk.")

    # 2. Resume logic — skip bahan yang sudah ada di bahan.json agar tidak mengulang
    bahan_terkumpul: list = []
    sudah_discrape: set = set()
    if os.path.exists(FILE_BAHAN):
        try:
            with open(FILE_BAHAN, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            bahan_terkumpul = existing.get("bahan", [])
            sudah_discrape = {b["nama_bahan"].lower() for b in bahan_terkumpul}
            print(f"[RESUME] {len(sudah_discrape)} bahan sudah ada, melanjutkan sesi sebelumnya.")
        except (json.JSONDecodeError, KeyError):
            print("[WARN] bahan.json korup, memulai dari awal.")

    # 3. Filter hanya bahan yang belum pernah di-scrape
    bahan_baru = [b for b in kumpulan_bahan if b.lower() not in sudah_discrape]
    print(f"[INFO] Akan men-scrape {len(bahan_baru)} bahan baru...\n")

    # Batasi per sesi — jalankan berkali-kali, resume otomatis tiap kali
    BATCH_SIZE = 100
    SAVE_EVERY = 10  # Simpan ke disk setiap N item agar Ctrl+C tidak kehilangan data

    bahan_sesi_ini = bahan_baru[:BATCH_SIZE]
    sisa = len(bahan_baru) - len(bahan_sesi_ini)
    print(f"[INFO] Sesi ini: {len(bahan_sesi_ini)} bahan. Sisa untuk sesi berikutnya: {sisa}\n")

    def _simpan(data: list) -> None:
        """Helper save — dipanggil berkala dan saat exit."""
        hasil_akhir = {
            "metadata": {"sumber": "INCIDecoder", "total_bahan": len(data)},
            "bahan": data
        }
        with open(FILE_BAHAN, 'w', encoding='utf-8') as f:
            json.dump(hasil_akhir, f, ensure_ascii=False, indent=2)

    bahan_sesi_count = 0
    try:
        for i, nama_asli in enumerate(bahan_sesi_ini):
            slug = format_slug(nama_asli)
            if len(slug) < 3:
                continue

            print(f"[{i+1}/{len(bahan_sesi_ini)}] {nama_asli}...", end=" ", flush=True)

            hasil = scrape_incidecoder(slug, nama_asli)
            if hasil:
                kategori = _kategorikan_bahan(nama_asli)
                if kategori and kategori in CONFLICT_MAP:
                    hasil["konflik_dengan"] = CONFLICT_MAP[kategori]
                bahan_terkumpul.append(hasil)
                bahan_sesi_count += 1
                print("✅")
            else:
                print("❌")

            # Simpan ke disk setiap SAVE_EVERY item — aman dari interrupt
            if (i + 1) % SAVE_EVERY == 0:
                _simpan(bahan_terkumpul)
                print(f"  💾 Auto-saved ({len(bahan_terkumpul)} total)")

            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n\n[STOP] Dihentikan manual. Menyimpan progress...")

    finally:
        # Selalu simpan di akhir — baik selesai normal maupun Ctrl+C
        _simpan(bahan_terkumpul)
        print("\n" + "=" * 60)
        print(f"  Sesi ini: +{bahan_sesi_count} bahan baru")
        print(f"  Total tersimpan: {len(bahan_terkumpul)} bahan di {FILE_BAHAN}")
        if sisa > 0:
            print(f"  Jalankan ulang skrip ini untuk melanjutkan ({sisa} bahan tersisa)")
        print("=" * 60)

if __name__ == "__main__":
    main()
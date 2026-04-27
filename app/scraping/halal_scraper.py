import json
import re
from pathlib import Path

try:
    from rapidfuzz import fuzz, process
except ImportError:
    print("Library rapidfuzz belum terinstall. Jalankan di terminal: pip install rapidfuzz")
    exit(1)

# Menggunakan Pathlib untuk resolusi path dinamis yang kebal OS-differences (Windows/Mac)
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "data" / "products_sociolla.json"
OUTPUT_FILE = BASE_DIR / "data" / "products_sociolla_halal.json"
MOCK_DB_FILE = BASE_DIR / "data" / "database_halal_pemerintah.json"

# Menggunakan tipe data SET untuk akses pencarian O(1) yang super efisien
BRAND_HALAL_TERVERIFIKASI = {
    "wardah", "emina", "make over", "skintific", 
    "somethinc", "azarine", "avoskin", "npure", 
    "whitelab", "scarlett whitening", "joylab", "blp beauty",
    "dorskin", "originote", "glad2glow"
}

class HalalValidator:
    def __init__(self, mock_db_path: Path):
        self.db_halal = self._load_mock_db(mock_db_path)

    def _load_mock_db(self, path: Path) -> list:
        """Memuat database halal mock (simulasi dari web pemerintah)"""
        if not path.exists():
            print(f"⚠️ Peringatan: File {path.name} tidak ditemukan. Menggunakan list kosong.")
            return []
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("data_halal", [])
        except Exception as e:
            print(f"❌ Error memuat database halal: {e}")
            return []

    def bersihkan_teks(self, teks: str) -> str:
        """Menghapus ukuran volume/berat (O(N) regex) agar pencocokan Fuzzy NLP lebih akurat"""
        teks = str(teks).lower()
        # Menghapus anomali ukuran seperti '150ml', '50 gr', '100 g', '30 ml'
        teks = re.sub(r'\b\d+\s*(ml|gr|g|oz|kg)\b', '', teks)
        # Menghapus spasi ganda
        return re.sub(r'\s+', ' ', teks).strip()

    def cek_halal(self, produk: dict) -> tuple:
        """
        Algoritma Hybrid Checking:
        1. Whitelist Brand Lookup -> O(1)
        2. Fuzzy Matching NLP -> O(N*M)
        """
        nama_produk = produk.get("product_name", "")
        brand_produk = produk.get("brand", "").lower().strip()
        
        # Lapisan 1: Pengecekan Brand Terverifikasi (Akurat & Instan)
        if brand_produk in BRAND_HALAL_TERVERIFIKASI:
            return True, "Verifikasi Brand (Otomatis)"

        # Lapisan 2: Pengecekan Nama Produk di Database Pemerintah
        if not self.db_halal or not nama_produk:
            return False, "Tidak Ditemukan"

        nama_bersih = self.bersihkan_teks(nama_produk)
        
        # Menggunakan token_set_ratio: mengabaikan urutan kata & kata tambahan
        # Mampu menangkap: "Cosrx Salicylic Acid Cleanser" == "Cosrx Salicylic Acid Daily Gentle Cleanser"
        hasil_match = process.extractOne(
            nama_bersih, 
            self.db_halal, 
            scorer=fuzz.token_set_ratio
        )
        
        # Threshold 85 di-set untuk meminimalisir False Positive (salah duga)
        if hasil_match and hasil_match[1] >= 85:
            return True, f"Verifikasi Produk (Kemiripan: {round(hasil_match[1])}%)"
            
        return False, "Tidak Tersertifikasi / Belum Dicek"

def jalankan_pipeline():
    print("=" * 50)
    print("Menjalankan Pipeline Pemetaan Status Halal")
    print("=" * 50)

    if not INPUT_FILE.exists():
        print(f"❌ Error: File sumber {INPUT_FILE.name} tidak ditemukan di folder data!")
        return

    # Inisiasi Instance
    validator = HalalValidator(MOCK_DB_FILE)

    # Memuat Data E-Commerce asli
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    produk_list = dataset.get("products", [])
    total_produk = len(produk_list)
    jumlah_halal = 0

    print(f"⚙️ Memproses {total_produk} produk... (Fuzzy Logic Running)")

    # Iterasi Data
    for p in produk_list:
        is_halal, metode = validator.cek_halal(p)
        p["is_halal"] = is_halal
        p["halal_method"] = metode
        
        if is_halal:
            jumlah_halal += 1

    # Simpan kembali sebagai dataset yang sudah diperkaya (Enriched Dataset)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("✅ Proses Pipeline Selesai!")
    print(f"📊 Statistik: {jumlah_halal} dari {total_produk} produk berhasil dipetakan sebagai Halal.")
    print(f"💾 Dataset baru berhasil disimpan di: {OUTPUT_FILE.name}")

if __name__ == "__main__":
    jalankan_pipeline()
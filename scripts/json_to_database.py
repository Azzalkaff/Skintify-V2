import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SociollaReferensi  # Pastikan models.py sudah yang terbaru dari Phase 3

# Konfigurasi Database SQLite
DB_URL = "sqlite:///tokopedia.db"
JSON_FILE = "data/products_sociolla_ALL.json"

def run_migration():
    print("=" * 50)
    print("🚀 Memulai Migrasi JSON ke Database SQLite...")
    print("=" * 50)

    # 1. Inisialisasi Database & Buat Tabel Baru
    engine = create_engine(DB_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 2. Baca File JSON
    if not os.path.exists(JSON_FILE):
        print(f"❌ ERROR: File {JSON_FILE} tidak ditemukan!")
        print("Pastikan Anda sudah menjalankan sociolla_scraper.py terlebih dahulu.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        products = data.get("products", [])

    if not products:
        print("⚠ File JSON kosong atau format tidak sesuai.")
        return

    print(f"📦 Ditemukan {len(products)} produk di file JSON. Mulai memasukkan ke database...\n")

    # 3. Masukkan Data ke Database
    berhasil = 0
    gagal = 0

    for p in products:
        try:
            # Cek apakah produk sudah ada (mencegah duplikasi jika dijalankan 2x)
            exists = session.query(SociollaReferensi).filter_by(slug=p.get("slug")).first()
            if exists:
                continue

            # Mapping dari JSON ke Model Database
            db_product = SociollaReferensi(
                slug=p.get("slug"),
                product_name=p.get("product_name"),
                brand=p.get("brand"),
                brand_country=p.get("brand_country"),
                brand_region=p.get("brand_region"),
                category=p.get("category"),
                all_categories=p.get("all_categories", []),
                
                # Harga
                min_price=p.get("min_price"),
                max_price=p.get("max_price"),
                min_price_after_discount=p.get("min_price_after_discount"),
                max_price_after_discount=p.get("max_price_after_discount"),
                
                # Performa & Metrik Loyalitas
                rating_sociolla=p.get("average_rating"),
                total_reviews=p.get("total_reviews"),
                total_recommended=p.get("total_recommended"),
                repurchase_yes=p.get("repurchase_yes"),
                repurchase_no=p.get("repurchase_no"),
                repurchase_maybe=p.get("repurchase_maybe"),
                total_wishlist=p.get("total_wishlist"),
                
                # Metadata
                bpom_reg_no=p.get("bpom_reg_no"),
                url_sociolla=p.get("url"),
                image_url=p.get("image_url"),
                is_in_stock=p.get("is_in_stock"),
                is_flashsale=p.get("is_flashsale"),
                
                # Raw Texts
                description_raw=p.get("description_raw"),
                how_to_use_raw=p.get("how_to_use_raw"),
                ingredients=p.get("ingredients"),
                
                # JSON Nested
                variants=p.get("variants", []),
                reviews=p.get("reviews", [])
            )
            
            session.add(db_product)
            berhasil += 1

        except Exception as e:
            print(f"❌ Gagal import produk {p.get('product_name')}: {e}")
            gagal += 1

    # 4. Simpan Perubahan (Commit)
    session.commit()
    session.close()

    print("=" * 50)
    print(f"✅ Migrasi Selesai!")
    print(f"   Berhasil: {berhasil} produk")
    print(f"   Gagal   : {gagal} produk")
    print("   Database 'tokopedia.db' sekarang siap digunakan oleh aplikasi NiceGUI!")
    print("=" * 50)

if __name__ == "__main__":
    run_migration()
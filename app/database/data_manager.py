"""
Hybrid Repository Pattern untuk DataManager
Menjadi Single Source of Truth: mencoba load SQLite terlebih dahulu. 
Jika kosong (belum ada scraping interaktif dari terminal), akan membaca file JSON fallback.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.database.engine import SessionLocal
from app.database.models import SociollaReferensi, Produk
from app.services.analyzer import IngredientDatabase, SkincareAnalyzer
from app.services.weather import WeatherService

logger = logging.getLogger(__name__)

class DataManager:
    """
    Facade class yang menggabungkan SQLite, JSON Fallback, Analyzer, dan WeatherService.
    Memberikan satu antarmuka yang bersih untuk digunakan oleh main.py.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.ingredient_db = IngredientDatabase(self.data_dir)
        
        # Cache memory
        self._categories = ["All"]
        self._cached_products = None 
        
        # Mapping Kategori untuk Harmonisasi UI (Pilihan A)
        self.CATEGORY_MAP = {
            # Mapping dari nama JSON → nama UI
            "Face Serum": "Serum",        
            "Face Gel": "Moisturizer",    # ✅ sudah ada
            "Micellar Water": "Cleanser", # ✅ 
            "Face Wash": "Cleanser",      # ✅
            "Scrub & Exfoliator": "Cleanser",
            "Face Mist": "Toner",         # ← anggap face mist = toner
            "Sunscreen": "Sunscreen",     # ✅
        }

    def get_ingredient_profile(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.ingredient_db.is_loaded():
            return None
        raw = product.get("ingredients", "")
        if not raw:
            return None
        ingredient_set = {item.strip().lower() for item in raw.split(',') if item.strip()}
        return self.ingredient_db.get_aggregate(ingredient_set)

    @property
    def categories(self) -> List[str]:
        if len(self._categories) > 1:
            return self._categories
            
        with SessionLocal() as session:
            cats = session.query(SociollaReferensi.category).distinct().all()
            if cats:
                clean_cats = {c[0] for c in cats if c[0] and c[0] != "Uncategorized"}
                self._categories = ["All"] + sorted(list(clean_cats))
            else:
                # Kategori Standar UI
                self._categories = ["All", "Face Wash", "Moisturizer", "Sunscreen", "Serum"]
        return self._categories

    def get_paginated_products(
        self, page: int = 1, items_per_page: int = 12, category_filter: str = "All",
        keyword: str = "", min_price: float = 0.0, max_price: float = float('inf'),
        sort_val: str = "Rating (Tertinggi)"
    ) -> Dict[str, Any]:
        """Pencarian efisien Big-O(1) Pagination limit-offset pada SQL"""
        with SessionLocal() as session:
            # Cek apakah db benar-benar kosong (< 10 data total) untuk pakai fallback
            is_empty_db = session.query(SociollaReferensi).count() < 10
            if is_empty_db:
                return self._fallback_json_load(
                    page, items_per_page, category_filter,
                    keyword, min_price, max_price, sort_val
                )

            query = session.query(SociollaReferensi)
            if category_filter != "All":
                query = query.filter(SociollaReferensi.category == category_filter)
            
            if keyword:
                from sqlalchemy import or_
                search_term = f"%{keyword.lower()}%"
                query = query.filter(or_(
                    SociollaReferensi.product_name.ilike(search_term),
                    SociollaReferensi.brand.ilike(search_term)
                ))
                
            if min_price > 0:
                query = query.filter(SociollaReferensi.min_price >= min_price)
            if max_price < float('inf'):
                query = query.filter(SociollaReferensi.min_price <= max_price)
                
            if sort_val == 'Rating (Tertinggi)':
                query = query.order_by(SociollaReferensi.rating_sociolla.desc())
            elif sort_val == 'Harga (Terendah)':
                query = query.order_by(SociollaReferensi.min_price.asc())
            elif sort_val == 'Harga (Tertinggi)':
                query = query.order_by(SociollaReferensi.min_price.desc())
                
            total_items = query.count()
            
            total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
            safe_page = max(1, min(page, total_pages))
            
            if total_items > 0:
                results = query.offset((safe_page - 1) * items_per_page).limit(items_per_page).all()
            else:
                results = []
            
            items = []
            for r in results:
                # Data SQLite -> Dict yang cocok dengan ekspektasi Frontend
                items.append({
                    "brand": r.brand,
                    "product_name": r.product_name,
                    "category": r.category,
                    "slug": r.product_name.lower().replace(" ", "-"),
                    "ingredients": "", # Tidak selalu ditarik full oleh ref
                    "min_price": r.min_price,
                    "rating": r.rating_sociolla,
                    "image_url": r.url_sociolla,
                })
                
            return {
                "items": items,
                "total_pages": total_pages,
                "current_page": safe_page,
                "total_items": total_items
            }

    def _fallback_json_load(
        self, page, items_per_page, category_filter,
        keyword="", min_price=0.0, max_price=float('inf'),
        sort_val="Rating (Tertinggi)"
    ) -> Dict[str, Any]:
        """Menyediakan data dari file JSON hasil Scraping dengan In-Memory Caching."""
        
        # 1. Cek apakah cache sudah terisi
        if self._cached_products is None:
            json_file = Path("app/scraping/data/products_sociolla_ALL.json")
            
            self._cached_products = []
            if json_file.exists():
                try:
                    with json_file.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._cached_products = data if isinstance(data, list) else data.get("products", [])
                except Exception as e:
                    logger.error(f"Gagal memuat JSON fallback: {e}")
                
        all_cats = set(p.get("category", "") for p in self._cached_products)
        print(f"DEBUG semua kategori di JSON: {all_cats}")
        
        # 2. Filter data dari Memori (Bukan Disk) - Kecepatan O(N) di RAM
        def matches_filter(prod_cat, filter_cat):
            if filter_cat == "All": return True
            
            ui_to_json = {
                "Serum": ["Face Serum"],
                "Moisturizer": ["Face Gel", "Moisturizer"],
                "Cleanser": ["Face Wash", "Micellar Water", "Scrub & Exfoliator"],
                "Toner": ["Face Mist", "Toner"],
                "Sunscreen": ["Sunscreen"],
            }
            
            valid_cats = ui_to_json.get(filter_cat, [filter_cat])
            return prod_cat in valid_cats

        filtered_products = []
        for p in self._cached_products:
            if not matches_filter(p.get("category", ""), category_filter):
                continue
                
            if keyword:
                kw = keyword.lower()
                name = p.get('product_name', p.get('name', '')).lower()
                brand = p.get('brand', '').lower()
                if kw not in name and kw not in brand:
                    continue
                    
            price = p.get('min_price', p.get('price', 0))
            if price < min_price or price > max_price:
                continue
                
            filtered_products.append(p)
            
        if sort_val == 'Rating (Tertinggi)':
            filtered_products.sort(key=lambda x: x.get('average_rating', x.get('rating', 0)), reverse=True)
        elif sort_val == 'Harga (Terendah)':
            filtered_products.sort(key=lambda x: x.get('min_price', x.get('price', float('inf'))))
        elif sort_val == 'Harga (Tertinggi)':
            filtered_products.sort(key=lambda x: x.get('min_price', x.get('price', 0)), reverse=True)
                
        total_items = len(filtered_products)
        if total_items == 0:
            return {"items": [], "total_pages": 1, "current_page": 1, "total_items": 0}
            
        total_pages = (total_items + items_per_page - 1) // items_per_page
        safe_page =max(1, min(page, total_pages))
        start_idx = (safe_page - 1) * items_per_page
        
        return {
            "items": filtered_products[start_idx:start_idx+items_per_page],
            "total_pages": total_pages,
            "current_page": safe_page,
            "total_items": total_items
        }

    def analyze_routine(self, routine_list: List[Dict[str, Any]], kota: str = "") -> Dict[str, Any]:
        result = {"warnings": [], "suggestions": [], "weather": None, "status": "empty"}
        if not routine_list:
            return result

        result["status"] = "safe" 
        routine_ingredients = set()
        
        for prod in routine_list:
            ingredients = prod.get("ingredients", "")
            if ingredients:
                routine_ingredients.update(item.strip().lower() for item in ingredients.split(","))

        result["warnings"].extend(SkincareAnalyzer.check_routine_safety(routine_ingredients))

        if self.ingredient_db.is_loaded():
            aggregate = self.ingredient_db.get_aggregate(routine_ingredients)
            result["warnings"].extend(SkincareAnalyzer.check_comedogenicity(aggregate))
            result["warnings"].extend(SkincareAnalyzer.check_irritancy_load(aggregate))

        weather = WeatherService.fetch_weather(kota)
        if weather["status"] == "success":
            result["weather"] = weather
            uv, hum = weather["uv_index"], weather["humidity"]

            has_photosensitive = any(
                kw in ing for ing in routine_ingredients 
                for kw in SkincareAnalyzer.ACTIVE_INGREDIENTS["retinol"] | SkincareAnalyzer.ACTIVE_INGREDIENTS["aha_bha"]
            )
            
            if uv >= 6 and has_photosensitive:
                result["warnings"].append(f"🛑 UV Index {uv} (Sangat Tinggi)! Hindari Retinol/AHA pagi ini atau WAJIB pakai sunscreen tebal.")
                result["status"] = "danger"
            
            if hum < 50:
                result["suggestions"].append(f"💧 Kelembapan {hum}% (Kering). Gunakan pelembap tebal.")

        return result

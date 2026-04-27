import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "reviews_youtube.json"
TEMP_AUDIO_DIR = Path("tmp_audio")
MAX_VIDEO_DURATION_SECONDS = 600  # Skip video > 10 menit, review skincare jarang sepanjang itu


# =============================================================================
# LAYER 1: ANALYZER — Ekstraksi data semantik dari teks transkrip (Pure Logic)
# =============================================================================

class ReviewAnalyzer:
    """
    Stateless analyzer untuk mengekstrak sinyal dari transkrip review.
    Prinsip: tidak ada I/O, tidak ada state, hanya transformasi teks → data.
    """

    INGREDIENT_KEYWORDS: frozenset = frozenset({
        "niacinamide", "retinol", "retinoid", "vitamin c", "ascorbic",
        "salicylic", "hyaluronic", "ceramide", "peptide", "aha", "bha",
        "glycolic", "lactic", "spf", "sunscreen", "kojic", "tranexamic",
        "alpha arbutin", "centella", "snail mucin", "collagen", "bakuchiol",
        "azelaic", "benzoyl peroxide", "zinc", "squalane",
    })

    SENTIMENT_POSITIVE: frozenset = frozenset({
        "bagus", "recommended", "rekomendasi", "cocok", "suka", "mantap",
        "worth it", "worth", "enak", "lembap", "cerah", "glowing", "ampuh",
        "efektif", "keren", "favorit", "holy grail", "repurchase", "beli lagi",
        "puas", "love", "works", "berhasil", "noticeable", "hasilnya keliatan",
    })

    SENTIMENT_NEGATIVE: frozenset = frozenset({
        "jelek", "tidak cocok", "ga cocok", "iritasi", "breakout", "purging",
        "berminyak", "lengket", "kecewa", "disappointing", "tidak efektif",
        "ga efektif", "waste", "rugi", "gatal", "merah", "perih", "panas",
        "menyumbat", "comedogenic",
    })

    # Setiap klaim dipasangkan dengan keyword trigger-nya (format: tuple[str, list[str]])
    CLAIM_PATTERNS: List[tuple] = [
        ("cocok untuk kulit berminyak",  ["berminyak", "oily"]),
        ("cocok untuk kulit kering",     ["kering", "dry"]),
        ("mencerahkan kulit",            ["cerah", "bright", "glowing", "putih", "luminous"]),
        ("melembapkan",                  ["lembap", "moist", "hydrat", "lembab"]),
        ("mengurangi jerawat",           ["jerawat", "acne", "pimple", "breakout"]),
        ("mengecilkan pori-pori",        ["pori", "pore", "minimiz"]),
        ("anti aging",                   ["kerutan", "aging", "wrinkle", "garis halus"]),
        ("menenangkan kulit sensitif",   ["sensitif", "sensitive", "kemerahan", "redness"]),
    ]

    @staticmethod
    def extract_mentioned_ingredients(transcript: str) -> List[str]:
        """Scan O(N·K) — cari keyword bahan aktif dalam transkrip."""
        t = transcript.lower()
        return [kw for kw in ReviewAnalyzer.INGREDIENT_KEYWORDS if kw in t]

    @staticmethod
    def analyze_sentiment(transcript: str) -> str:
        """Hitung sentimen dominan dari frekuensi keyword positif vs negatif."""
        t = transcript.lower()
        pos = sum(1 for kw in ReviewAnalyzer.SENTIMENT_POSITIVE if kw in t)
        neg = sum(1 for kw in ReviewAnalyzer.SENTIMENT_NEGATIVE if kw in t)

        if pos == 0 and neg == 0:
            return "neutral"
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "mixed"

    @staticmethod
    def extract_claims(transcript: str) -> List[str]:
        """Cocokkan pola klaim produk dari transkrip."""
        t = transcript.lower()
        return [
            claim for claim, keywords in ReviewAnalyzer.CLAIM_PATTERNS
            if any(kw in t for kw in keywords)
        ]


# =============================================================================
# LAYER 2: TRANSCRIBER — Wraps faster-whisper dengan lazy loading
# =============================================================================

class AudioTranscriber:
    """
    Singleton-style transcriber dengan lazy model loading.
    Model ~500MB hanya didownload sekali dan di-cache oleh faster-whisper.
    """

    _model = None
    MODEL_SIZE = "small"  # 'small' cukup akurat untuk Bahasa Indonesia dan ringan di CPU

    @classmethod
    def _get_model(cls):
        if cls._model is not None:
            return cls._model

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper belum terinstall. Jalankan: pip install faster-whisper"
            )

        logger.info(
            f"Memuat Whisper model '{cls.MODEL_SIZE}'... "
            "(Download ~500MB jika belum pernah dijalankan)"
        )
        # OPTIMASI: cpu_threads=2 mencegah over-utilization saat dijalankan paralel
        cls._model = WhisperModel(cls.MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=2)
        logger.info("Model Whisper siap digunakan.")
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: Path) -> str:
        """
        Transkripsi file audio ke teks Bahasa Indonesia.
        Menggunakan VAD filter untuk otomatis skip bagian hening (iklan, jeda).
        Return string kosong jika gagal — tidak raise exception ke caller.
        """
        if not audio_path.exists():
            logger.error(f"File audio tidak ditemukan: {audio_path}")
            return ""

        try:
            model = cls._get_model()
            segments, _ = model.transcribe(
                str(audio_path),
                language="id",
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            # Join semua segment menjadi satu string bersih
            return " ".join(seg.text for seg in segments).strip()

        except Exception as e:
            logger.error(f"Gagal transkripsi {audio_path.name}: {e}")
            return ""


# =============================================================================
# LAYER 3: SCRAPER — Orchestrator utama (search + download + pipeline)
# =============================================================================

class YouTubeReviewScraper:
    """
    Orchestrator pipeline: search YouTube → download audio → transcribe → analyze → simpan.
    Setiap sub-proses diisolasi agar satu kegagalan tidak membatalkan proses lainnya.
    """

    def __init__(
        self,
        output_file: Path = OUTPUT_FILE,
        temp_dir: Path = TEMP_AUDIO_DIR,
    ):
        self.output_file = output_file
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    # --- Search ---

    def search_videos(self, product_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Cari video YouTube tanpa mendownload apapun (extract_flat=True).
        Query dioptimasi untuk konten review skincare Indonesia.
        """
        _require_ytdlp()

        import yt_dlp

        query = f"{product_name} review skincare"
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                entries = info.get("entries", []) if info else []

            return [
                {
                    "video_id": e.get("id", ""),
                    "title": e.get("title", ""),
                    "url": f"https://youtube.com/watch?v={e.get('id', '')}",
                    "duration": e.get("duration") or 0,
                    "uploader": e.get("uploader", ""),
                }
                for e in entries
                if e and e.get("id")
            ]

        except Exception as e:
            logger.error(f"Gagal search YouTube untuk '{product_name}': {e}")
            return []

    # --- Download ---

    def download_audio(self, video_url: str, video_id: str) -> Optional[Path]:
        """
        Download audio terbaik tersedia tanpa konversi.
        yt-dlp memilih format m4a/webm secara otomatis.
        Return path file audio, atau None jika gagal.
        """
        _require_ytdlp()

        import yt_dlp

        output_template = str(self.temp_dir / f"{video_id}.%(ext)s")

        def _duration_filter(info, *, incomplete):
            duration = info.get("duration")
            if duration and duration > MAX_VIDEO_DURATION_SECONDS:
                return f"Video terlalu panjang ({duration}s), dilewati."
            return None

        ydl_opts = {
            "format": "worstaudio[ext=m4a]/worstaudio",  # OPTIMASI: File terkecil, hemat memori & I/O
            "extract_audio": True,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "match_filter": _duration_filter,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Temukan file yang dihasilkan (ekstensi bisa m4a, webm, dsb)
            candidates = list(self.temp_dir.glob(f"{video_id}.*"))
            return candidates[0] if candidates else None

        except Exception as e:
            logger.error(f"Gagal download audio {video_id}: {e}")
            return None

    # --- Persistence ---

    def _load_existing(self) -> Dict[str, Any]:
        """Muat data review existing agar bisa di-merge (tidak overwrite)."""
        if not self.output_file.exists():
            return {"metadata": {}, "reviews": {}}

        try:
            with self.output_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Gagal baca {self.output_file.name}, mulai fresh: {e}")
            return {"metadata": {}, "reviews": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        """Tulis JSON ke disk dengan metadata timestamp otomatis."""
        data["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "total_products_reviewed": len(data.get("reviews", {})),
        }
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with self.output_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Pipeline Utama ---

    def run_pipeline(
        self,
        product_name: str,
        product_slug: str,
        max_videos: int = 3,
        progress_callback=None,
    ) -> List[Dict[str, Any]]:
        """
        Entry point utama. Jalankan full pipeline untuk satu produk.
        progress_callback(str) opsional — dipakai oleh NiceGUI untuk update UI secara real-time.
        Return list review baru yang berhasil diproses di run ini.
        """

        def notify(msg: str) -> None:
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        notify(f"Mencari video review: '{product_name}'...")
        videos = self.search_videos(product_name, max_results=max_videos)

        if not videos:
            notify("Tidak ada video ditemukan.")
            return []

        all_data = self._load_existing()

        # Pakai set untuk O(1) lookup: skip video yang sudah pernah diproses
        existing_ids: set = {
            r["video_id"]
            for r in all_data["reviews"].get(product_slug, [])
        }

        new_reviews: List[Dict[str, Any]] = []

        def process_single_video(video: Dict[str, Any], idx: int) -> Optional[Dict[str, Any]]:
            """Fungsi worker yang akan dieksekusi oleh thread."""
            video_id = video["video_id"]
            prefix = f"[{idx}/{len(videos)}]"

            if video_id in existing_ids:
                notify(f"{prefix} Sudah diproses sebelumnya, skip.")
                return None

            notify(f"{prefix} Download audio: {video['title'][:50]}...")
            audio_path = self.download_audio(video["url"], video_id)

            if not audio_path:
                notify(f"{prefix} Download gagal, lanjut ke video berikutnya.")
                return None

            notify(f"{prefix} Transkripsi berjalan (Paralel)...")
            transcript = AudioTranscriber.transcribe(audio_path)

            # Hapus file audio dari disk segera setelah transkripsi selesai (hemat storage O(1))
            audio_path.unlink(missing_ok=True)

            if not transcript:
                notify(f"{prefix} Transkripsi kosong, skip.")
                return None

            review_entry = {
                "video_id": video_id,
                "video_title": video["title"],
                "uploader": video["uploader"],
                "source_url": video["url"],
                "transcript": transcript,
                "mentioned_ingredients": ReviewAnalyzer.extract_mentioned_ingredients(transcript),
                "sentiment": ReviewAnalyzer.analyze_sentiment(transcript),
                "claims": ReviewAnalyzer.extract_claims(transcript),
            }

            notify(f"{prefix} OK — sentimen: {review_entry['sentiment']}, "
                   f"bahan disebut: {len(review_entry['mentioned_ingredients'])}")
            return review_entry

        # OPTIMASI: Eksekusi Konkuren / Paralel menggunakan 2 Worker Thread
        # Sementara Worker 1 sibuk transkripsi (CPU), Worker 2 bisa download video selanjutnya (Network/IO)
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit semua tasks
            futures = {
                executor.submit(process_single_video, video, idx): video
                for idx, video in enumerate(videos, start=1)
            }
            
            # As_completed memastikan data yang selesai duluan langsung diproses, tanpa nge-blok
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        new_reviews.append(result)
                except Exception as e:
                    logger.error(f"Error pada thread pemrosesan video: {e}")

        if new_reviews:
            if product_slug not in all_data["reviews"]:
                all_data["reviews"][product_slug] = []
            all_data["reviews"][product_slug].extend(new_reviews)
            self._save(all_data)
            notify(f"Selesai. {len(new_reviews)} review baru disimpan.")
        else:
            notify("Tidak ada review baru yang berhasil diproses.")

        return new_reviews


# =============================================================================
# HELPERS
# =============================================================================

def _require_ytdlp() -> None:
    """Raise RuntimeError dengan pesan jelas jika yt-dlp belum terinstall."""
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        raise RuntimeError("yt-dlp belum terinstall. Jalankan: pip install yt-dlp")


def check_dependencies() -> bool:
    """
    Validasi semua dependency sebelum pipeline dijalankan.
    Return True jika semua siap, False jika ada yang kurang.
    """
    issues = []

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        issues.append("yt-dlp   → pip install yt-dlp")

    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        issues.append("faster-whisper → pip install faster-whisper")

    if not shutil.which("ffmpeg"):
        issues.append(
            "ffmpeg   → https://ffmpeg.org/download.html "
            "(atau: winget install ffmpeg / brew install ffmpeg)"
        )

    if issues:
        print("\n[DEPENDENCY CHECK GAGAL] Install berikut terlebih dahulu:\n")
        for issue in issues:
            print(f"  - {issue}")
        print()
        return False

    print("[DEPENDENCY CHECK] Semua dependency tersedia.")
    return True


# =============================================================================
# STANDALONE ENTRY POINT
# Jalankan: python anggota4_review_scraper.py
# Konsisten dengan pola anggota2_scraper.py dan anggota3_halal_mapper.py
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 55)
    print("Pipeline Review Scraper — YouTube")
    print("=" * 55)

    if not check_dependencies():
        exit(1)

    products_file = DATA_DIR / "products_sociolla.json"
    if not products_file.exists():
        print(f"Error: {products_file} tidak ditemukan. Jalankan anggota1_scraper.py dulu.")
        exit(1)

    with products_file.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    products = raw.get("products", [])[:5]  # Batasi 5 produk untuk test awal
    scraper = YouTubeReviewScraper()

    for prod in products:
        name = prod.get("product_name", "")
        slug = prod.get("slug") or name.lower().replace(" ", "-")
        if not name:
            continue

        print(f"\n» Produk: {name}")
        results = scraper.run_pipeline(
            product_name=name,
            product_slug=slug,
            max_videos=2,
        )
        print(f"  Hasil: {len(results)} review baru tersimpan.")

    print("\n" + "=" * 55)
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 55)
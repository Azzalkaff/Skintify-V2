import requests

def get_environmental_baseline(kota):
    """
    Mengambil data lingkungan dari WeatherAPI untuk merancang Skincare Starter Kit.
    Versi Final: Anti-freeze (timeout), Clean Return (Dictionary), dan Bebas Print() di fungsi inti.
    """
    # MASUKKAN API KEY WEATHERAPI KAMU DI SINI
    API_KEY = "b4322057e0a44598929105728261704"


    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={kota}&days=3&lang=id"

    try:
        # Timeout 5 detik sangat krusial agar UI Desktop NiceGUI tidak freeze/hang
        response = requests.get(url, timeout=5)
        data = response.json()

        # Hapus data yang tidak dipakai (early trimming)
        data.pop("alerts", None)
        
        if response.status_code == 200:
            data = response.json()
            
            return {
    "success": True,
    "kota": data["location"]["name"],
    
    # CURRENT WEATHER
    "suhu": data["current"]["temp_c"],
    "feels_like": data["current"]["feelslike_c"],
    "kelembapan": data["current"]["humidity"],
    "uv_index": data["current"]["uv"],
    "status_cuaca": data["current"]["condition"]["text"],

    # HOURLY FORECAST (ambil beberapa jam pertama saja agar ringan)
    "hourly_forecast": [
        {
            "jam": hour["time"],
            "suhu": hour["temp_c"],
            "peluang_hujan": hour["chance_of_rain"],
            "kondisi": hour["condition"]["text"]
        }
        for hour in data["forecast"]["forecastday"][0]["hour"] if hour["time"].endswith(("06:00", "12:00", "18:00", "21:00"))
    ],

    # DAILY FORECAST
    "daily_forecast": [
        {
            "tanggal": day["date"],
            "range_suhu": f"{day['day']['mintemp_c']}-{day['day']['maxtemp_c']}",
            "hujan": day["day"]["daily_chance_of_rain"],
            "kondisi": day["day"]["condition"]["text"]
        }
        for day in data["forecast"]["forecastday"][:3]
    ]
}
        else:
            return {
                "success": False,
                "error_message": f"Gagal memuat data (Error {response.status_code}). Pastikan nama kota diketik dengan benar."
            }
            
    except requests.exceptions.RequestException:
        # Fallback jika internet user mati atau server API down (Mencegah Single Point of Failure)
        return {
            "success": False,
            "error_message": "Koneksi internet terputus. Sistem akan menggunakan mode Default Routine tanpa filter lingkungan."
        }

# =====================================================================
# BLOK TESTING (Simulasi Logika Rules Engine sebelum dijahit ke NiceGUI)
# =====================================================================
if __name__ == "__main__":
    # Nanti di aplikasi GUI, variabel ini diambil dari input form profil user
    kota_target = "Jakarta" 
    gaya_hidup = "Indoor"  # Opsi: "Indoor" (Ruangan Ber-AC) atau "Outdoor" (Lapangan/Luar Ruangan)
    
    print(f"Memproses Profil Iklim untuk domisili: {kota_target}...\n")
    iklim = get_environmental_baseline(kota_target)
    
    if iklim["success"]:
        print("="*65)
        print("🌍 DATA LINGKUNGAN DOMISILI (WeatherAPI)")
        print("="*65)
        print(f"📍 Kota       : {iklim['kota']}")
        print(f"🌡️ Suhu       : {iklim['suhu']} °C (Feels like: {iklim['feels_like']} °C)")
        print(f"💧 Kelembapan : {iklim['kelembapan']}%")
        print(f"☀️ UV Index   : {iklim['uv_index']}")
        print(f"🌤️ Kondisi    : {iklim['status_cuaca']}")

        print("\n⏰ HOURLY FORECAST (6 Jam Ke Depan)")
        print("-" * 65)
        for h in iklim["hourly_forecast"]:
            print(f"{h['jam']} | {h['suhu']}°C | 🌧️ {h['peluang_hujan']}% | {h['kondisi']}")

        print("\n📅 DAILY FORECAST (3 Hari)")
        print("-" * 65)
        for d in iklim["daily_forecast"]:
            print(f"{d['tanggal']} | 🌡️ {d['range_suhu']}°C | 🌧️ {d['hujan']}% | {d['kondisi']}")
                
        print("\n💡 RULES ENGINE: PENYUSUNAN STARTER KIT (SMART HEURISTIC)")
        print("-" * 65)
        
        # Rule 1: Logika Kelembapan + Gaya Hidup (Menjawab Kritik Indoor vs Outdoor / TEWL)
        if iklim['kelembapan'] > 75 and gaya_hidup == "Outdoor":
            print("[FILTER TEKSTUR] 🔴 Kelembapan Tinggi & Aktivitas Outdoor.")
            print("                 Sistem memblokir pelembap bertekstur Krim Tebal.")
            print("                 Rekomendasi aman: Gel / Water-based Moisturizer.")
        elif iklim['kelembapan'] > 75 and gaya_hidup == "Indoor":
            print("[FILTER TEKSTUR] 🟡 Kelembapan Luar Tinggi, TAPI dominan AC (Indoor).")
            print("                 Sistem merekomendasikan Cream/Lotion ceramide untuk")
            print("                 mencegah dehidrasi kulit akibat AC ruangan yang kering.")
        else:
            print("[FILTER TEKSTUR] ✅ Kelembapan Normal/Kering.")
            print("                 Aman merekomendasikan produk dengan tekstur Krim.")

        print()

        # Rule 2: Logika UV Index -> Kewajiban Sunscreen (Standar Mutlak WHO)
        if iklim['uv_index'] >= 6:
            print("[FILTER PROTEKSI] 🔴 UV Index Bahaya/Ekstrem!")
            print("                  Sistem MENGUNCI rutinitas. User WAJIB menambah Sunscreen SPF 50+.")
            print("                  Peringatan keras: Jangan gunakan AHA/BHA di pagi hari.")
        elif iklim['uv_index'] >= 3:
            print("[FILTER PROTEKSI] 🟡 UV Index Moderat.")
            print("                  User diwajibkan menggunakan Sunscreen SPF 30+.")
        else:
            print("[FILTER PROTEKSI] ✅ UV Index Rendah (Aman).")
            print("                  Gunakan Sunscreen SPF 15-30 sebagai proteksi dasar blue-light.")
            
        print("="*65)
    else:
        # Jika API gagal (misal tidak ada internet), tampilkan error tanpa bikin program crash
        print(f"❌ ERROR UI: {iklim['error_message']}")
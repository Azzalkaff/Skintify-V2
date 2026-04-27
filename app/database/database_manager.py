import sqlite3

class BasisData:
    """Manajer Database SQLite sederhana untuk pemula (Separation of Concerns)."""
    
    # Nama file database yang akan terbuat otomatis di folder proyek
    DB_NAMA = "data_skintify.db"

    @staticmethod
    def inisialisasi():
        """Membuat file database dan tabel jika belum ada."""
        with sqlite3.connect(BasisData.DB_NAMA) as koneksi:
            kursor = koneksi.cursor()
            # Membuat tabel pengguna
            kursor.execute('''
                CREATE TABLE IF NOT EXISTS pengguna (
                    email TEXT PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT NOT NULL
                )
            ''')
            koneksi.commit()

    @staticmethod
    def cek_identifier_terdaftar(identifier: str) -> bool:
        """Mengembalikan True jika email atau username sudah ada di database."""
        with sqlite3.connect(BasisData.DB_NAMA) as koneksi:
            kursor = koneksi.cursor()
            # Tanda '?' digunakan untuk mencegah SQL Injection (Keamanan Dasar)
            kursor.execute('SELECT email FROM pengguna WHERE email = ? OR username = ?', (identifier, identifier))
            return kursor.fetchone() is not None

    @staticmethod
    def tambah_pengguna(email: str, username: str, password: str) -> bool:
        """Memasukkan pengguna baru ke database permanen."""
        try:
            with sqlite3.connect(BasisData.DB_NAMA) as koneksi:
                kursor = koneksi.cursor()
                kursor.execute('INSERT INTO pengguna (email, username, password) VALUES (?, ?, ?)', (email, username, password))
                koneksi.commit()
            return True
        except sqlite3.IntegrityError:
            # Gagal karena email atau username mungkin sudah ada (Duplikat)
            return False 

    @staticmethod
    def verifikasi_login(identifier: str, password: str) -> bool:
        """Mengecek apakah kombinasi email/username dan password cocok di database."""
        with sqlite3.connect(BasisData.DB_NAMA) as koneksi:
            kursor = koneksi.cursor()
            kursor.execute('SELECT password FROM pengguna WHERE email = ? OR username = ?', (identifier, identifier))
            hasil = kursor.fetchone()
            
            # Jika hasil ditemukan, dan password cocok
            if hasil and hasil[0] == password:
                return True
            return False
import sqlite3
import re
from pathlib import Path
from datetime import date, datetime, timedelta
from core.migrations import migrate_schema
from core.utils import DENDA_PER_HARI

DB_PATH = Path(__file__).resolve().parent / "sewain.db"
PREFIX_KATEGORI = {
    "Audio": "AUD",
    "Fotografi": "FTG",
    "Visual": "VIS",
    "Musik": "MSK",
    "Logistik": "LOG",
    "Kelistrikan": "KLS",
    "Pencahayaan": "LGT",
    "Komunikasi": "KOM",
    "Dekorasi": "DKR",
    "Sekretariat": "SKR",
    "Kesehatan": "KSH",
    "Kebersihan": "KBR",
    "Perkakas": "PRK",
    "Atribut": "ATB",
    "Konsumsi": "KNS",
}
KONDISI_BARANG = ("Baik", "Rusak Ringan", "Rusak Berat")
KATEGORI_SEED = (
    ("KAT-001", "Atribut", "Pakaian khusus, identitas panitia, dan kostum pementasan."),
    ("KAT-002", "Audio", "Peralatan pengeras dan pengolah suara untuk kegiatan indoor maupun outdoor."),
    ("KAT-003", "Dekorasi", "Properti dan perlengkapan untuk menghias area panggung atau ruangan."),
    ("KAT-004", "Fotografi", "Perangkat untuk keperluan dokumentasi visual, pengambilan foto, dan video."),
    ("KAT-005", "Kebersihan", "Peralatan sanitasi untuk menjaga kebersihan lokasi kegiatan dan sekretariat."),
    ("KAT-006", "Kelistrikan", "Perangkat penyalur dan pendistribusi daya listrik lokasi kegiatan."),
    ("KAT-007", "Kesehatan", "Perlengkapan medis dasar untuk penanganan darurat dan keselamatan."),
    ("KAT-008", "Komunikasi", "Alat koordinasi dan komunikasi jarak jauh antarpanitia di lapangan."),
    ("KAT-009", "Konsumsi", "Perlengkapan penunjang penyediaan makanan dan minuman kegiatan."),
    ("KAT-010", "Logistik", "Perlengkapan operasional acara, pemetaan area, dan kebutuhan lapangan."),
    ("KAT-011", "Musik", "Instrumen dan alat musik pendukung untuk latihan maupun pertunjukan."),
    ("KAT-012", "Pencahayaan", "Perlengkapan tata cahaya dan tata panggung untuk mempercantik suasana event."),
    ("KAT-013", "Perkakas", "Alat-alat teknik manual untuk perbaikan dan persiapan teknis acara."),
    ("KAT-014", "Sekretariat", "Peralatan penunjang administrasi, operasional ruang UKM, dan rapat."),
    ("KAT-015", "Visual", "Media presentasi dan penayangan konten visual dalam acara."),
)
KATEGORI_LAMA = {
    "Alat Musik": "Musik",
    "Alat Tulis Kantor": "Sekretariat",
    "Dokumentasi": "Fotografi",
    "Elektronik": "Visual",
    "Furniture": "Sekretariat",
    "Keamanan": "Logistik",
    "Kesehatan dan P3K": "Kesehatan",
    "Komputer dan IT": "Sekretariat",
    "Jaringan": "Komunikasi",
    "Laboratorium": "Perkakas",
    "Olahraga": "Logistik",
    "Penyimpanan": "Logistik",
    "Perlengkapan Acara": "Logistik",
    "Perlengkapan Rapat": "Sekretariat",
    "Publikasi": "Visual",
    "Seni dan Dekorasi": "Dekorasi",
    "Seragam dan Atribut": "Atribut",
    "Tenda dan Lapangan": "Logistik",
}
INVENTARIS_SEED = (
    ("ATB-001", "Atribut", "Rompi Panitia", 1, 1, 15000, "Gudang UKM", ()),
    ("ATB-002", "Atribut", "Jas Almamater/Organisasi", 1, 1, 25000, "Gudang UKM", ()),
    ("AUD-001", "Audio", "Speaker Portable", 6, 4, 1250000, "Gudang UKM", ()),
    ("AUD-002", "Audio", "Mikrofon Wireless", 6, 0, 675000, "Gudang UKM", ()),
    ("AUD-003", "Audio", "Mixer Audio 8 Channel", 2, 0, 2200000, "Gudang UKM", ()),
    ("AUD-004", "Audio", "Cable Jack Sound", 1, 1, 35000, "Gudang UKM", ()),
    ("DKR-001", "Dekorasi", "Stand Banner", 1, 1, 45000, "Gudang UKM", ()),
    ("DKR-002", "Dekorasi", "Backdrop", 1, 1, 150000, "Gudang UKM", ()),
    ("DKR-003", "Dekorasi", "Karpet Merah", 1, 0, 75000, "Gudang UKM", ()),
    ("DKR-004", "Dekorasi", "Bendera UKM", 1, 1, 20000, "Gudang UKM", ()),
    ("FTG-001", "Fotografi", "Tripod Kamera", 5, 4, 450000, "Sekretariat", ()),
    ("FTG-002", "Fotografi", "Kamera DSLR Canon", 2, 2, 7200000, "Sekretariat", ("Kamera DSLR/Mirrorless", "Kamera Mirrorless")),
    ("FTG-003", "Fotografi", "Webcam Logitech", 1, 0, 825000, "Gudang UKM", ("Webcam Logitach",)),
    ("FTG-004", "Fotografi", "Lensa Kamera", 1, 1, 1500000, "Gudang UKM", ("Lensa",)),
    ("FTG-005", "Fotografi", "Memory Card", 1, 1, 120000, "Gudang UKM", ()),
    ("KBR-001", "Kebersihan", "Sapu & Alat Pel", 1, 1, 30000, "Gudang UKM", ()),
    ("KBR-002", "Kebersihan", "Tempat Sampah Portabel", 1, 1, 25000, "Gudang UKM", ()),
    ("KLS-001", "Kelistrikan", "Kabel Roll", 10, 10, 185000, "Gudang UKM", ()),
    ("KLS-002", "Kelistrikan", "Stopkontak Extension", 1, 1, 65000, "Gudang UKM", ()),
    ("KNS-001", "Konsumsi", "Dispenser Air", 1, 1, 85000, "Gudang UKM", ()),
    ("KNS-002", "Konsumsi", "Kompor Portable", 1, 1, 110000, "Gudang UKM", ()),
    ("KNS-003", "Konsumsi", "Termos Es", 1, 1, 70000, "Gudang UKM", ()),
    ("KOM-001", "Komunikasi", "Router Wi-Fi", 2, 0, 575000, "Sekretariat", ()),
    ("KOM-002", "Komunikasi", "Handy Talky", 6, 6, 780000, "Sekretariat", ()),
    ("KOM-003", "Komunikasi", "Megafon", 1, 1, 250000, "Gudang UKM", ()),
    ("KSH-001", "Kesehatan", "Kotak P3K", 3, 3, 225000, "Sekretariat", ()),
    ("KSH-002", "Kesehatan", "Tandu Lipat", 1, 1, 450000, "Gudang UKM", ()),
    ("LGT-001", "Pencahayaan", "Lampu LED Panggung", 8, 8, 340000, "Gudang UKM", ()),
    ("LGT-002", "Pencahayaan", "LED Bar", 1, 1, 420000, "Gudang UKM", ()),
    ("LGT-003", "Pencahayaan", "Stand Lampu", 1, 1, 125000, "Gudang UKM", ()),
    ("LOG-001", "Logistik", "Kursi Lipat", 40, 27, 275000, "Gudang UKM", ()),
    ("LOG-002", "Logistik", "Meja Lipat", 12, 12, 525000, "Gudang UKM", ()),
    ("LOG-003", "Logistik", "Tenda Lipat", 2, 2, 1850000, "Gudang UKM", ("Tenda Lipat/Pleton", "Tenda Pleton")),
    ("LOG-004", "Logistik", "Terpal", 1, 1, 95000, "Gudang UKM", ()),
    ("LOG-005", "Logistik", "Container Box", 1, 1, 135000, "Gudang UKM", ()),
    ("MSK-001", "Musik", "Gitar Akustik", 2, 0, 1125000, "Gudang UKM", ("Gitar Akustik/Listrik",)),
    ("MSK-002", "Musik", "Gitar Elektrik", 1, 0, 1800000, "Gudang UKM", ("Gitar", "Gitar Listrik")),
    ("MSK-003", "Musik", "Bass", 1, 1, 165000, "Gudang UKM", ()),
    ("MSK-004", "Musik", "Keyboard", 1, 1, 3500000, "Gudang UKM", ()),
    ("MSK-005", "Musik", "Drum Set", 1, 1, 4500000, "Gudang UKM", ()),
    ("MSK-006", "Musik", "Amplifier", 1, 1, 1350000, "Gudang UKM", ()),
    ("PRK-001", "Perkakas", "Palu Sidang", 1, 1, 250000, "Sekretariat", ()),
    ("PRK-002", "Perkakas", "Obeng Set", 1, 1, 75000, "Gudang UKM", ()),
    ("PRK-003", "Perkakas", "Tang & Palu", 1, 1, 85000, "Gudang UKM", ()),
    ("PRK-004", "Perkakas", "Isolasi Listrik", 1, 1, 15000, "Gudang UKM", ()),
    ("SKR-001", "Sekretariat", "Laptop ASUS", 3, 3, 8500000, "Sekretariat", ("Laptop",)),
    ("SKR-002", "Sekretariat", "Printer Epson", 1, 1, 2350000, "Sekretariat", ("Printer",)),
    ("SKR-003", "Sekretariat", "Papan Tulis Whiteboard", 2, 2, 650000, "Sekretariat", ("Papan Tulis", "Papan Tulis (Whiteboard)")),
    ("SKR-004", "Sekretariat", "Stapler Besar", 1, 1, 45000, "Gudang UKM", ()),
    ("VIS-001", "Visual", "Proyektor Epson", 4, 0, 4500000, "Sekretariat", ()),
    ("VIS-002", "Visual", "Layar Proyektor Portable", 2, 2, 950000, "Gudang UKM", ("Layar Proyektor (Screen)",)),
    ("VIS-003", "Visual", "Kabel HDMI/VGA", 1, 1, 60000, "Gudang UKM", ()),
)


def _normalized_name(value):
    return "".join(character.casefold() for character in value if character.isalnum())


def normalisasi_kondisi_barang(value):
    if value is None:
        return "Baik"
    normalized = str(value).strip()
    aliases = {
        "Baik": "Baik",
        "baik": "Baik",
        "Perlu perbaikan": "Rusak Ringan",
        "perlu perbaikan": "Rusak Ringan",
        "Rusak": "Rusak Berat",
        "rusak": "Rusak Berat",
        "Rusak ringan": "Rusak Ringan",
        "rusak ringan": "Rusak Ringan",
        "Rusak berat": "Rusak Berat",
        "rusak berat": "Rusak Berat",
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized in KONDISI_BARANG:
        return normalized
    raise ValueError("Pilihan kondisi barang tidak valid.")


def hitung_denda(tanggal_rencana, tanggal_kembali):
    def as_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as error:
                raise ValueError("Format tanggal harus berupa ISO yang valid.") from error
        raise ValueError("Tanggal harus berupa objek date atau teks ISO.")

    tanggal_rencana = as_date(tanggal_rencana)
    tanggal_kembali = as_date(tanggal_kembali)
    lama_terlambat = max(0, (tanggal_kembali - tanggal_rencana).days)
    return lama_terlambat, lama_terlambat * DENDA_PER_HARI


def _category_prefix(conn, kategori_id):
    row = conn.execute("SELECT nama FROM kategori WHERE id=?", (kategori_id,)).fetchone()
    if row is None:
        raise ValueError("Kategori inventaris tidak ditemukan.")
    nama = row["nama"]
    if nama in PREFIX_KATEGORI:
        return PREFIX_KATEGORI[nama]
    letters = re.sub(r"[^A-Za-z]", "", nama).upper()
    return (letters + "XXX")[:3]


def _next_inventory_code(conn, kategori_id):
    prefix = _category_prefix(conn, kategori_id)
    codes = conn.execute(
        "SELECT kode FROM inventaris WHERE kode LIKE ?",
        (f"{prefix}-%",),
    ).fetchall()
    numbers = [
        int(match.group(1))
        for row in codes
        if (match := re.fullmatch(rf"{prefix}-(\d{{3}})", row["kode"]))
    ]
    next_number = max(numbers, default=0) + 1
    return f"{prefix}-{next_number:03d}" if next_number <= 999 else None


def next_inventory_code(kategori_id):
    with connect() as conn:
        return _next_inventory_code(conn, kategori_id)


def _next_category_code(conn):
    codes = conn.execute("SELECT kode FROM kategori WHERE kode LIKE 'KAT-%'").fetchall()
    numbers = [
        int(match.group(1))
        for row in codes
        if (match := re.fullmatch(r"KAT-(\d+)", row["kode"]))
    ]
    return f"KAT-{max(numbers, default=0) + 1:03d}"


def create_category(nama, keterangan):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        kode = _next_category_code(conn)
        cursor = conn.execute(
            "INSERT INTO kategori(kode,nama,keterangan) VALUES(?,?,?)",
            (kode, nama, keterangan),
        )
        conn.commit()
        return kode, cursor.lastrowid


def delete_category(kategori_id):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        count = conn.execute(
            "SELECT COUNT(*) FROM inventaris WHERE kategori_id=?",
            (kategori_id,),
        ).fetchone()[0]
        if count:
            raise ValueError(
                f"Kategori tidak dapat dihapus karena masih digunakan oleh {count} barang."
            )
        conn.execute("DELETE FROM kategori WHERE id=?", (kategori_id,))
        conn.commit()


def create_inventory(nama, kategori_id, jumlah, harga, kondisi, lokasi):
    kondisi = normalisasi_kondisi_barang(kondisi)
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        kode = _next_inventory_code(conn, kategori_id)
        if kode is None:
            raise ValueError("Nomor kode untuk prefix kategori ini sudah mencapai 999.")
        conn.execute(
            """INSERT INTO inventaris
            (kode,nama,kategori_id,jumlah,tersedia,harga,kondisi,lokasi)
            VALUES(?,?,?,?,?,?,?,?)""",
            (kode, nama, kategori_id, jumlah, jumlah, harga, kondisi, lokasi),
        )
        conn.commit()
        return kode


def update_inventory(inventory_id, nama, kategori_id, jumlah, harga, kondisi, lokasi):
    kondisi = normalisasi_kondisi_barang(kondisi)
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute(
            "SELECT kode,kategori_id,jumlah,tersedia FROM inventaris WHERE id=?",
            (inventory_id,),
        ).fetchone()
        if current is None:
            raise ValueError("Barang inventaris tidak ditemukan.")
        borrowed = current["jumlah"] - current["tersedia"]
        if jumlah < borrowed:
            raise ValueError(
                f"Jumlah barang tidak boleh kurang dari {borrowed} unit yang sedang disewa."
            )
        if conn.execute("SELECT 1 FROM kategori WHERE id=?", (kategori_id,)).fetchone() is None:
            raise ValueError("Kategori inventaris tidak ditemukan.")

        kode = current["kode"]
        if kategori_id != current["kategori_id"]:
            kode = _next_inventory_code(conn, kategori_id)
            if kode is None:
                raise ValueError("Nomor kode untuk prefix kategori ini sudah mencapai 999.")
        conn.execute(
            """UPDATE inventaris SET kode=?,nama=?,kategori_id=?,jumlah=?,
            tersedia=?,harga=?,kondisi=?,lokasi=? WHERE id=?""",
            (
                kode,
                nama,
                kategori_id,
                jumlah,
                jumlah - borrowed,
                harga,
                kondisi,
                lokasi,
                inventory_id,
            ),
        )
        conn.commit()
        return kode


def _normalize_inventory_codes(conn):
    items = conn.execute(
        "SELECT id,kode,kategori_id FROM inventaris ORDER BY id"
    ).fetchall()
    reassign = []
    for item in items:
        if item["kategori_id"] is None:
            continue
        prefix = _category_prefix(conn, item["kategori_id"])
        if not re.fullmatch(rf"{prefix}-\d{{3}}", item["kode"]):
            reassign.append(item)

    for item in reassign:
        temporary_code = f"__MIGRATING__{item['id']}"
        while conn.execute(
            "SELECT 1 FROM inventaris WHERE kode=?", (temporary_code,)
        ).fetchone():
            temporary_code += "_"
        conn.execute(
            "UPDATE inventaris SET kode=? WHERE id=?",
            (temporary_code, item["id"]),
        )

    for item in reassign:
        kode = _next_inventory_code(conn, item["kategori_id"])
        if kode is None:
            raise ValueError(
                f"Nomor kode untuk inventaris ID {item['id']} sudah mencapai 999."
            )
        conn.execute("UPDATE inventaris SET kode=? WHERE id=?", (kode, item["id"]))

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON"); migrate_schema(conn)
    return conn

def _seed(conn):
    conn.executescript("""
    DROP TABLE IF EXISTS admins;
    CREATE TABLE IF NOT EXISTS kategori (
      id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE NOT NULL,
      nama TEXT UNIQUE NOT NULL, keterangan TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS mahasiswa (
      id INTEGER PRIMARY KEY AUTOINCREMENT, nim TEXT UNIQUE NOT NULL,
      nama TEXT NOT NULL, prodi TEXT DEFAULT '', no_hp TEXT DEFAULT '', email TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS inventaris (
      id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE NOT NULL,
      nama TEXT NOT NULL, kategori_id INTEGER, jumlah INTEGER NOT NULL DEFAULT 0,
        tersedia INTEGER NOT NULL DEFAULT 0, harga INTEGER NOT NULL DEFAULT 0,
        kondisi TEXT DEFAULT 'Baik', lokasi TEXT DEFAULT '',
      FOREIGN KEY(kategori_id) REFERENCES kategori(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS peminjaman (
      id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE NOT NULL,
      mahasiswa_id INTEGER NOT NULL, tanggal_pinjam TEXT NOT NULL,
      tanggal_rencana_kembali TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Dipinjam',
      catatan TEXT DEFAULT '', FOREIGN KEY(mahasiswa_id) REFERENCES mahasiswa(id)
    );
    CREATE TABLE IF NOT EXISTS detail_peminjaman (
      id INTEGER PRIMARY KEY AUTOINCREMENT, peminjaman_id INTEGER NOT NULL,
        inventaris_id INTEGER, kode_barang TEXT NOT NULL DEFAULT '',
        nama_barang TEXT NOT NULL DEFAULT '', harga_satuan INTEGER NOT NULL DEFAULT 0,
        jumlah INTEGER NOT NULL, kondisi_barang TEXT,
      FOREIGN KEY(peminjaman_id) REFERENCES peminjaman(id) ON DELETE CASCADE,
        FOREIGN KEY(inventaris_id) REFERENCES inventaris(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS pengembalian (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      peminjaman_id INTEGER NOT NULL UNIQUE,
      tanggal_pengembalian TEXT NOT NULL,
      status_pengembalian TEXT NOT NULL,
      kondisi_barang TEXT NOT NULL DEFAULT 'Baik',
      lama_terlambat INTEGER NOT NULL DEFAULT 0,
      denda_per_hari INTEGER NOT NULL DEFAULT 0,
      total_denda INTEGER NOT NULL DEFAULT 0,
      catatan TEXT DEFAULT '',
      FOREIGN KEY(peminjaman_id) REFERENCES peminjaman(id) ON DELETE CASCADE
    );
    CREATE TRIGGER IF NOT EXISTS prevent_category_delete_with_inventory
    BEFORE DELETE ON kategori
    WHEN EXISTS (SELECT 1 FROM inventaris WHERE kategori_id=OLD.id)
    BEGIN
      SELECT RAISE(ABORT, 'Kategori masih digunakan oleh barang inventaris.');
    END;
    """)
    conn.executemany(
        """INSERT INTO kategori(kode,nama,keterangan) VALUES(?,?,?)
        ON CONFLICT(nama) DO UPDATE SET
          kode=excluded.kode,keterangan=excluded.keterangan""",
        KATEGORI_SEED,
    )
    kategori_ids = {
        row["nama"]: row["id"]
        for row in conn.execute("SELECT id,nama FROM kategori").fetchall()
    }
    for nama_lama, nama_baru in KATEGORI_LAMA.items():
        id_lama = kategori_ids.get(nama_lama)
        if id_lama is not None:
            conn.execute(
                "UPDATE inventaris SET kategori_id=? WHERE kategori_id=?",
                (kategori_ids[nama_baru], id_lama),
            )
            conn.execute("DELETE FROM kategori WHERE id=?", (id_lama,))
    if conn.execute("SELECT COUNT(*) FROM mahasiswa").fetchone()[0] == 0:
        conn.executemany("INSERT INTO mahasiswa(nim,nama,prodi,no_hp,email) VALUES(?,?,?,?,?)", [
            ("2401001","Nadia Putri","Administrasi Bisnis","081234567801","nadia@example.com"),
            ("2401002","Rizky Pratama","Teknik Informatika","081234567802","rizky@example.com"),
            ("2401003","Salsa Maharani","Akuntansi","081234567803","salsa@example.com"),
        ])
    kategori_ids = {
        row["nama"]: row["id"]
        for row in conn.execute("SELECT id,nama FROM kategori").fetchall()
    }
    alias_to_seed = {
        _normalized_name(alias): seed
        for seed in INVENTARIS_SEED
        for alias in (seed[2], *seed[7])
    }
    matched_ids = {}
    for item in conn.execute("SELECT id,nama FROM inventaris ORDER BY id").fetchall():
        seed = alias_to_seed.get(_normalized_name(item["nama"]))
        if seed and seed[0] not in matched_ids:
            matched_ids[seed[0]] = item["id"]

    for item in conn.execute("SELECT id FROM inventaris").fetchall():
        temporary_code = f"__SEEDING__{item['id']}"
        while conn.execute(
            "SELECT 1 FROM inventaris WHERE kode=?", (temporary_code,)
        ).fetchone():
            temporary_code += "_"
        conn.execute(
            "UPDATE inventaris SET kode=? WHERE id=?",
            (temporary_code, item["id"]),
        )

    next_id = conn.execute("SELECT COALESCE(MAX(id),0) FROM inventaris").fetchone()[0]
    for kode, kategori, nama, jumlah, tersedia, harga, lokasi, _aliases in INVENTARIS_SEED:
        item_id = matched_ids.get(kode)
        if item_id is None:
            next_id += 1
            cursor = conn.execute(
                """INSERT INTO inventaris
                (kode,nama,kategori_id,jumlah,tersedia,harga,kondisi,lokasi)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    f"__SEEDING__{next_id}",
                    nama,
                    kategori_ids[kategori],
                    jumlah,
                    tersedia,
                    harga,
                    "Baik",
                    lokasi,
                ),
            )
            item_id = cursor.lastrowid
        conn.execute(
            """UPDATE inventaris SET kode=?,nama=?,kategori_id=?,jumlah=?,
            tersedia=?,harga=?,lokasi=? WHERE id=?""",
            (kode,nama,kategori_ids[kategori],jumlah,tersedia,harga,lokasi,item_id),
        )

    _normalize_inventory_codes(conn)
    conn.commit()

def init_db(reset=False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with connect() as conn:
        _seed(conn)
        migrate_schema(conn)

def query(sql, params=()):
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def get_student_by_nim(nim):
    with connect() as conn:
        row = conn.execute(
            "SELECT nim,nama,prodi,no_hp,email FROM mahasiswa WHERE nim=?",
            (nim.strip(),),
        ).fetchone()
        return dict(row) if row else None

def execute(sql, params=()):
    with connect() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

def dashboard_stats():
    with connect() as c:
        return {
          "inventaris": c.execute("SELECT COUNT(*) FROM inventaris").fetchone()[0],
          "unit": c.execute("SELECT COALESCE(SUM(jumlah),0) FROM inventaris").fetchone()[0],
          "dipinjam": c.execute("SELECT COUNT(*) FROM peminjaman WHERE status='Dipinjam'").fetchone()[0],
          "terlambat": c.execute("SELECT COUNT(*) FROM peminjaman WHERE status='Dipinjam' AND tanggal_rencana_kembali < ?",(date.today().isoformat(),)).fetchone()[0],
          "mahasiswa": c.execute("SELECT COUNT(*) FROM mahasiswa").fetchone()[0],
        }

def _next_loan_code(conn):
    codes = conn.execute(
        "SELECT kode FROM peminjaman WHERE kode LIKE 'PJM-%'"
    ).fetchall()
    sequence_numbers = [
        int(match.group(1))
        for row in codes
        if (match := re.fullmatch(r"PJM-(\d+)", row["kode"]))
    ]
    return f"PJM-{max(sequence_numbers, default=0) + 1:04d}"


def create_loan(peminjam, tanggal_pinjam, tanggal_kembali, items, catatan=""):
    with connect() as c:
        c.execute("BEGIN IMMEDIATE")
        kode = _next_loan_code(c)
        if isinstance(peminjam, dict):
            fields = ("nim", "nama", "prodi", "no_hp", "email")
            if any(not str(peminjam.get(field, "")).strip() for field in fields):
                raise ValueError("Data belum terisi semua")
            nim = peminjam["nim"].strip()
            existing = c.execute(
                "SELECT id,nama FROM mahasiswa WHERE nim=?",
                (nim,),
            ).fetchone()
            nama = peminjam["nama"].strip()
            if existing and " ".join(existing["nama"].split()).casefold() != " ".join(nama.split()).casefold():
                raise ValueError(
                    f"NIM {nim} sudah terdaftar atas nama {existing['nama']}. "
                    "Silakan periksa kembali data masukan Anda."
                )
            if existing:
                c.execute(
                    "UPDATE mahasiswa SET prodi=?,no_hp=?,email=? WHERE id=?",
                    (
                        peminjam["prodi"].strip(),
                        peminjam["no_hp"].strip(),
                        peminjam["email"].strip(),
                        existing["id"],
                    ),
                )
            else:
                c.execute(
                    "INSERT INTO mahasiswa(nim,nama,prodi,no_hp,email) VALUES(?,?,?,?,?)",
                    tuple(peminjam[field].strip() for field in fields),
                )
            mahasiswa = c.execute("SELECT id FROM mahasiswa WHERE nim=?", (peminjam["nim"].strip(),)).fetchone()
            mahasiswa_id = mahasiswa["id"]
        else:
            mahasiswa_id = peminjam
        if not items:
            raise ValueError("Data belum terisi semua")
        jumlah_item={}
        for inv_id, qty in items:
            jumlah_item[inv_id]=jumlah_item.get(inv_id,0)+int(qty)
        items=list(jumlah_item.items())
        for inv_id, qty in items:
            row = c.execute("SELECT kode,nama,harga,tersedia FROM inventaris WHERE id=?", (inv_id,)).fetchone()
            if not row or qty < 1 or qty > row["tersedia"]:
                raise ValueError(f"Stok tersedia tidak cukup untuk {row['nama'] if row else 'inventaris'}.")
        cur = c.execute("INSERT INTO peminjaman(kode,mahasiswa_id,tanggal_pinjam,tanggal_rencana_kembali,status,catatan) VALUES(?,?,?,?,?,?)",
                        (kode,mahasiswa_id,tanggal_pinjam,tanggal_kembali,"Dipinjam",catatan))
        loan_id = cur.lastrowid
        for inv_id, qty in items:
            item = c.execute("SELECT kode,nama,harga FROM inventaris WHERE id=?", (inv_id,)).fetchone()
            c.execute("""INSERT INTO detail_peminjaman
              (peminjaman_id,inventaris_id,kode_barang,nama_barang,harga_satuan,jumlah)
              VALUES(?,?,?,?,?,?)""", (loan_id,inv_id,item["kode"],item["nama"],item["harga"],qty))
            c.execute("UPDATE inventaris SET tersedia=tersedia-? WHERE id=?",(qty,inv_id))
        c.commit()
    return kode

def delete_loan(loan_id):
    with connect() as c:
        c.execute("BEGIN")
        row = c.execute("SELECT status FROM peminjaman WHERE id=?", (loan_id,)).fetchone()
        if not row:
            raise ValueError("Transaksi tidak ditemukan.")
        if row["status"] == "Dipinjam":
            details = c.execute("SELECT inventaris_id,jumlah FROM detail_peminjaman WHERE peminjaman_id=?", (loan_id,)).fetchall()
            for detail in details:
                if detail["inventaris_id"] is not None:
                    c.execute("UPDATE inventaris SET tersedia=MIN(jumlah,tersedia+?) WHERE id=?", (detail["jumlah"],detail["inventaris_id"]))
        c.execute("DELETE FROM peminjaman WHERE id=?", (loan_id,))
        c.commit()

def return_loan(loan_id, tanggal_kembali=None, kondisi=None, catatan=""):
    conn = connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        transaction = conn.execute(
            """SELECT kode,tanggal_pinjam,tanggal_rencana_kembali,status
            FROM peminjaman WHERE id=?""",
            (loan_id,),
        ).fetchone()
        if not transaction or transaction["status"] != "Dipinjam":
            raise ValueError(
                "Transaksi penyewaan sudah dikembalikan atau tidak ditemukan."
            )

        if tanggal_kembali is None:
            tanggal_kembali = date.today()
        if not isinstance(tanggal_kembali, (date, str)):
            raise ValueError("Tanggal kembali harus berupa tanggal yang valid.")
        if isinstance(tanggal_kembali, datetime):
            tanggal_kembali = tanggal_kembali.date()
        elif isinstance(tanggal_kembali, str):
            try:
                tanggal_kembali = date.fromisoformat(tanggal_kembali)
            except ValueError as error:
                raise ValueError("Format tanggal kembali tidak valid.") from error
        try:
            tanggal_sewa = date.fromisoformat(transaction["tanggal_pinjam"])
            tanggal_rencana = date.fromisoformat(
                transaction["tanggal_rencana_kembali"]
            )
        except (TypeError, ValueError) as error:
            raise ValueError("Tanggal penyewaan pada transaksi tidak valid.") from error
        if tanggal_kembali < tanggal_sewa:
            raise ValueError(
                "Tanggal kembali tidak boleh lebih awal dari tanggal sewa."
            )

        lama_terlambat, total_denda = hitung_denda(
            tanggal_rencana, tanggal_kembali
        )
        details = conn.execute(
            """SELECT id,inventaris_id,jumlah,kode_barang,nama_barang
            FROM detail_peminjaman WHERE peminjaman_id=? ORDER BY id""",
            (loan_id,),
        ).fetchall()
        if kondisi is not None and not isinstance(kondisi, dict):
            raise ValueError("Kondisi barang harus berupa pasangan detail dan kondisi.")
        kondisi = kondisi or {}
        kondisi_by_detail = {}
        for detail_id, value in kondisi.items():
            try:
                detail_id = int(detail_id)
            except (TypeError, ValueError) as error:
                raise ValueError("Detail barang pada kondisi tidak valid.") from error
            kondisi_by_detail[detail_id] = normalisasi_kondisi_barang(value)
        detail_ids = {detail["id"] for detail in details}
        if not set(kondisi_by_detail).issubset(detail_ids):
            raise ValueError(
                "Kondisi memuat barang yang tidak termasuk dalam transaksi."
            )

        kondisi_terburuk = max(
            (
                kondisi_by_detail.get(detail["id"], "Baik")
                for detail in details
            ),
            key=KONDISI_BARANG.index,
            default="Baik",
        )
        conn.execute(
            """INSERT INTO pengembalian
            (peminjaman_id,tanggal_pengembalian,status_pengembalian,
             kondisi_barang,lama_terlambat,denda_per_hari,total_denda,catatan)
            VALUES(?,?,?,?,?,?,?,?)""",
            (
                loan_id,
                tanggal_kembali.isoformat(),
                "Terlambat" if lama_terlambat else "Tepat Waktu",
                kondisi_terburuk,
                lama_terlambat,
                DENDA_PER_HARI,
                total_denda,
                "" if catatan is None else str(catatan).strip(),
            ),
        )
        for detail in details:
            kondisi_detail = kondisi_by_detail.get(detail["id"], "Baik")
            conn.execute(
                "UPDATE detail_peminjaman SET kondisi_barang=? WHERE id=?",
                (kondisi_detail, detail["id"]),
            )
            if detail["inventaris_id"] is not None:
                conn.execute(
                    """UPDATE inventaris
                    SET tersedia=MIN(jumlah,tersedia+?) WHERE id=?""",
                    (detail["jumlah"], detail["inventaris_id"]),
                )
        conn.execute(
            "UPDATE peminjaman SET status='Dikembalikan' WHERE id=?",
            (loan_id,),
        )
        conn.commit()
        return {
            "kode": transaction["kode"],
            "tanggal_kembali": tanggal_kembali.isoformat(),
            "lama_terlambat": lama_terlambat,
            "total_denda": total_denda,
            "kondisi_barang": kondisi_terburuk,
        }
    except ValueError:
        conn.rollback()
        raise
    except Exception as error:
        conn.rollback()
        raise ValueError(
            f"Pengembalian tidak dapat diproses: {error}"
        ) from error
    finally:
        conn.close()

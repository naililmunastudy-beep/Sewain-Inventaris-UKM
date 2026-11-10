from datetime import date

from core.utils import DENDA_PER_HARI


def migrate_schema(conn):
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "inventaris" in tables and "detail_peminjaman" in tables:
        inventaris_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(inventaris)")
        }
        if "harga" not in inventaris_columns:
            conn.execute(
                "ALTER TABLE inventaris ADD COLUMN harga INTEGER NOT NULL DEFAULT 0"
            )

        category_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(kategori)")
        }
        initialize_category_codes = "kode" not in category_columns
        if initialize_category_codes:
            conn.execute("ALTER TABLE kategori ADD COLUMN kode TEXT")
        elif conn.execute(
            "SELECT 1 FROM kategori WHERE kode IS NULL OR kode LIKE '__MIGRATE__%' LIMIT 1"
        ).fetchone():
            initialize_category_codes = True
        if initialize_category_codes:
            conn.execute("UPDATE kategori SET kode='__MIGRATE__' || id")
            canonical_categories = (
                "Atribut", "Audio", "Dekorasi", "Fotografi", "Kebersihan",
                "Kelistrikan", "Kesehatan", "Komunikasi", "Konsumsi", "Logistik",
                "Musik", "Pencahayaan", "Perkakas", "Sekretariat", "Visual",
            )
            for number, name in enumerate(canonical_categories, start=1):
                conn.execute(
                    "UPDATE kategori SET kode=? WHERE nama=?",
                    (f"KAT-{number:03d}", name),
                )
            custom_categories = conn.execute(
                """SELECT id FROM kategori
                WHERE kode LIKE '__MIGRATE__%'
                ORDER BY nama COLLATE NOCASE,id"""
            ).fetchall()
            for number, row in enumerate(
                custom_categories, start=len(canonical_categories) + 1
            ):
                conn.execute(
                    "UPDATE kategori SET kode=? WHERE id=?",
                    (f"KAT-{number:03d}", row[0]),
                )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_kategori_kode ON kategori(kode)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_inventaris_kode ON inventaris(kode)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_mahasiswa_nim ON mahasiswa(nim)"
        )

        detail_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(detail_peminjaman)")
        }
        if "kode_barang" not in detail_columns:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute(
                "ALTER TABLE detail_peminjaman RENAME TO detail_peminjaman_lama"
            )
            conn.execute("""CREATE TABLE detail_peminjaman (
              id INTEGER PRIMARY KEY AUTOINCREMENT, peminjaman_id INTEGER NOT NULL,
              inventaris_id INTEGER, kode_barang TEXT NOT NULL DEFAULT '',
              nama_barang TEXT NOT NULL DEFAULT '', harga_satuan INTEGER NOT NULL DEFAULT 0,
              jumlah INTEGER NOT NULL,
              FOREIGN KEY(peminjaman_id) REFERENCES peminjaman(id) ON DELETE CASCADE,
              FOREIGN KEY(inventaris_id) REFERENCES inventaris(id) ON DELETE SET NULL
            )""")
            conn.execute("""INSERT INTO detail_peminjaman
              (id,peminjaman_id,inventaris_id,kode_barang,nama_barang,harga_satuan,jumlah)
              SELECT d.id,d.peminjaman_id,d.inventaris_id,i.kode,i.nama,i.harga,d.jumlah
              FROM detail_peminjaman_lama d JOIN inventaris i ON i.id=d.inventaris_id""")
            conn.execute("DROP TABLE detail_peminjaman_lama")
            conn.execute("PRAGMA foreign_keys = ON")

        detail_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(detail_peminjaman)")
        }
        if "kondisi_barang" not in detail_columns:
            conn.execute(
                "ALTER TABLE detail_peminjaman ADD COLUMN kondisi_barang TEXT"
            )

    if "peminjaman" not in tables:
        return

    conn.execute("""CREATE TABLE IF NOT EXISTS pengembalian (
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
    )""")

    backfill_return_history = False
    return_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(pengembalian)")
    }
    if "tanggal_pengembalian" not in return_columns:
        if "tanggal_kembali" in return_columns:
            conn.execute(
                "ALTER TABLE pengembalian RENAME COLUMN tanggal_kembali TO tanggal_pengembalian"
            )
            backfill_return_history = True
        else:
            conn.execute(
                "ALTER TABLE pengembalian ADD COLUMN tanggal_pengembalian TEXT NOT NULL DEFAULT ''"
            )
    return_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(pengembalian)")
    }
    columns_to_add = (
        ("status_pengembalian", "TEXT NOT NULL DEFAULT 'Tepat Waktu'"),
        ("kondisi_barang", "TEXT NOT NULL DEFAULT 'Baik'"),
        ("lama_terlambat", "INTEGER NOT NULL DEFAULT 0"),
        ("denda_per_hari", "INTEGER NOT NULL DEFAULT 0"),
        ("total_denda", "INTEGER NOT NULL DEFAULT 0"),
        ("catatan", "TEXT DEFAULT ''"),
    )
    for column, definition in columns_to_add:
        if column not in return_columns:
            conn.execute(
                f"ALTER TABLE pengembalian ADD COLUMN {column} {definition}"
            )
            if column in ("status_pengembalian", "lama_terlambat"):
                backfill_return_history = True

    duplicate = conn.execute(
        """SELECT peminjaman_id FROM pengembalian
        GROUP BY peminjaman_id HAVING COUNT(*) > 1 LIMIT 1"""
    ).fetchone()
    if duplicate:
        raise ValueError(
            "Data pengembalian memiliki catatan ganda untuk satu transaksi; "
            "indeks unik tidak dapat dibuat tanpa menghapus data."
        )
    conn.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS
        idx_pengembalian_peminjaman_id ON pengembalian(peminjaman_id)"""
    )

    if backfill_return_history and "tanggal_rencana_kembali" in {
        row[1] for row in conn.execute("PRAGMA table_info(peminjaman)")
    }:
        legacy_returns = conn.execute(
            """SELECT r.id,r.tanggal_pengembalian,p.tanggal_rencana_kembali
            FROM pengembalian r
            JOIN peminjaman p ON p.id=r.peminjaman_id
            WHERE r.tanggal_pengembalian != ''"""
        ).fetchall()
        for row in legacy_returns:
            try:
                returned = date.fromisoformat(row["tanggal_pengembalian"])
                planned = date.fromisoformat(row["tanggal_rencana_kembali"])
            except (TypeError, ValueError):
                continue
            late_days = max(0, (returned - planned).days)
            conn.execute(
                """UPDATE pengembalian
                SET status_pengembalian=?,lama_terlambat=?
                WHERE id=?""",
                (
                    "Terlambat" if late_days else "Tepat Waktu",
                    late_days,
                    row["id"],
                ),
            )

import streamlit as st
from core import db

def header(kicker, title, subtitle):
    st.markdown(f'<div class="page-kicker">{kicker}</div><h1>{title}</h1><div class="page-intro">{subtitle}</div>', unsafe_allow_html=True)

def display_table(frame):
  frame = frame.copy()
  column_config = {}
  for column in frame.columns:
    normalized = str(column).casefold()
    alignment = (
      "center"
      if any(label in normalized for label in (
        "kode", "nim", "jumlah", "tersedia", "disewa", "kondisi",
        "tanggal", "kembali", "status", "terlambat", "hari",
      ))
      else "left"
    )
    display_name = str(column).upper()
    if frame[column].dtype.kind in "iu":
      column_config[column] = st.column_config.NumberColumn(
        display_name,
        format="%d",
        alignment=alignment,
      )
    elif alignment == "center":
      column_config[column] = st.column_config.TextColumn(
        display_name,
        alignment=alignment,
      )
    else:
      column_config[column] = st.column_config.TextColumn(
        display_name,
        alignment=alignment,
      )
  st.markdown(
    """
    <style>
    [data-testid="stDataObjectViz"] th,
    div[data-testid="stTable"] th,
    [data-testid="stDataFrame"] [role="columnheader"],
    [data-testid="stDataFrame"] [role="columnheader"] * {
      text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
  )
  st.dataframe(frame, column_config=column_config, width="stretch", hide_index=True)

def format_rupiah_column(values):
  formatted = [f"{int(value):,}".replace(",", ".") for value in values]
  width = max((len(value) for value in formatted), default=0)
  return [
    "Rp" + "\u00a0" + "\u00a0" * (width - len(value)) + value
    for value in formatted
  ]

def loan_rows(where="", params=()):
    return db.query("""
      SELECT p.id,p.kode,m.nim,m.nama,p.tanggal_pinjam,p.tanggal_rencana_kembali,
      CASE p.status WHEN 'Dipinjam' THEN 'Disewa' ELSE p.status END AS status,p.catatan,
      r.tanggal_pengembalian,r.lama_terlambat,r.total_denda,
      r.status_pengembalian,r.kondisi_barang AS kondisi_pengembalian,
      r.catatan AS catatan_pengembalian,
      GROUP_CONCAT(COALESCE(NULLIF(d.nama_barang,''),i.nama) || ' x ' || d.jumlah, ', ') AS barang
      FROM peminjaman p JOIN mahasiswa m ON m.id=p.mahasiswa_id
      LEFT JOIN pengembalian r ON r.peminjaman_id=p.id
      LEFT JOIN detail_peminjaman d ON d.peminjaman_id=p.id
      LEFT JOIN inventaris i ON i.id=d.inventaris_id
    """ + ((" WHERE "+where) if where else "") + " GROUP BY p.id ORDER BY p.id DESC", params)

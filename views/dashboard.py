import streamlit as st
import pandas as pd
from core import db
from views.common import header, loan_rows


def _render_recent_rentals_table(frame):
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
    st.dataframe(
        frame,
        column_config={
            "Kode transaksi": st.column_config.TextColumn("KODE TRANSAKSI", alignment="center"),
            "Penyewa": st.column_config.TextColumn("NAMA PENYEWA", alignment="left"),
            "Barang": st.column_config.TextColumn("BARANG", alignment="left"),
            "Tanggal sewa": st.column_config.TextColumn("TANGGAL SEWA", alignment="center"),
            "Rencana kembali": st.column_config.TextColumn("RENCANA KEMBALI", alignment="center"),
            "Status": st.column_config.TextColumn("STATUS", alignment="center"),
        },
        width="stretch",
        hide_index=True,
    )

def render():
    header("RINGKASAN","Dashboard","Ringkasan inventaris dan aktivitas penyewaan UKM.")
    s = db.dashboard_stats()
    cols = st.columns(4)
    cols[0].metric("Jenis inventaris",s["inventaris"],"Terdaftar")
    cols[1].metric("Total unit",s["unit"],"Seluruh aset")
    cols[2].metric("Sedang disewa",s["dipinjam"],"Transaksi aktif")
    cols[3].metric("Terlambat",s["terlambat"],"Perlu ditindaklanjuti")
    st.markdown("### Aktivitas penyewaan terbaru")
    rows = loan_rows()
    if rows:
        df = pd.DataFrame(rows[:8])[["kode","nama","barang","tanggal_pinjam","tanggal_rencana_kembali","status"]]
        df.columns = ["Kode transaksi","Penyewa","Barang","Tanggal sewa","Rencana kembali","Status"]
        _render_recent_rentals_table(df)
    else:
        st.info("Belum ada transaksi penyewaan.")
    st.markdown('<div class="notice"><span class="material-symbols-rounded">info</span> <b>Tips Sewain:</b> Periksa daftar terlambat secara berkala dan pastikan stok tersedia diperbarui setelah barang kembali.</div>',unsafe_allow_html=True)

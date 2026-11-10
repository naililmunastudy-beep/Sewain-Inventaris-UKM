import streamlit as st
import pandas as pd
from core import db
from views.common import format_rupiah_column, header, loan_rows


def _format_rupiah_opsional(nilai):
    return (
        "-"
        if nilai is None or pd.isna(nilai)
        else format_rupiah_column([nilai])[0]
    )


def _render_history_table(frame):
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
            "Kode": st.column_config.TextColumn("KODE", alignment="center"),
            "NIM": st.column_config.TextColumn("NIM", alignment="center"),
            "Nama penyewa": st.column_config.TextColumn("NAMA PENYEWA", alignment="left"),
            "Barang": st.column_config.TextColumn("BARANG", alignment="left"),
            "Tanggal sewa": st.column_config.TextColumn("TANGGAL SEWA", alignment="center"),
            "Rencana kembali": st.column_config.TextColumn("RENCANA KEMBALI", alignment="center"),
            "Tanggal kembali": st.column_config.TextColumn("TANGGAL KEMBALI", alignment="center"),
            "Denda": st.column_config.TextColumn("DENDA", alignment="left"),
            "Status": st.column_config.TextColumn("STATUS", alignment="center"),
            "Catatan": st.column_config.TextColumn("CATATAN", alignment="left"),
        },
        width="stretch",
        hide_index=True,
    )

def render():
    header("RIWAYAT PENYEWAAN","Riwayat Penyewaan","Telusuri transaksi penyewaan dan status pengembalian.")
    status=st.selectbox("Filter status",["Semua","Disewa","Dikembalikan"])
    status_internal = {"Disewa": "Dipinjam", "Dikembalikan": "Dikembalikan"}
    where="" if status=="Semua" else "p.status=?"
    rows=loan_rows(where,(status_internal[status],) if where else ())
    if rows:
        df=pd.DataFrame(rows)
        df=df[[
            "kode","nim","nama","barang","tanggal_pinjam",
            "tanggal_rencana_kembali","tanggal_pengembalian",
            "total_denda","status","catatan",
        ]]
        df["tanggal_pengembalian"] = df["tanggal_pengembalian"].fillna("-")
        df["total_denda"] = df["total_denda"].map(_format_rupiah_opsional)
        df.columns=[
            "Kode","NIM","Nama penyewa","Barang","Tanggal sewa",
            "Rencana kembali","Tanggal kembali","Denda","Status","Catatan",
        ]
        _render_history_table(df)
        pilihan=st.selectbox("Pilih transaksi",rows,format_func=lambda row:f'{row["kode"]} - {row["nama"]} ({row["status"]})')
        detail=db.query("SELECT kode_barang,nama_barang,harga_satuan,jumlah FROM detail_peminjaman WHERE peminjaman_id=? ORDER BY id",(pilihan["id"],))
        formatted_prices = format_rupiah_column(
            item["harga_satuan"] for item in detail
        )
        lines=[
            "SEWAIN | NOTA PENYEWAAN",
            f'Kode transaksi: {pilihan["kode"]}',
            f'Penyewa: {pilihan["nama"]} ({pilihan["nim"]})',
            f'Tanggal sewa: {pilihan["tanggal_pinjam"]}',
            f'Rencana kembali: {pilihan["tanggal_rencana_kembali"]}',
        ]
        if pilihan["tanggal_pengembalian"]:
            lines.extend(
                [
                    f'Tanggal kembali: {pilihan["tanggal_pengembalian"]}',
                    f'Lama terlambat: {pilihan["lama_terlambat"]} hari',
                    f'Denda: {_format_rupiah_opsional(pilihan["total_denda"])}',
                ]
            )
        lines.extend(["", "Barang:"])
        lines.extend(
            f'{item["kode_barang"]} | {item["nama_barang"]} | '
            f'{item["jumlah"]} unit | {price}'
            for item, price in zip(detail, formatted_prices)
        )
        st.download_button("Unduh nota penyewaan", "\n".join(lines), file_name=f'nota_{pilihan["kode"]}.txt', mime="text/plain")
        with st.expander("Batalkan transaksi yang salah"):
            yakin=st.checkbox("Saya yakin ingin menghapus transaksi ini",key=f'confirm_delete_{pilihan["id"]}')
            if st.button("Hapus transaksi",disabled=not yakin,key=f'delete_loan_{pilihan["id"]}'):
                try:
                    db.delete_loan(pilihan["id"])
                    if st.session_state.get("last_loan_code")==pilihan["kode"]:
                        del st.session_state["last_loan_code"]
                    st.success("Transaksi dihapus dan stok dipulihkan jika barang masih disewa.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Transaksi tidak dapat dihapus: {error}")
    else: st.info("Tidak ada data untuk filter ini.")

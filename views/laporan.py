from html import escape

import streamlit as st
import pandas as pd
from datetime import date
from core import db
from views.common import display_table, format_rupiah_column, header, loan_rows


def _render_inventory_report(rows):
    headers = (
        "KODE", "NAMA BARANG", "KATEGORI", "JUMLAH", "TERSEDIA",
        "DISEWA", "HARGA", "KONDISI", "LOKASI",
    )
    body = []
    for row in rows:
        amount = f"{int(row['harga']):,}".replace(",", ".")
        cells = (
            (row["kode"], "center", False),
            (row["nama"], "left", False),
            (row["kategori"], "left", False),
            (row["jumlah"], "center", False),
            (row["tersedia"], "center", False),
            (row["disewa"], "center", False),
            (
                '<div style="display:flex;justify-content:space-between;width:100%;">'
                f'<span>Rp</span><span>{amount}</span></div>',
                "left",
                True,
            ),
            (row["kondisi"], "center", False),
            (row["lokasi"], "left", False),
        )
        cells_html = []
        for value, alignment, is_html in cells:
            content = value if is_html else escape(str(value))
            cells_html.append(
                f'<td style="text-align:{alignment};padding:8px 10px;'
                f'border-bottom:1px solid #d7e3f1">{content}</td>'
            )
        body.append("<tr>" + "".join(cells_html) + "</tr>")

    header_html = "".join(
        f'<th style="text-align:center;padding:8px 10px;'
        f'border-bottom:1px solid var(--border-color);'
        f'background:var(--secondary-background-color);color:var(--text-color)">'
        f'{escape(label)}</th>'
        for label in headers
    )
    st.markdown(
        '<style>div[data-testid="stMarkdown"] table th {text-align:center !important;'
        'font-weight:inherit !important;text-transform:none !important;}</style>'
        '<table style="width:100%;border-collapse:collapse;'
        'background:var(--background-color);color:var(--text-color)">'
        f"<thead><tr>{header_html}</tr></thead><tbody>{''.join(body)}</tbody></table>",
        unsafe_allow_html=True,
    )

def render():
    header("LAPORAN & EKSPOR","Laporan","Ringkasan data yang dapat diunduh untuk dokumentasi administrasi.")
    stats=db.dashboard_stats()
    a,b,c,d=st.columns(4)
    a.metric("Total unit inventaris",stats["unit"])
    b.metric("Mahasiswa terdaftar",stats["mahasiswa"])
    c.metric("Penyewaan aktif",stats["dipinjam"])
    total_denda = db.query(
        "SELECT COALESCE(SUM(total_denda),0) AS total FROM pengembalian"
    )[0]["total"]
    d.metric("Total denda",f"Rp{int(total_denda):,}".replace(",","."))
    st.markdown("### Laporan inventaris")
    inv=db.query("SELECT i.kode,i.nama,COALESCE(k.nama,'Tanpa kategori') kategori,i.jumlah,i.tersedia,(i.jumlah-i.tersedia) disewa,i.harga,i.kondisi,i.lokasi FROM inventaris i LEFT JOIN kategori k ON k.id=i.kategori_id ORDER BY CAST(SUBSTR(i.kode,INSTR(i.kode,'-')+1) AS INTEGER),i.kode")
    if inv:
        df=pd.DataFrame(inv)
        df.columns = [
            "Kode", "Nama Barang", "Kategori", "Jumlah", "Tersedia",
            "Disewa", "Harga", "Kondisi", "Lokasi",
        ]
        _render_inventory_report(inv)
        st.download_button("Unduh inventaris (CSV)",df.to_csv(index=False).encode("utf-8-sig"),"laporan_inventaris.csv","text/csv")
    st.markdown("### Laporan penyewaan")
    loans=loan_rows()
    if loans:
        df2=pd.DataFrame(loans)
        df2=df2[[
            "kode","nim","nama","barang","tanggal_pinjam",
            "tanggal_rencana_kembali","tanggal_pengembalian",
            "lama_terlambat","total_denda","status","catatan",
        ]]
        df2["tanggal_pengembalian"] = df2["tanggal_pengembalian"].fillna("-")
        df2["lama_terlambat"] = df2["lama_terlambat"].map(
            lambda value: "-" if pd.isna(value) else int(value)
        )
        df2["total_denda"] = df2["total_denda"].map(
            lambda value: "-"
            if pd.isna(value)
            else format_rupiah_column([value])[0]
        )
        df2.columns=[
            "Kode", "NIM", "Nama penyewa", "Barang", "Tanggal Sewa",
            "Rencana Kembali", "Tanggal Kembali", "Terlambat (Hari)",
            "Denda", "Status", "Catatan",
        ]
        display_table(df2)
        st.download_button("Unduh penyewaan (CSV)",df2.to_csv(index=False).encode("utf-8-sig"),"laporan_penyewaan.csv","text/csv")
    st.caption(f"Laporan dibuat pada {date.today().strftime('%d-%m-%Y')}.")

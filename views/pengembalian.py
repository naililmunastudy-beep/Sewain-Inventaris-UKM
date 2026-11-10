from io import BytesIO
from datetime import date

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

from core import db
from views.penyewaan_baru import _receipt_font, _wrap_text
from views.common import format_rupiah_column, header, loan_rows

PILIHAN_KONDISI = ("Baik", "Rusak Ringan", "Rusak Berat")


def _rupiah(nilai):
    return f"Rp{int(nilai):,}".replace(",", ".")


def _format_rupiah_opsional(nilai):
    return (
        "-"
        if nilai is None or pd.isna(nilai)
        else format_rupiah_column([nilai])[0]
    )


def _render_receipt(kode):
    rows = db.query(
        """SELECT p.kode,p.tanggal_pinjam,p.tanggal_rencana_kembali,
        m.nama,m.nim,r.tanggal_pengembalian,r.status_pengembalian,r.lama_terlambat,
        r.denda_per_hari,r.total_denda,r.kondisi_barang,r.catatan
        FROM peminjaman p
        JOIN mahasiswa m ON m.id=p.mahasiswa_id
        JOIN pengembalian r ON r.peminjaman_id=p.id
        WHERE p.kode=?""",
        (kode,),
    )
    if not rows:
        return
    row = rows[0]
    details = db.query(
        """SELECT kode_barang,nama_barang,jumlah,kondisi_barang
        FROM detail_peminjaman
        WHERE peminjaman_id=(SELECT id FROM peminjaman WHERE kode=?)
        ORDER BY id""",
        (kode,),
    )
    st.success(
        f"Pengembalian {kode} tercatat. Total denda: "
        f"{_rupiah(row['total_denda'])}."
    )
    receipt_png = _return_receipt_png(row, details)
    st.image(
        receipt_png,
        caption="Pratinjau bukti pengembalian (PNG)",
        width="stretch",
    )
    st.download_button(
        "Unduh bukti pengembalian",
        receipt_png,
        file_name=f"bukti_pengembalian_{kode}.png",
        mime="image/png",
        type="primary",
        key=f"download_return_{kode}",
    )
    if st.button(
        "Selesai / Transaksi Baru",
        key=f"finish_return_{kode}",
    ):
        st.session_state.pop("last_return_code", None)
        st.rerun()


def _return_receipt_png(row, details):
    width = 1000
    outer_margin = 48
    paper_left, paper_right = 56, width - 56
    content_left, content_right = 105, width - 105
    content_width = content_right - content_left
    estimated_height = 1100 + len(details) * 160
    if row["catatan"]:
        estimated_height += max(0, len(row["catatan"]) - 60) // 48 * 30 + 48

    image = Image.new("RGB", (width, estimated_height), "#e8edf3")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (
            paper_left + 10,
            outer_margin + 12,
            paper_right + 10,
            estimated_height - outer_margin + 12,
        ),
        radius=18,
        fill="#cbd5e1",
    )
    draw.rounded_rectangle(
        (paper_left, outer_margin, paper_right, estimated_height - outer_margin),
        radius=18,
        fill="#ffffff",
        outline="#d5dce5",
        width=2,
    )

    title_font = _receipt_font(36, bold=True)
    subtitle_font = _receipt_font(23)
    heading_font = _receipt_font(24, bold=True)
    body_font = _receipt_font(21)
    small_font = _receipt_font(18)
    bold_font = _receipt_font(21, bold=True)
    line_color = "#cbd5e1"
    y = 90

    title = "SEWAIN | BUKTI PENGEMBALIAN"
    draw.text(
        ((width - draw.textlength(title, font=title_font)) / 2, y),
        title,
        font=title_font,
        fill="#102a56",
    )
    y += 56
    subtitle = "BUKTI TRANSAKSI PENGEMBALIAN INVENTARIS"
    draw.text(
        ((width - draw.textlength(subtitle, font=subtitle_font)) / 2, y),
        subtitle,
        font=subtitle_font,
        fill="#526b8a",
    )
    y += 52
    draw.line((content_left, y, content_right, y), fill=line_color, width=2)
    y += 25

    metadata = (
        ("Kode Transaksi", row["kode"]),
        ("Nama Penyewa", row["nama"]),
        ("NIM", row["nim"]),
        ("Tanggal Sewa", row["tanggal_pinjam"]),
        ("Rencana Kembali", row["tanggal_rencana_kembali"]),
        ("Tanggal Kembali", row["tanggal_pengembalian"]),
        ("Status Pengembalian", row["status_pengembalian"]),
        ("Lama Terlambat", f'{row["lama_terlambat"]} hari'),
    )
    label_width = 210
    for label, value in metadata:
        draw.text((content_left, y), label, font=body_font, fill="#526b8a")
        draw.text(
            (content_left + label_width, y),
            ":",
            font=body_font,
            fill="#526b8a",
        )
        value_lines = _wrap_text(
            draw, value or "-", body_font, content_width - label_width - 18
        )
        for line_number, line in enumerate(value_lines):
            draw.text(
                (content_left + label_width + 18, y + line_number * 30),
                line,
                font=body_font,
                fill="#172b4d",
            )
        y += max(34, len(value_lines) * 30 + 4)

    y += 8
    draw.line((content_left, y, content_right, y), fill=line_color, width=2)
    y += 24
    draw.text((content_left, y), "RINGKASAN DENDA", font=heading_font, fill="#102a56")
    y += 42
    fine_rows = (
        ("Tarif denda per hari", _rupiah(row["denda_per_hari"])),
        ("Total denda", _rupiah(row["total_denda"])),
    )
    for label, value in fine_rows:
        font = bold_font if label == "Total denda" else body_font
        color = "#102a56" if label == "Total denda" else "#172b4d"
        draw.text((content_left, y), label, font=font, fill=color)
        draw.text(
            (content_right - draw.textlength(value, font=font), y),
            value,
            font=font,
            fill=color,
        )
        y += 36

    y += 8
    draw.line((content_left, y, content_right, y), fill=line_color, width=2)
    y += 24
    draw.text((content_left, y), "KONDISI BARANG", font=heading_font, fill="#102a56")
    y += 42
    column_x = (content_left, content_left + 150, content_left + 515, content_left + 670)
    column_width = (138, 350, 148, 120)
    header_height = 42
    draw.rounded_rectangle(
        (content_left, y, content_right, y + header_height),
        radius=6,
        fill="#eaf2ff",
    )
    for x, label in zip(column_x, ("Kode Barang", "Nama Barang", "Jumlah", "Kondisi")):
        draw.text((x + 5, y + 9), label, font=small_font, fill="#102a56")
    y += header_height + 8

    for item in details:
        columns = (
            (item["kode_barang"], column_width[0]),
            (item["nama_barang"], column_width[1]),
            (f'{item["jumlah"]} unit', column_width[2]),
            (item["kondisi_barang"] or "Baik", column_width[3]),
        )
        wrapped = [
            _wrap_text(draw, text, small_font, max_width - 8)
            for text, max_width in columns
        ]
        line_count = max(map(len, wrapped))
        for x, lines in zip(column_x, wrapped):
            for line_number, line in enumerate(lines):
                draw.text(
                    (x + 5, y + 7 + line_number * 25),
                    line,
                    font=small_font,
                    fill="#172b4d",
                )
        y += max(44, line_count * 25 + 14)
        draw.line((content_left, y, content_right, y), fill="#e2e8f0", width=1)
        y += 8

    if row["catatan"]:
        y += 12
        draw.text((content_left, y), "Catatan", font=bold_font, fill="#102a56")
        y += 32
        for line in _wrap_text(draw, row["catatan"], body_font, content_width):
            draw.text((content_left, y), line, font=body_font, fill="#172b4d")
            y += 30

    y += 18
    footer = "Bukti transaksi resmi Sewain. Simpan nota ini sebagai bukti pengembalian."
    for line in _wrap_text(draw, footer, small_font, content_width):
        draw.text(
            ((width - draw.textlength(line, font=small_font)) / 2, y),
            line,
            font=small_font,
            fill="#526b8a",
        )
        y += 26

    receipt_buffer = BytesIO()
    image.crop((0, 0, width, min(estimated_height, y + outer_margin))).save(
        receipt_buffer,
        format="PNG",
    )
    return receipt_buffer.getvalue()


def _render_return_history(rows):
    if not rows:
        st.info("Belum ada riwayat pengembalian.")
        return

    frame = pd.DataFrame(rows)
    history = pd.DataFrame(
        {
            "KODE": frame["kode"],
            "PENYEWA": frame["nama"],
            "BARANG": frame["barang"].fillna("-"),
            "TANGGAL SEWA": frame["tanggal_pinjam"],
            "RENCANA KEMBALI": frame["tanggal_rencana_kembali"],
            "TANGGAL KEMBALI": frame["tanggal_pengembalian"].fillna("-"),
            "TERLAMBAT (HARI)": frame["lama_terlambat"].map(
                lambda value: "-" if pd.isna(value) else int(value)
            ),
            "DENDA": frame["total_denda"].map(_format_rupiah_opsional),
            "STATUS": frame["status"],
            "CATATAN": frame["catatan_pengembalian"].fillna("-").replace("", "-"),
        }
    )
    column_config = {
        "KODE": st.column_config.TextColumn("KODE", alignment="center"),
        "PENYEWA": st.column_config.TextColumn("PENYEWA", alignment="left"),
        "BARANG": st.column_config.TextColumn("BARANG", alignment="left"),
        "TANGGAL SEWA": st.column_config.TextColumn(
            "TANGGAL SEWA", alignment="center"
        ),
        "RENCANA KEMBALI": st.column_config.TextColumn(
            "RENCANA KEMBALI", alignment="center"
        ),
        "TANGGAL KEMBALI": st.column_config.TextColumn(
            "TANGGAL KEMBALI", alignment="center"
        ),
        "TERLAMBAT (HARI)": st.column_config.TextColumn(
            "TERLAMBAT (HARI)", alignment="center"
        ),
        "DENDA": st.column_config.TextColumn("DENDA", alignment="left"),
        "STATUS": st.column_config.TextColumn("STATUS", alignment="center"),
        "CATATAN": st.column_config.TextColumn("CATATAN", alignment="left"),
    }
    st.markdown(
        """
        <style>
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] [role="columnheader"] * {
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(
        history,
        column_config=column_config,
        width="stretch",
        hide_index=True,
        alt="Riwayat pengembalian dan denda penyewaan",
    )


def render():
    header(
        "PENGEMBALIAN",
        "Pengembalian",
        "Proses pengembalian barang sewaan dan perbarui stok secara otomatis.",
    )
    active_rows = loan_rows("p.status='Dipinjam'")
    if not active_rows:
        st.success("Tidak ada penyewaan aktif saat ini.")
    else:
        for row in active_rows:
            today = date.today()
            today_late_days, today_fine = db.hitung_denda(
                row["tanggal_rencana_kembali"], today
            )
            details = db.query(
                """SELECT id,kode_barang,nama_barang,jumlah
                FROM detail_peminjaman WHERE peminjaman_id=? ORDER BY id""",
                (row["id"],),
            )
            with st.container(border=True):
                a, b, c = st.columns([2, 3, 1.4])
                a.markdown(f'**{row["kode"]}**\n\n{row["nama"]}')
                b.write(f'Barang: {row["barang"] or "-"}')
                b.caption(f'Tanggal sewa: {row["tanggal_pinjam"]}')
                b.caption(
                    f'Rencana kembali: {row["tanggal_rencana_kembali"]}'
                )
                if today_late_days:
                    c.warning(
                        f"Terlambat {today_late_days} hari. "
                        f"Estimasi denda hari ini: {_rupiah(today_fine)}."
                    )

                with st.expander(f"Proses pengembalian {row['kode']}"):
                    try:
                        tanggal_sewa = date.fromisoformat(row["tanggal_pinjam"])
                    except (TypeError, ValueError):
                        st.error("Tanggal sewa pada transaksi tidak valid.")
                        continue
                    tanggal_kembali = st.date_input(
                        "Tanggal kembali aktual",
                        value=max(today, tanggal_sewa),
                        min_value=tanggal_sewa,
                        key=f"return_date_{row['id']}",
                    )
                    if tanggal_kembali > today:
                        st.caption(
                            "Tanggal kembali yang dipilih melewati hari ini."
                        )
                    kondisi = {}
                    for item in details:
                        kondisi[item["id"]] = st.selectbox(
                            f"Kondisi {item['kode_barang']} — {item['nama_barang']}",
                            PILIHAN_KONDISI,
                            index=0,
                            key=f"return_condition_{item['id']}",
                        )
                    catatan = st.text_input(
                        "Catatan pengembalian (opsional)",
                        key=f"return_note_{row['id']}",
                    )
                    late_days, fine = db.hitung_denda(
                        row["tanggal_rencana_kembali"], tanggal_kembali
                    )
                    if fine:
                        st.warning(
                            f"Terlambat {late_days} hari. "
                            f"Total denda: {_rupiah(fine)}."
                        )
                    else:
                        st.info("Tidak ada keterlambatan atau denda.")
                    if st.button(
                        "Konfirmasi pengembalian",
                        key=f"confirm_return_{row['id']}",
                        type="primary",
                    ):
                        try:
                            result = db.return_loan(
                                row["id"],
                                tanggal_kembali,
                                kondisi,
                                catatan,
                            )
                            st.session_state["last_return_code"] = result["kode"]
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))

    last_return_code = st.session_state.get("last_return_code")
    if last_return_code:
        _render_receipt(last_return_code)

    st.markdown("### Riwayat pengembalian")
    returned_rows = loan_rows("p.status='Dikembalikan'")
    _render_return_history(returned_rows)

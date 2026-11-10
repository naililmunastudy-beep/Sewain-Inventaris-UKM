"""Formulir dan bukti transaksi penyewaan inventaris."""
import streamlit as st
from io import BytesIO
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageFont
from core import db
from core.utils import PROGRAM_STUDI_PER_JURUSAN
from views.common import format_rupiah_column, header

def _reset_loan_program_studi():
    st.session_state.pop("loan_program_studi", None)

def _lookup_loan_student():
    nim = str(st.session_state.get("loan_nim", "")).strip()
    existing = (
        db.get_student_by_nim(nim)
        if nim.isascii() and nim.isdigit()
        else None
    )
    previous = st.session_state.get("loan_matched_student")
    if existing:
        st.session_state["loan_matched_student"] = existing
        st.session_state["loan_nama"] = existing["nama"]
        st.session_state["loan_hp"] = existing["no_hp"]
        st.session_state["loan_email"] = existing["email"]
        jurusan = next(
            (
                department
                for department, programs in PROGRAM_STUDI_PER_JURUSAN.items()
                if existing["prodi"] in programs
            ),
            "Data jurusan lama",
        )
        st.session_state["loan_jurusan"] = jurusan
        st.session_state["loan_program_studi"] = existing["prodi"]
    elif previous:
        for key in (
            "loan_matched_student",
            "loan_nama",
            "loan_hp",
            "loan_email",
            "loan_jurusan",
            "loan_program_studi",
        ):
            st.session_state.pop(key, None)

def _selected_item_id(item):
    if isinstance(item, dict):
        return item.get("id")
    return item

def _reset_selected_item(item_key, quantity_key):
    st.session_state.pop(item_key, None)
    st.session_state.pop(quantity_key, None)

def _reset_quantity(quantity_key):
    st.session_state.pop(quantity_key, None)

def _change_quantity(quantity_key, change, stock_limit):
    quantity = int(st.session_state.get(quantity_key, 1))
    st.session_state[quantity_key] = max(1, min(quantity + change, stock_limit))

def _clear_previous_loan():
    for key in list(st.session_state):
        if key.startswith("loan_") or key == "last_loan_code":
            del st.session_state[key]
    st.session_state["_reset_loan_form"] = False

def _rupiah(value):
    return f"Rp {int(value):,}".replace(",", ".")

def _draw_accounting_amount(draw, amount, left, right, y, font, fill):
    draw.text((left, y), "Rp", font=font, fill=fill)
    numeric_amount = f"{int(amount):,}".replace(",", ".")
    amount_width = draw.textlength(numeric_amount, font=font)
    draw.text((right - amount_width, y), numeric_amount, font=font, fill=fill)

def _receipt_font(size, bold=False):
    font_files = (
        (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf")
        if bold
        else (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf")
    )
    for font_file in font_files:
        try:
            return ImageFont.truetype(font_file, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)

def _wrap_text(draw, text, font, max_width):
    words = str(text or "-").split()
    if not words:
        return ["-"]
    lines = []
    current = words[0]
    if draw.textlength(current, font=font) > max_width:
        pieces = []
        piece = ""
        for character in current:
            if piece and draw.textlength(piece + character, font=font) > max_width:
                pieces.append(piece)
                piece = character
            else:
                piece += character
        if piece:
            pieces.append(piece)
        lines.extend(pieces[:-1])
        current = pieces[-1]
    for word in words[1:]:
        if draw.textlength(word, font=font) > max_width:
            if current:
                lines.append(current)
                current = ""
            piece = ""
            for character in word:
                if piece and draw.textlength(piece + character, font=font) > max_width:
                    lines.append(piece)
                    piece = character
                else:
                    piece += character
            current = piece
            continue
        candidate = f"{current} {word}"
        if not current or draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

def _receipt_png(row, items, jurusan):
    width = 1000
    outer_margin = 48
    paper_left = 56
    paper_right = width - 56
    content_left = 105
    content_right = width - 105
    content_width = content_right - content_left
    total_value = sum(int(item["harga_satuan"]) * int(item["jumlah"]) for item in items)
    metadata = [
        ("Kode Transaksi", row["kode"]),
        ("Tanggal Sewa", row["tanggal_pinjam"]),
        ("Rencana Kembali", row["tanggal_rencana_kembali"]),
        ("Nama", row["nama"]),
        ("NIM", row["nim"]),
        ("Jurusan", jurusan),
        ("Program Studi", row["prodi"]),
        ("Nomor HP", row["no_hp"]),
        ("Email", row["email"]),
    ]
    estimated_height = (
        1000
        + len(items) * 105
        + sum(max(0, len(str(value)) - 48) // 42 * 30 for _, value in metadata)
        + sum(max(0, len(str(item["nama_barang"])) - 35) // 38 * 30 for item in items)
        + max(0, len(str(row.get("catatan") or "")) - 60) // 48 * 30
    )
    image = Image.new("RGB", (width, estimated_height), "#e8edf3")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (paper_left + 10, outer_margin + 12, paper_right + 10, estimated_height - outer_margin + 12),
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

    title = "SEWAIN | NOTA PENYEWAAN"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) / 2, y), title, font=title_font, fill="#102a56")
    y += 56
    subtitle = "BUKTI TRANSAKSI PENYEWAAN INVENTARIS"
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    draw.text(((width - subtitle_width) / 2, y), subtitle, font=subtitle_font, fill="#526b8a")
    y += 52
    draw.line((content_left, y, content_right, y), fill=line_color, width=2)
    y += 25

    label_width = 175
    for label, value in metadata:
        draw.text((content_left, y), f"{label}", font=body_font, fill="#526b8a")
        draw.text((content_left + label_width, y), ":", font=body_font, fill="#526b8a")
        value_lines = _wrap_text(
            draw,
            value,
            body_font,
            content_width - label_width - 18,
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
    draw.text((content_left, y), "DETAIL BARANG", font=heading_font, fill="#102a56")
    y += 44

    col_x = [content_left, content_left + 150, content_left + 495, content_left + 625]
    col_width = [138, 325, 118, 155]
    value_column_left = col_x[3]
    value_column_right = col_x[3] + col_width[3]
    table_header_height = 42
    draw.rounded_rectangle(
        (content_left, y, content_right, y + table_header_height),
        radius=6,
        fill="#eaf2ff",
    )
    for x, label in zip(col_x, ("Kode Barang", "Nama Barang", "Jumlah", "Nilai Barang")):
        draw.text((x + 5, y + 9), label, font=small_font, fill="#102a56")
    y += table_header_height + 8

    for item in items:
        code_lines = _wrap_text(draw, item["kode_barang"], small_font, col_width[0] - 8)
        name_lines = _wrap_text(draw, item["nama_barang"], small_font, col_width[1] - 8)
        qty_lines = _wrap_text(draw, f'{item["jumlah"]} unit', small_font, col_width[2] - 8)
        value = int(item["harga_satuan"]) * int(item["jumlah"])
        row_lines = max(len(code_lines), len(name_lines), len(qty_lines))
        row_height = max(44, row_lines * 25 + 14)
        for x, lines in zip(col_x[:3], (code_lines, name_lines, qty_lines)):
            for line_number, line in enumerate(lines):
                draw.text(
                    (x + 5, y + 7 + line_number * 25),
                    line,
                    font=small_font,
                    fill="#172b4d",
                )
        _draw_accounting_amount(
            draw,
            value,
            value_column_left,
            value_column_right,
            y + 7,
            small_font,
            "#172b4d",
        )
        y += row_height
        draw.line((content_left, y, content_right, y), fill="#e2e8f0", width=1)
        y += 8

    y += 8
    total_label = "TOTAL NILAI BARANG"
    draw.text((content_left, y), total_label, font=bold_font, fill="#102a56")
    _draw_accounting_amount(
        draw,
        total_value,
        value_column_left,
        value_column_right,
        y,
        bold_font,
        "#102a56",
    )
    y += 42
    draw.line((content_left, y, content_right, y), fill=line_color, width=2)
    y += 22

    draw.text((content_left, y), "Catatan", font=bold_font, fill="#102a56")
    y += 32
    note_lines = _wrap_text(draw, row.get("catatan", ""), body_font, content_width)
    for line in note_lines:
        draw.text((content_left, y), line, font=body_font, fill="#172b4d")
        y += 30
    y += 18
    footer = "Bukti transaksi resmi Sewain. Simpan nota ini sebagai bukti penyewaan."
    for line in _wrap_text(draw, footer, small_font, content_width):
        line_width = draw.textlength(line, font=small_font)
        draw.text(((width - line_width) / 2, y), line, font=small_font, fill="#526b8a")
        y += 26

    final_height = min(estimated_height, y + outer_margin)
    return image.crop((0, 0, width, final_height))

def _nota(kode):
    transaksi=db.query("""SELECT p.kode,p.tanggal_pinjam,p.tanggal_rencana_kembali,p.catatan,
      m.nim,m.nama,m.prodi,m.no_hp,m.email FROM peminjaman p
      JOIN mahasiswa m ON m.id=p.mahasiswa_id WHERE p.kode=?""",(kode,))
    if not transaksi:
        return
    row=transaksi[0]
    items=db.query("SELECT kode_barang,nama_barang,harga_satuan,jumlah FROM detail_peminjaman WHERE peminjaman_id=(SELECT id FROM peminjaman WHERE kode=?)",(kode,))
    nilai=sum(int(item["harga_satuan"])*int(item["jumlah"]) for item in items)
    jurusan=next(
        (
            department
            for department, programs in PROGRAM_STUDI_PER_JURUSAN.items()
            if row["prodi"] in programs
        ),
        "Tidak tercatat",
    )
    st.markdown("### Nota penyewaan")
    formatted_prices = format_rupiah_column(
        int(item["harga_satuan"]) * int(item["jumlah"]) for item in items
    )
    st.table([
        {
            "KODE BARANG": item["kode_barang"],
            "NAMA BARANG": item["nama_barang"],
            "JUMLAH": f'{item["jumlah"]} unit',
            "HARGA / NILAI BARANG": price,
        }
        for item, price in zip(items, formatted_prices)
    ])
    st.markdown(f"**Total Nilai Barang: {_rupiah(nilai)}**")
    receipt_buffer=BytesIO()
    _receipt_png(row,items,jurusan).save(receipt_buffer,format="PNG")
    receipt_png=receipt_buffer.getvalue()
    st.image(receipt_png,caption="Pratinjau nota penyewaan (PNG)",width="stretch")
    download_col,new_loan_col=st.columns(2)
    download_col.download_button(
        "Unduh nota penyewaan",
        receipt_png,
        file_name=f'nota_{kode}.png',
        mime="image/png",
        type="primary",
        width="stretch",
    )
    if new_loan_col.button(
        "Buat Penyewaan Baru",
        type="secondary",
        width="stretch",
    ):
        st.session_state["_reset_loan_form"] = True
        st.rerun()

def render():
    if st.session_state.pop("_reset_loan_form", False):
        _clear_previous_loan()

    header("PENYEWAAN BARU","Penyewaan Baru","Masukkan data penyewa dan barang dalam satu transaksi.")
    categories=db.query("SELECT id,nama FROM kategori ORDER BY nama")
    if not categories:
        st.warning("Tambahkan kategori sebelum mencatat penyewaan.")
        return

    st.markdown("#### Data mahasiswa")
    nim_col,nama_col=st.columns(2)
    matched_student=st.session_state.get("loan_matched_student")
    nim=nim_col.text_input(
        "NIM",
        key="loan_nim",
        on_change=_lookup_loan_student,
    )
    nama=nama_col.text_input(
        "Nama lengkap",
        key="loan_nama",
        disabled=matched_student is not None,
    )

    jurusan_col,prodi_col=st.columns(2)
    jurusan_options=list(PROGRAM_STUDI_PER_JURUSAN)
    existing_prodi=matched_student["prodi"] if matched_student else None
    if matched_student and not any(
        existing_prodi in programs
        for programs in PROGRAM_STUDI_PER_JURUSAN.values()
    ):
        jurusan_options.append("Data jurusan lama")
    jurusan=jurusan_col.selectbox(
        "Jurusan",
        jurusan_options,
        key="loan_jurusan",
        on_change=_reset_loan_program_studi,
    )
    program_options=PROGRAM_STUDI_PER_JURUSAN.get(jurusan, [])
    if matched_student and existing_prodi and existing_prodi not in program_options:
        program_options=[existing_prodi]
    prodi=prodi_col.selectbox(
        "Program studi",
        program_options,
        key="loan_program_studi",
    )

    hp_col,email_col=st.columns(2)
    no_hp=hp_col.text_input(
        "Nomor HP",
        key="loan_hp",
    )
    email=email_col.text_input(
        "Email",
        key="loan_email",
    )
    if matched_student:
        st.caption("Data mahasiswa ditemukan berdasarkan NIM dan telah diisi otomatis.")

    st.markdown("#### Detail penyewaan")
    if "loan_item_rows" not in st.session_state:
        st.session_state["loan_item_rows"] = [0]
        st.session_state["loan_next_row_id"] = 1

    row_ids=list(st.session_state["loan_item_rows"])
    used_item_ids=set()
    for row_id in row_ids:
        item_key=f"loan_item_{row_id}"
        quantity_key=f"loan_quantity_{row_id}"
        item_id=_selected_item_id(st.session_state.get(item_key))
        if item_id is None:
            continue
        if item_id in used_item_ids:
            st.session_state.pop(item_key, None)
            st.session_state.pop(quantity_key, None)
        else:
            used_item_ids.add(item_id)

    selected_items=[]
    all_rows_valid=True
    remove_row=None
    for number,row_id in enumerate(row_ids,start=1):
        st.markdown(f"**Barang {number}**")
        category_col,item_col,qty_col,remove_col=st.columns(
            [1,2,1.5,0.35],
            vertical_alignment="top",
        )
        category_key=f"loan_category_{row_id}"
        item_key=f"loan_item_{row_id}"
        quantity_key=f"loan_quantity_{row_id}"
        category=category_col.selectbox(
            "Kategori",
            categories,
            format_func=lambda row:row["nama"],
            key=category_key,
            on_change=_reset_selected_item,
            args=(item_key,quantity_key),
            label_visibility="collapsed",
        )
        barang=db.query(
            "SELECT id,kode,nama,tersedia,harga FROM inventaris WHERE kategori_id=? ORDER BY nama",
            (category["id"],),
        )
        barang_tersedia=[item for item in barang if int(item["tersedia"]) > 0]
        selected_item_id=_selected_item_id(st.session_state.get(item_key))
        selected_elsewhere={
            _selected_item_id(st.session_state.get(f"loan_item_{other_row_id}"))
            for other_row_id in row_ids
            if other_row_id != row_id
        }
        item_options=[
            item for item in barang_tersedia
            if item["id"] not in selected_elsewhere
        ]
        item_options.extend(
            item for item in barang
            if item["id"] == selected_item_id
            and item["id"] not in {option["id"] for option in item_options}
            and item["id"] not in selected_elsewhere
        )
        if _selected_item_id(st.session_state.get(item_key)) not in {
            item["id"] for item in item_options
        }:
            st.session_state.pop(item_key, None)
            st.session_state.pop(quantity_key, None)
        if item_options:
            item=item_col.selectbox(
                "Barang",
                item_options,
                format_func=lambda row:f'{row["kode"]} - {row["nama"]} | stok {row["tersedia"]} | Rp {row["harga"]:,}'.replace(",","."),
                key=item_key,
                on_change=_reset_quantity,
                args=(quantity_key,),
                label_visibility="collapsed",
            )
            if item is not None:
                stock=int(item["tersedia"])
                if stock <= 0:
                    item_col.markdown(
                        '<div style="min-height:42px;box-sizing:border-box;display:flex;align-items:center;'
                        'padding:8px 12px;background:#eaf2ff;border:1px solid #bfd3ec;border-radius:8px;'
                        'color:#1e40af">Stok habis (0). Barang ini tidak dapat disewa.</div>',
                        unsafe_allow_html=True,
                    )
                    minus_col,quantity_col,plus_col=qty_col.columns(
                        [1,1,1],
                        vertical_alignment="top",
                    )
                    minus_col.button(
                        "−",
                        key=f"decrease_loan_quantity_{row_id}",
                        help="Kurangi jumlah barang",
                        disabled=True,
                        width="stretch",
                    )
                    quantity_col.markdown(
                        '<div style="height:42px;display:flex;align-items:center;justify-content:center;'
                        'font-weight:400">0</div>',
                        unsafe_allow_html=True,
                    )
                    plus_col.button(
                        "+",
                        key=f"increase_loan_quantity_{row_id}",
                        help="Tambah jumlah barang",
                        disabled=True,
                        width="stretch",
                    )
                    all_rows_valid=False
                else:
                    qty_key=quantity_key
                    qty=max(1,min(int(st.session_state.get(qty_key,1)),stock))
                    st.session_state[qty_key]=qty
                    minus_col,quantity_col,plus_col=qty_col.columns(
                        [1,1,1],
                        vertical_alignment="top",
                    )
                    minus_col.button(
                        "−",
                        key=f"decrease_loan_quantity_{row_id}",
                        help="Kurangi jumlah barang",
                        disabled=qty <= 1,
                        on_click=_change_quantity,
                        args=(qty_key,-1,stock),
                        width="stretch",
                    )
                    quantity_col.markdown(
                        f'<div style="height:42px;display:flex;align-items:center;justify-content:center;'
                        f'font-weight:400">{qty}</div>',
                        unsafe_allow_html=True,
                    )
                    plus_col.button(
                        "+",
                        key=f"increase_loan_quantity_{row_id}",
                        help="Tambah jumlah barang",
                        disabled=qty >= stock,
                        on_click=_change_quantity,
                        args=(qty_key,1,stock),
                        width="stretch",
                    )
                    qty_col.caption(
                        f"Stok tersedia: {stock} unit"
                        + (" - stok penuh" if qty >= stock else "")
                    )
                    selected_items.append((item["id"],int(qty)))
            else:
                item_col.markdown(
                    '<div style="min-height:42px;box-sizing:border-box;display:flex;align-items:center;'
                    'padding:8px 12px;background:#eaf2ff;border:1px solid #bfd3ec;border-radius:8px;'
                    'color:#1e40af">Pilih barang yang tersedia.</div>',
                    unsafe_allow_html=True,
                )
                all_rows_valid=False
        else:
            message=(
                "Semua barang tersedia pada kategori ini sudah dipilih di baris lain."
                if barang_tersedia
                else "Tidak ada stok tersedia."
            )
            item_col.markdown(
                f'<div style="min-height:42px;box-sizing:border-box;display:flex;align-items:center;'
                f'padding:8px 12px;background:#eaf2ff;border:1px solid #bfd3ec;border-radius:8px;'
                f'color:#1e40af">{message}</div>',
                unsafe_allow_html=True,
            )
            all_rows_valid=False

        if len(row_ids) > 1 and remove_col.button(
            "Hapus",
            key=f"remove_loan_item_{row_id}",
            icon=":material/delete:",
            help="Hapus baris barang ini",
        ):
            remove_row=row_id

    if remove_row is not None:
        st.session_state["loan_item_rows"].remove(remove_row)
        st.session_state.pop(f"loan_item_{remove_row}", None)
        st.session_state.pop(f"loan_quantity_{remove_row}", None)
        st.rerun()

    if st.button("Tambah barang lain",icon=":material/add:"):
        next_id=st.session_state["loan_next_row_id"]
        st.session_state["loan_item_rows"].append(next_id)
        st.session_state["loan_next_row_id"]=next_id+1
        st.rerun()

    a,b=st.columns(2)
    tgl_pinjam=a.date_input("Tanggal sewa",value=date.today())
    tgl_kembali=b.date_input("Rencana kembali",value=date.today()+timedelta(days=3),min_value=date.today())
    catatan=st.text_area("Catatan",placeholder="Tuliskan keperluan penyewaan")
    ok=st.button("Simpan penyewaan",type="primary",width="stretch")
    if ok:
        nim=str(st.session_state.get("loan_nim","")).strip()
        nama=str(st.session_state.get("loan_nama","")).strip()
        no_hp=str(st.session_state.get("loan_hp","")).strip()
        email=str(st.session_state.get("loan_email","")).strip()
        missing_fields=[]
        if not nim:
            missing_fields.append("NIM")
        if not nama:
            missing_fields.append("Nama")
        if jurusan not in PROGRAM_STUDI_PER_JURUSAN:
            missing_fields.append("Jurusan")
        if not prodi or prodi not in PROGRAM_STUDI_PER_JURUSAN.get(jurusan, []):
            missing_fields.append("Program Studi")
        if not no_hp:
            missing_fields.append("Nomor HP")
        if not email:
            missing_fields.append("Email")

        identity_valid=not missing_fields
        if missing_fields:
            st.error(
                "Gagal menyimpan: Data mahasiswa belum lengkap! "
                f"Silakan lengkapi bagian [{' / '.join(missing_fields)}]."
            )

        name_mismatch=(
            matched_student is not None
            and " ".join(nama.split()).casefold()
            != " ".join(matched_student["nama"].split()).casefold()
        )
        if name_mismatch:
            st.error(
                f"NIM {nim} sudah terdaftar atas nama {matched_student['nama']}. "
                "Silakan periksa kembali data masukan Anda."
            )
            identity_valid=False
        if nim and (not nim.isascii() or not nim.isdigit()):
            st.error("Gagal menyimpan: NIM hanya boleh berisi angka tanpa titik, spasi, atau huruf.")
            identity_valid=False
        if nama and not all(character.isalpha() or character == " " for character in nama):
            st.error("Gagal menyimpan: Nama lengkap hanya boleh berisi huruf dan spasi.")
            identity_valid=False
        if no_hp and (not no_hp.isascii() or not no_hp.isdigit()):
            st.error("Gagal menyimpan: Nomor HP hanya boleh berisi angka.")
            identity_valid=False

        detail_valid=(
            bool(selected_items)
            and all_rows_valid
            and all(isinstance(qty, int) and qty > 0 for _, qty in selected_items)
        )
        if not detail_valid:
            st.error(
                "Gagal menyimpan: Silakan pilih barang dan tentukan jumlah unit yang akan disewa."
            )

        dates_valid=tgl_kembali >= tgl_pinjam
        if not dates_valid:
            st.error(
                "Gagal menyimpan: Rencana tanggal kembali tidak boleh lebih awal dari tanggal sewa."
            )

        if identity_valid and detail_valid and dates_valid:
            try:
                code=db.create_loan({"nim":nim,"nama":nama,"prodi":prodi,"no_hp":no_hp,"email":email},tgl_pinjam.isoformat(),tgl_kembali.isoformat(),selected_items,catatan.strip())
                st.session_state["last_loan_code"]=code
                st.rerun()
            except Exception as error:
                st.error(f"Gagal menyimpan penyewaan: {error}")

    if st.session_state.get("last_loan_code"):
        _nota(st.session_state["last_loan_code"])

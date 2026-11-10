import sqlite3
import streamlit as st
import pandas as pd
from core import db
from views.common import format_rupiah_column, header


def _render_table(frame, column_config):
    st.markdown(
        """
        <style>
        [data-testid="stDataObjectViz"] th,
        div[data-testid="stTable"] th,
        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataFrame"] [role="columnheader"] *,
        [data-testid="stDataEditor"] th,
        [data-testid="stDataEditor"] [role="columnheader"],
        [data-testid="stDataEditor"] [role="columnheader"] * {
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(
        frame,
        column_config=column_config,
        width="stretch",
        hide_index=True,
    )


@st.dialog("Edit data inventaris", width="medium")
def _edit_inventory_dialog(inventory_id):
    item = db.query(
        """SELECT id,nama,kategori_id,jumlah,tersedia,harga,kondisi,lokasi
        FROM inventaris WHERE id=?""",
        (inventory_id,),
    )
    if not item:
        st.error("Barang inventaris tidak ditemukan.")
        return
    item = item[0]
    categories = db.query("SELECT id,nama FROM kategori ORDER BY nama")
    category_ids = [category["id"] for category in categories]
    with st.form(f"edit_inventory_{inventory_id}"):
        nama = st.text_input("Nama barang", value=item["nama"])
        kategori_id = st.selectbox(
            "Kategori",
            category_ids,
            index=category_ids.index(item["kategori_id"]),
            format_func=lambda category_id: next(
                category["nama"] for category in categories
                if category["id"] == category_id
            ),
        )
        jumlah = st.number_input(
            "Jumlah",
            min_value=1,
            value=item["jumlah"],
            step=1,
        )
        harga = st.number_input(
            "Harga (Rp)",
            min_value=0,
            value=item["harga"],
            step=10000,
        )
        kondisi = st.selectbox(
            "Kondisi",
            ["Baik", "Perlu perbaikan", "Rusak"],
            index=["Baik", "Perlu perbaikan", "Rusak"].index(item["kondisi"]),
        )
        lokasi = st.text_input("Lokasi", value=item["lokasi"])
        simpan = st.form_submit_button("Simpan Perubahan", type="primary")
    if simpan:
        try:
            if not nama.strip() or not lokasi.strip():
                raise ValueError("Nama barang dan lokasi wajib diisi.")
            kode = db.update_inventory(
                inventory_id,
                nama.strip(),
                kategori_id,
                jumlah,
                harga,
                kondisi,
                lokasi.strip(),
            )
            st.success(f"Perubahan disimpan. Kode barang: {kode}.")
            st.rerun()
        except Exception as error:
            st.error(f"Gagal menyimpan perubahan: {error}")


def _render_inventory_table(rows):
    frame = pd.DataFrame(rows)
    frame["HARGA"] = format_rupiah_column(frame["HARGA"])
    frame["EDIT"] = ":material/edit:"
    item_ids = frame.pop("ID").tolist()
    _render_table(frame, {
        "KODE": st.column_config.TextColumn("KODE", width=90, alignment="center"),
        "NAMA BARANG": st.column_config.TextColumn("NAMA BARANG", width=220, alignment="left"),
        "KATEGORI": st.column_config.TextColumn("KATEGORI", width=120, alignment="left"),
        "JUMLAH": st.column_config.NumberColumn("JUMLAH", width=70, format="%d", alignment="center"),
        "TERSEDIA": st.column_config.NumberColumn("TERSEDIA", width=70, format="%d", alignment="center"),
        "DISEWA": st.column_config.NumberColumn("DISEWA", width=70, format="%d", alignment="center"),
        "HARGA": st.column_config.TextColumn("HARGA", width=130, alignment="left"),
        "KONDISI": st.column_config.TextColumn("KONDISI", width=80, alignment="center"),
        "LOKASI": st.column_config.TextColumn("LOKASI", width=120, alignment="left"),
        "EDIT": st.column_config.ButtonColumn(
            "EDIT",
            width="small",
            type="tertiary",
            key="inventory_edit_action",
        ),
    })
    click = st.session_state.get("inventory_edit_action")
    if click is not None:
        row_index = click["row"]
        if 0 <= row_index < len(item_ids):
            _edit_inventory_dialog(item_ids[row_index])


def render():
    header("INVENTARIS","Inventaris","Kelola data barang, jumlah unit, kondisi, dan lokasi penyimpanan.")
    tab_barang, tab_kategori = st.tabs(["Daftar Barang", "Kelola Kategori"])

    with tab_barang:
        cats=db.query("SELECT id,nama FROM kategori ORDER BY nama")
        with st.expander("＋ Tambah inventaris",expanded=False):
            if cats:
                cat=st.selectbox("Kategori",cats,format_func=lambda x:x["nama"],key="inventory_category")
                kode_berikut=db.next_inventory_code(cat["id"])
                with st.form("add_inv",clear_on_submit=True):
                    a,b=st.columns(2)
                    a.text_input(
                        "Kode barang",
                        value=kode_berikut or "Nomor kode kategori sudah penuh",
                        disabled=True,
                    )
                    nama=b.text_input("Nama barang")
                    qty=b.number_input("Jumlah unit",min_value=1,step=1)
                    harga=a.number_input("Harga barang (Rp)",min_value=1,step=10000)
                    kondisi=a.selectbox("Kondisi",["Baik","Perlu perbaikan","Rusak"])
                    lokasi=b.text_input("Lokasi penyimpanan")
                    ok=st.form_submit_button(
                        "Simpan inventaris",
                        type="primary",
                        disabled=kode_berikut is None,
                    )
                if ok:
                    try:
                        if not nama.strip() or not lokasi.strip():
                            raise ValueError("Data belum terisi semua")
                        kode=db.create_inventory(
                            nama.strip(),
                            cat["id"],
                            qty,
                            harga,
                            kondisi,
                            lokasi.strip(),
                        )
                        st.success(f"Inventaris berhasil ditambahkan dengan kode {kode}.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Kode barang sudah digunakan.")
                    except Exception as e:
                        st.error(f"Gagal menyimpan: {e}")
            else:
                st.info("Tambahkan kategori terlebih dahulu sebelum membuat inventaris.")
        rows=db.query("""SELECT i.id AS 'ID',i.kode AS 'KODE',i.nama AS 'NAMA BARANG',
            COALESCE(k.nama,'Tanpa kategori') AS 'KATEGORI',
            i.jumlah AS 'JUMLAH',i.tersedia AS 'TERSEDIA',
            (i.jumlah-i.tersedia) AS 'DISEWA',i.harga AS 'HARGA',
            i.kondisi AS 'KONDISI',i.lokasi AS 'LOKASI'
            FROM inventaris i LEFT JOIN kategori k ON k.id=i.kategori_id
            ORDER BY i.kode""")
        if rows:
            _render_inventory_table(rows)
        else: st.info("Belum ada inventaris.")
        with st.expander("Hapus inventaris"):
            opts=db.query("SELECT id,kode,nama FROM inventaris ORDER BY nama")
            if opts:
                chosen=st.selectbox("Pilih barang",opts,format_func=lambda x:f'{x["kode"]} — {x["nama"]}')
                if st.button("Hapus barang terpilih"):
                    try:
                        db.execute("DELETE FROM inventaris WHERE id=?",(chosen["id"],)); st.success("Barang dihapus."); st.rerun()
                    except Exception as e: st.error(f"Barang tidak dapat dihapus karena terkait transaksi: {e}")

    with tab_kategori:
        with st.form("add_cat",clear_on_submit=True):
            a,b=st.columns([1,2]); nama=a.text_input("Nama kategori"); ket=b.text_input("Keterangan")
            ok=st.form_submit_button("Tambah kategori",type="primary")
        if ok:
            try:
                if not nama.strip(): raise ValueError("Nama kategori wajib diisi.")
                kode_kategori, _ = db.create_category(nama.strip(), ket.strip())
                st.success(f"Kategori {kode_kategori} ditambahkan."); st.rerun()
            except Exception as e: st.error(f"Gagal: {e}")
        rows=db.query("""SELECT k.kode AS 'ID KATEGORI',
            k.nama AS 'NAMA KATEGORI',k.keterangan AS 'KETERANGAN',
            COUNT(i.id) AS 'JUMLAH BARANG'
            FROM kategori k LEFT JOIN inventaris i ON i.kategori_id=k.id
            GROUP BY k.id ORDER BY k.nama""")
        if rows:
            _render_table(pd.DataFrame(rows), {
                "ID KATEGORI": st.column_config.TextColumn("ID KATEGORI", width="small", alignment="center"),
                "NAMA KATEGORI": st.column_config.TextColumn("NAMA KATEGORI", width="medium", alignment="left"),
                "KETERANGAN": st.column_config.TextColumn("KETERANGAN", width="large", alignment="left"),
                "JUMLAH BARANG": st.column_config.NumberColumn("JUMLAH BARANG", width="small", format="%d", alignment="center"),
            })
        with st.expander("Hapus kategori"):
            opts=db.query("""SELECT k.id,k.nama,COUNT(i.id) jumlah_barang
                FROM kategori k LEFT JOIN inventaris i ON i.kategori_id=k.id
                GROUP BY k.id ORDER BY k.nama""")
            if opts:
                chosen=st.selectbox(
                    "Kategori",
                    opts,
                    format_func=lambda x:f'{x["nama"]} ({x["jumlah_barang"]} barang)',
                )
                if chosen["jumlah_barang"]:
                    st.info("Kategori tidak dapat dihapus selama masih memiliki barang.")
                if st.button(
                    "Hapus kategori terpilih",
                    disabled=chosen["jumlah_barang"] > 0,
                ):
                    try:
                        db.delete_category(chosen["id"])
                        st.success("Kategori dihapus."); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus kategori: {e}")

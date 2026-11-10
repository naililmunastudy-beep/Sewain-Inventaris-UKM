"""Sewain: sistem penyewaan inventaris UKM."""
import streamlit as st

st.set_page_config(
    page_title="Sewain",
    page_icon=":material/inventory_2:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import db, styles
from core.utils import HALAMAN
from views import dashboard, inventaris, laporan, penyewaan_baru, pengembalian, riwayat

styles.inject()
db.init_db()
st.markdown(
    """
    <style>
    [data-testid="stDataObjectViz"] th,
    div[data-testid="stTable"] th,
    [data-testid="stDataFrame"] [role="columnheader"],
    [data-testid="stDataFrame"] [role="columnheader"] *,
    [data-testid="stDataEditor"] [role="columnheader"],
    [data-testid="stDataEditor"] [role="columnheader"] * {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

RUTE = {
    HALAMAN[0]: dashboard.render,
    HALAMAN[1]: penyewaan_baru.render,
    HALAMAN[2]: pengembalian.render,
    HALAMAN[3]: riwayat.render,
    HALAMAN[4]: laporan.render,
    HALAMAN[5]: inventaris.render,
}

st.session_state.setdefault("nav", HALAMAN[0])
if st.session_state["nav"] not in RUTE:
    st.session_state["nav"] = HALAMAN[0]
with st.sidebar:
    st.markdown("""
        <div class="brand">
            <div class="brand-logo"><span class="material-symbols-rounded">inventory_2</span></div>
            <div><div class="brand-name">Sewain</div><div class="brand-sub">INVENTARIS • UKM</div></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("### Menu Utama")
    ikon_navigasi = [
        ":material/dashboard:",
        ":material/post_add:",
        ":material/assignment_return:",
        ":material/history:",
        ":material/analytics:",
        ":material/inventory_2:",
    ]
    for halaman, ikon in zip(HALAMAN, ikon_navigasi):
        st.button(
            halaman,
            key=f"nav_{halaman}",
            icon=ikon,
            type="primary" if st.session_state["nav"] == halaman else "secondary",
            width="stretch",
            on_click=lambda tujuan=halaman: st.session_state.update(nav=tujuan),
        )
    st.divider()
    st.markdown('<div class="sidebar-info"><span class="online-dot"></span> <b>Sistem Penyewaan UKM</b></div>', unsafe_allow_html=True)

RUTE[st.session_state["nav"]]()

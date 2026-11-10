import streamlit as st

def inject():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0&display=swap');
    :root { --navy:#102a56; --blue:#2563eb; --sky:#eaf2ff; --ink:#172b4d; --muted:#60748f; --line:#c9daf0; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background:linear-gradient(115deg,#e5effb 0%,#f4f8fd 48%,#e8f1fc 100%); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(232,241,252,.88); }
    [data-testid="stMainBlockContainer"] { padding-top:1.5rem;padding-bottom:2rem; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#102a56 0%,#174a91 100%); }
    [data-testid="stSidebar"] * { color:#f4f8ff !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"] { background:transparent !important;border:1px solid transparent !important;color:#f4f8ff !important;box-shadow:none !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:hover { background:#ffffff1c !important;border-color:#ffffff30 !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] { background:#b9d7ff !important;border-color:#b9d7ff !important;color:#102a56 !important;box-shadow:0 4px 12px #061b3933 !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] * { color:#102a56 !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button { justify-content:flex-start !important;text-align:left !important; }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button > div { width:100%;justify-content:flex-start !important; }
    [data-testid="stSidebar"] .brand-logo .material-symbols-rounded { color:#1d4ed8 !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:9px 12px; border-radius:10px; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.12); }
    .brand { display:flex; gap:12px; align-items:center; padding:8px 4px 24px; }
    .brand-logo { display:flex; align-items:center; justify-content:center; background:#fff; color:#1d4ed8; border-radius:16px; box-shadow:0 8px 22px #071d3c33; }
    .material-symbols-rounded { font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;font-size:27px;line-height:1;letter-spacing:normal;text-transform:none;white-space:nowrap;direction:ltr;font-feature-settings:'liga';-webkit-font-feature-settings:'liga';-webkit-font-smoothing:antialiased; }
    .brand-logo { width:48px;height:48px;font-size:25px; }
    .brand-name { font-family:Manrope,sans-serif;font-size:22px;font-weight:800;letter-spacing:0; }
    .brand-sub { font-size:10px;letter-spacing:1.5px;opacity:.75; }
    .sidebar-info { margin-top:16px;padding:14px;border:1px solid #ffffff33;background:#ffffff12;border-radius:14px;line-height:1.8; }
    .online-dot { display:inline-block;width:8px;height:8px;background:#4ade80;border-radius:50%;margin-right:6px; }
    .eyebrow { color:#2563eb;font-size:11px;font-weight:800;letter-spacing:2px; }
    h1,h2,h3 { font-family:Manrope,sans-serif !important;color:#102a56;letter-spacing:0; }
    [data-testid="stMetric"] { background:linear-gradient(145deg,#f8fbff 0%,#e6f0fc 100%);padding:15px 18px;border:1px solid #c5d8f0;border-top:3px solid #3979c9;border-radius:8px;box-shadow:0 4px 12px #183a6810; }
    [data-testid="stMetricLabel"] { color:#526b8a; }
    [data-testid="stMetricValue"] { color:#102a56;font-family:Manrope,sans-serif; }
    div.stButton > button, div.stFormSubmitButton > button { border-radius:8px;font-weight:700;min-height:42px; }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background:#2563eb !important;border-color:#2563eb !important;color:#fff !important; }
    div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { background:#174ea6 !important;border-color:#174ea6 !important; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { background:#f7faff !important;border-color:#bfd3ec !important; }
    div[data-baseweb="select"] > div { background:#f7faff !important;border-color:#bfd3ec !important; }
    div[data-testid="stForm"] { border-radius:10px;border-color:#c8d9ee; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { background:#f9fbff;border:1px solid #c9daf0;border-radius:8px;overflow:hidden; }
    div[data-testid="stTable"] th { background:#e6f0fc !important;color:#172b4d !important;text-align:center !important; }
        [data-testid="stDataFrame"] .stDataFrameGlideDataEditor {
            --gdg-accent-color:#2563eb !important;
            --gdg-accent-fg:#ffffff !important;
            --gdg-text-dark:#183655 !important;
            --gdg-text-medium:#526b8a !important;
            --gdg-text-light:#6b7c93 !important;
            --gdg-bg-icon-header:#e6f0fc !important;
            --gdg-fg-icon-header:#526b8a !important;
            --gdg-text-header:#172b4d !important;
            --gdg-text-group-header:#172b4d !important;
            --gdg-bg-group-header:#e6f0fc !important;
            --gdg-bg-group-header-hovered:#d8e8fb !important;
            --gdg-text-header-selected:#172b4d !important;
            --gdg-bg-cell:#f8fbff !important;
            --gdg-bg-cell-medium:#edf4fc !important;
            --gdg-bg-header:#e6f0fc !important;
            --gdg-bg-header-has-focus:#d8e8fb !important;
            --gdg-bg-header-hovered:#d8e8fb !important;
            --gdg-bg-bubble:#dceafb !important;
            --gdg-bg-bubble-selected:#bfd3ec !important;
            --gdg-bg-search-result:rgba(37,99,235,.18) !important;
            --gdg-border-color:#c9daf0 !important;
            --gdg-horizontal-border-color:#d7e3f1 !important;
            --gdg-drilldown-border:#c9daf0 !important;
        }
        [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] { border-color:#c9daf0 !important; }
    .page-kicker { display:inline-block;padding:4px 8px;background:#d8e8fb;border-radius:4px;color:#1c58a5;font-size:11px;font-weight:800;letter-spacing:1.8px;text-transform:uppercase; }
    .page-intro { color:#526b8a;margin-top:-8px;margin-bottom:18px; }
    .notice { padding:12px 15px;background:linear-gradient(100deg,#dceafb,#edf5ff);border:1px solid #bfd4ef;border-left:4px solid #3979c9;border-radius:8px;color:#1e40af; }
    </style>
    """, unsafe_allow_html=True)

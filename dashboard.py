# dashboard.py — PROFESSIONAL UI EDITION
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ───────────────────── PAGE CONFIGURATION ─────────────────────
st.set_page_config(
    page_title="AP-TG MW DPR | Command Center",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ───────────────────── CUSTOM CSS & THEME ─────────────────────
# This function injects custom CSS to make the dashboard look like a web app
def inject_custom_css():
    st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Gradient Header Text */
        .gradient-text {
            background: linear-gradient(90deg, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        /* KPI Card Styling */
        .kpi-card {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            border-color: #3b82f6;
        }
        .kpi-value {
            font-size: 32px;
            font-weight: 800;
            margin: 0;
            color: #ffffff;
        }
        .kpi-label {
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 5px;
        }
        .kpi-sub {
            font-size: 10px;
            color: #3b82f6;
            font-weight: 600;
        }

        /* Customizing Streamlit UI Elements */
        div[data-testid="stExpander"] {
            border: none;
            background-color: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
        }
        
        /* Sidebar Polish */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(255,255,255,0.05);
            border-radius: 5px;
            color: #fff;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3b82f6 !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ───────────────────── PASSWORD PROTECTION ─────────────────────
def check_password():
    def password_entered():
        if st.session_state["password"] == "APTGMW2025": 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<br><br><h1 style='text-align:center;'>🔒 Secure Access</h1>", unsafe_allow_html=True)
            st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
            st.markdown("<p style='text-align:center; color:gray;'>AP & TG MW Project Dashboard</p>", unsafe_allow_html=True)
        return False
    elif not st.session_state["password_correct"]:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.markdown("<br><br><h1 style='text-align:center;'>🔒 Secure Access</h1>", unsafe_allow_html=True)
            st.text_input("Wrong Password", type="password", on_change=password_entered, key="password")
            st.error("Access Denied. Please try again.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ───────────────────── SIDEBAR & THEME LOGIC ─────────────────────

st.sidebar.markdown("### 📡 MW DPR Dashboard")
st.sidebar.markdown(f"<div style='font-size:12px; color:#4ade80; margin-bottom:15px;'>● Live System Active</div>", unsafe_allow_html=True)

# Logo
st.sidebar.image("https://companieslogo.com/img/orig/NOK_BIG-8604230c.png?t=1720244493", use_container_width=True)
st.sidebar.markdown("---")

# ───────────────────── DATA LOADING ─────────────────────

@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1BD-Bww-k_3jVwJAGqBbs02YcOoUyNrOWcY_T9xvnbgY"
    gid = "0"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    df = pd.read_csv(csv_url)
    
    # Smart Date Conversion
    date_cols = df.columns[df.columns.str.contains("Date|DATE", case=False)]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

with st.sidebar:
    with st.status("Syncing Database...", expanded=True) as status:
        try:
            df = load_data()
            status.update(label="Data Synced Successfully", state="complete", expanded=False)
        except Exception as e:
            st.error("Connection Failed")
            st.stop()

# ───────────────────── FILTERS ─────────────────────

st.sidebar.markdown("#### 🛠 Filter Controls")

date_columns = [col for col in df.columns if "Date" in col or "DATE" in col]
valid_dates = pd.to_datetime(df[date_columns].stack().dropna(), errors='coerce')
min_date = valid_dates.min().date() if not valid_dates.empty else datetime.now().date()
max_date = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()

with st.sidebar.expander("📅 Date Range", expanded=False):
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

selected_circle = st.sidebar.selectbox("📍 Circle", ["All"] + sorted(df["Circle"].dropna().unique().tolist()))
selected_month = st.sidebar.selectbox("🗓 Month", ["All"] + sorted(df["Month"].dropna().unique().tolist()))
priority = st.sidebar.multiselect("🔥 Priority", ["P0", "P1"], default=["P0", "P1"])

# ───────────────────── DATA FILTERING ENGINE ─────────────────────

filtered = df.copy()
if date_columns:
    mask = pd.Series([False] * len(filtered))
    for col in date_columns:
        dates = pd.to_datetime(filtered[col], errors='coerce')
        mask |= (dates.dt.date >= start_date) & (dates.dt.date <= end_date)
    filtered = filtered[mask]

if selected_circle != "All": filtered = filtered[filtered["Circle"] == selected_circle]
if selected_month != "All": filtered = filtered[filtered["Month"] == selected_month]
if priority: filtered = filtered[filtered["Priority(P0/P1)"].isin(priority)]

# Status Logic
def get_status(r):
    if pd.notna(r.get("PRI OPEN DATE")): return "PRI Open"
    if pd.notna(r.get("HOP AT DATE")): return "AT Completed"
    if pd.notna(r.get("ACTUAL HOP RFAI OFFERED DATE")): return "RFAI Offered"
    if pd.notna(r.get("HOP MATERIAL DELIVERY DATE")): return "Material Delivered"
    if pd.notna(r.get("HOP MATERIAL DISPATCH DATE")): return "In-Transit"
    return "Planning"

filtered["Current Status"] = filtered.apply(get_status, axis=1)

# ───────────────────── KPI COMPONENT GENERATOR ─────────────────────

def kpi_card_html(label, value, total):
    pct = (value / total * 100) if total > 0 else 0
    color = "#ef4444" if label in ["PRI", "CCRFAI"] else "#ffffff"
    sub_color = "#f87171" if label in ["PRI", "CCRFAI"] else "#3b82f6"
    
    return f"""
    <div class="kpi-card">
        <h3 class="kpi-value" style="color:{color}">{value}</h3>
        <div class="kpi-label">{label}</div>
        <div class="kpi-sub" style="color:{sub_color}">{pct:.1f}%</div>
    </div>
    """

# ───────────────────── HEADER SECTION ─────────────────────

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 class='gradient-text'>AP & TG MW Project Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"**Scope:** {len(filtered):,} Hops | **Last Refreshed:** {datetime.now().strftime('%H:%M • %d %b')}")
with c2:
    if st.button("📊 Full Summary Report", use_container_width=True, type="primary"):
        st.session_state.show_summary = True
        st.rerun()

if st.session_state.get("show_summary", False):
    # SUMMARY VIEW (Simplified for brevity - uses same logic as main)
    st.info("Displaying Full Summary Report Mode")
    # (Insert Summary Logic Here if needed, or just use the button to toggle layouts)
    if st.button("Back to Dashboard"):
        st.session_state.show_summary = False
        st.rerun()

st.markdown("---")

# ───────────────────── KPI GRID LAYOUT ─────────────────────

total_scope = len(filtered) if len(filtered) > 0 else 1
rfa_i_offered = len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()])
pri_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"])
ccrfai_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "CCRFAI"])

kpi_data = [
    ("Scope", len(filtered)), ("LB", len(filtered[~filtered["PLAN ID"].isna()])),
    ("SR", len(filtered[~filtered["HOP SR Date"].isna()])), ("RFAI", rfa_i_offered),
    ("Survey", len(filtered[~filtered["Survey Date"].isna()])), ("PRI", pri_count),
    ("CRFAI", rfa_i_offered - pri_count),
    ("Media", len(filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["Media Date"].isna())])),
    ("CCRFAI", ccrfai_count), ("MO", len(filtered[~filtered["HOP MO DATE"].isna()])),
    ("Mat. Disp.", len(filtered[~filtered["HOP MATERIAL DISPATCH DATE"].isna()])),
    ("MOS", len(filtered[~filtered["HOP MATERIAL DELIVERY DATE"].isna()])),
    ("I&C", len(filtered[~filtered["HOP I&C DATE"].isna()])),
    ("Alignment", len(filtered[~filtered["Alignment Date"].isna()])),
    ("NMS Done", len(filtered[filtered["VISIBLE IN NMS"].astype(str).str.contains("YES|Yes|yes", na=False)])),
    ("Phy AT Offer", len(filtered[~filtered["PHY-AT OFFER DATE"].isna()])),
    ("Soft AT Offer", len(filtered[~filtered["SOFT AT OFFER DATE"].isna()])),
    ("Phy AT Acc", len(filtered[~filtered["PHY-AT ACCEPTANCE DATE"].isna()])),
    ("Soft AT Acc", len(filtered[~filtered["SOFT AT ACCEPTANCE DATE"].isna()])),
    ("HOP AT Done", len(filtered[~filtered["HOP AT DATE"].isna()]))
]

# Responsive Grid: Break into rows of 5 for better spacing
rows = [kpi_data[i:i+5] for i in range(0, len(kpi_data), 5)]

for row_items in rows:
    cols = st.columns(len(row_items))
    for idx, (label, val) in enumerate(row_items):
        with cols[idx]:
            st.markdown(kpi_card_html(label, val, total_scope), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ───────────────────── CHARTS & VISUALS ─────────────────────

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🥧 Status Distribution")
    status_counts = filtered["Current Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
    fig = px.pie(status_counts, names="Status", values="Count", hole=0.5, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=20, r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 📊 Hops by Circle")
    circle_counts = filtered["Circle"].value_counts().reset_index()
    circle_counts.columns = ["Circle", "Count"]
    
    fig2 = px.bar(circle_counts, x="Circle", y="Count", text="Count",
                  color="Count", color_continuous_scale="Bluyl")
    fig2.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       xaxis=dict(showgrid=False, color="white"), 
                       yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", color="white"))
    st.plotly_chart(fig2, use_container_width=True)

# ───────────────────── URGENT ALERTS ─────────────────────

pri_list = filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"]
if not pri_list.empty:
    st.markdown(f"""
    <div style="background-color: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; padding: 15px; border-radius: 10px; margin: 20px 0;">
        <h3 style="color: #ef4444; margin:0;">🚨 ACTION REQUIRED: {len(pri_list)} Hops Blocked on PRI</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("View PRI Details", expanded=True):
        st.dataframe(
            pri_list[["HOP A-B","SITE ID A","SITE ID B","PRI ISSUE CATEGORY","PRI REMARKS","PRI OPEN DATE"]],
            use_container_width=True, hide_index=True
        )

# ───────────────────── AGING ANALYSIS TABS ─────────────────────

st.markdown("### ⏳ Aging Analysis")

# Helper for aging
def calc_aging(df, date_col):
    if df.empty or date_col not in df.columns: return pd.Series([0] * len(df))
    dates = pd.to_datetime(df[date_col], errors='coerce')
    return (pd.Timestamp.now() - dates).dt.days

tab1, tab2, tab3 = st.tabs(["RFAI → MS1 (Integration)", "MS1 → MS2 (HOP AT)", "RFAI → MS2 (E2E)"])

# --- TAB 1: RFAI to MS1 ---
with tab1:
    rfai_done = filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()]
    ms1_pending = rfai_done[rfai_done["INTEGRATION DATE"].isna()].copy()
    
    if not ms1_pending.empty:
        ms1_pending["Aging Days"] = calc_aging(ms1_pending, "ACTUAL HOP RFAI OFFERED DATE")
        
        col_a, col_b = st.columns([1,3])
        with col_a:
            st.markdown(f"""
            <div style="padding:20px; background:rgba(59, 130, 246, 0.1); border-radius:10px; text-align:center;">
                <h2 style="color:#3b82f6; margin:0;">{len(ms1_pending)}</h2>
                <p style="margin:0;">Pending MS1</p>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.dataframe(
                ms1_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "ACTUAL HOP RFAI OFFERED DATE", "Aging Days"]].sort_values("Aging Days", ascending=False),
                use_container_width=True, hide_index=True
            )

# --- TAB 2: MS1 to MS2 ---
with tab2:
    ms1_done = filtered[~filtered["INTEGRATION DATE"].isna()]
    ms2_pending = ms1_done[ms1_done["HOP AT DATE"].isna()].copy()
    
    if not ms2_pending.empty:
        ms2_pending["Aging Days"] = calc_aging(ms2_pending, "INTEGRATION DATE")
        col_a, col_b = st.columns([1,3])
        with col_a:
             st.markdown(f"""
            <div style="padding:20px; background:rgba(16, 185, 129, 0.1); border-radius:10px; text-align:center;">
                <h2 style="color:#10b981; margin:0;">{len(ms2_pending)}</h2>
                <p style="margin:0;">Pending MS2</p>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.dataframe(
                ms2_pending[["Circle", "HOP A-B", "SITE ID A", "INTEGRATION DATE", "Aging Days"]].sort_values("Aging Days", ascending=False),
                use_container_width=True, hide_index=True
            )

# --- TAB 3: E2E ---
with tab3:
    e2e_pending = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()
    if not e2e_pending.empty:
        e2e_pending["Total Aging"] = calc_aging(e2e_pending, "ACTUAL HOP RFAI OFFERED DATE")
        st.dataframe(
            e2e_pending[["Circle", "HOP A-B", "ACTUAL HOP RFAI OFFERED DATE", "Total Aging"]].sort_values("Total Aging", ascending=False),
            use_container_width=True, hide_index=True
        )

# ───────────────────── SEARCHABLE DATA TABLE ─────────────────────

st.markdown("---")
st.markdown("### 🔎 Interactive Data Explorer")

# Default columns
default_cols = ["Circle", "Month", "HOP A-B", "SITE ID A", "SITE ID B", "Priority(P0/P1)", "Current Status", "Final Remarks"]
selected_cols = st.multiselect("Customize Table Columns", filtered.columns.tolist(), default=default_cols)

if selected_cols:
    st.dataframe(
        filtered[selected_cols],
        use_container_width=True,
        height=600,
        column_config={
            col: st.column_config.Column(width="medium") for col in selected_cols
        },
        hide_index=True
    )
    
    # Download
    c_d1, c_d2 = st.columns([1, 4])
    with c_d1:
        st.download_button(
            "📥 Download CSV",
            filtered[selected_cols].to_csv(index=False).encode(),
            f"MW_DPR_Extract_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            type="primary",
            use_container_width=True
        )

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; font-size: 12px; padding: 20px;'>
        AP & TG Circle Dashboard • Powered by Streamlit & Python <br>
        Data auto-refreshes every 60 seconds
    </div>
    """, 
    unsafe_allow_html=True
)

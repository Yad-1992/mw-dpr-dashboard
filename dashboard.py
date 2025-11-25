import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ───────────────────── PAGE SETUP ─────────────────────
# Must be the very first Streamlit command
st.set_page_config(page_title="AP-TG MW DPR", page_icon="📈", layout="wide")

# ───────────────────── PASSWORD PROTECTION ─────────────────────
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "APTGMW2025":  # ← PASSWORD
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.title("AP & TG MW DPR – Secure Access")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Access Denied. Please try again.")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()

# ───────────────────── THEME SETTINGS (LIGHT MODE) ─────────────────────
main_bg = "#f1f5f9"      # Light Grey Background
card_bg = "#ffffff"      # White Cards
text_color = "#0f172a"   # Dark Blue/Black Text
sub_text = "#64748b"     # Slate Grey Subtext
border_color = "#e2e8f0" # Light Border
pending_color = "#d97706"# Amber for alerts

st.markdown(f"""
<style>
    .stApp {{ background-color: {main_bg}; }}
    h1, h2, h3 {{ color: {text_color} !important; font-family: 'Segoe UI', sans-serif; }}
    .kpi-box {{
        background-color: {card_bg}; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid {border_color};
        text-align: center; margin-bottom: 10px; transition: transform 0.2s;
    }}
    .kpi-box:hover {{ transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
    .pending-value {{ color: {pending_color}; font-size: 28px; font-weight: 800; margin: 0; }}
    .kpi-value {{ font-size: 32px; font-weight: 800; margin: 0; line-height: 1.2; color: {text_color}; }}
    .kpi-label {{ font-size: 13px; color: {sub_text}; font-weight: 600; text-transform: uppercase; margin-top: 5px; }}
    .kpi-pct {{ font-size: 11px; font-weight: bold; background-color: rgba(0, 212, 255, 0.1); padding: 2px 6px; border-radius: 4px; display: inline-block; margin-top: 4px; color: {text_color}; }}
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: #888; border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)

# ───────────────────── DATA LOADING & FORMATTING ─────────────────────
@st.cache_data(ttl=60)
def load_data():
    sheet_id = "1BD-Bww-k_3jVwJAGqBbs02YcOoUyNrOWcY_T9xvnbgY"
    gid = "0"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(csv_url)
        # Convert date columns to datetime objects
        date_cols = df.columns[df.columns.str.contains("Date|DATE", case=False)]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()

def format_date_cols(df_in):
    """Helper function to format dates as DD-MMM-YY for display only"""
    df_out = df_in.copy()
    for col in df_out.columns:
        if pd.api.types.is_datetime64_any_dtype(df_out[col]):
            # Format: 25-Nov-25
            df_out[col] = df_out[col].dt.strftime('%d-%b-%y')
    return df_out

# Load Data
df = load_data()

if df.empty:
    st.error("Could not connect to Google Sheet. Please check the permissions or internet connection.")
    st.stop()

# ───────────────────── SIDEBAR ─────────────────────
st.sidebar.title("MW DPR Dashboard")
st.sidebar.markdown("Live • Auto-refresh")
st.sidebar.image("https://companieslogo.com/img/orig/NOK_BIG-8604230c.png?t=1720244493", use_container_width=True)
st.sidebar.success(f"✅ Data Synced\n{len(df):,} hops loaded")

st.sidebar.markdown("### 🔍 Filters")
c1, c2 = st.sidebar.columns(2)
with c1: 
    selected_circle = st.selectbox("Circle", ["All"] + sorted(df["Circle"].dropna().unique().tolist()))
with c2: 
    selected_month = st.selectbox("Month", ["All"] + sorted(df["Month"].dropna().unique().tolist()))

priority = st.sidebar.multiselect("Priority", ["P0", "P1"], default=["P0", "P1"])

# Dynamic Filters
if "Nominal Aop" in df.columns:
    nominal_options = sorted(df["Nominal Aop"].dropna().astype(str).unique().tolist())
    selected_nominal = st.sidebar.multiselect("Nominal Aop", nominal_options)
else:
    selected_nominal = []

if "Final Remarks" in df.columns:
    remarks_options = sorted(df["Final Remarks"].dropna().astype(str).unique().tolist())
    selected_remarks = st.sidebar.multiselect("Final Remarks", remarks_options)
else:
    selected_remarks = []

# Apply Filters
filtered = df.copy()
if selected_circle != "All": 
    filtered = filtered[filtered["Circle"] == selected_circle]
if selected_month != "All": 
    filtered = filtered[filtered["Month"] == selected_month]
if priority: 
    filtered = filtered[filtered["Priority(P0/P1)"].isin(priority)]
if selected_nominal: 
    filtered = filtered[filtered["Nominal Aop"].astype(str).isin(selected_nominal)]
if selected_remarks: 
    filtered = filtered[filtered["Final Remarks"].astype(str).isin(selected_remarks)]

# Status Logic
def get_status(r):
    if pd.notna(r.get("PRI OPEN DATE")): return "PRI Open"
    if pd.notna(r.get("HOP AT DATE")): return "AT Completed"
    if pd.notna(r.get("ACTUAL HOP RFAI OFFERED DATE")): return "RFAI Offered"
    if pd.notna(r.get("HOP MATERIAL DELIVERY DATE")): return "Material Delivered"
    if pd.notna(r.get("HOP MATERIAL DISPATCH DATE")): return "In-Transit"
    return "Planning"

filtered["Current Status"] = filtered.apply(get_status, axis=1)

# ───────────────────── SUMMARY PAGE ─────────────────────
if st.session_state.get("show_summary", False):
    st.title("MW DPR Milestone Summary Report")
    st.markdown(f"Generated: {datetime.now().strftime('%d %b %y • %H:%M')}")

    total_scope = len(filtered) if len(filtered) > 0 else 1
    rfa_i_offered = len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()])
    pri_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"])
    ccrfai_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "CCRFAI"])

    kpi_data = [
        ("Scope", len(filtered)), 
        ("LB", len(filtered[~filtered["PLAN ID"].isna()])),
        ("SR", len(filtered[~filtered["HOP SR Date"].isna()])), 
        ("RFAI", rfa_i_offered),
        ("Survey", len(filtered[~filtered["Survey Date"].isna()])), 
        ("PRI", pri_count),
        ("CRFAI", rfa_i_offered - pri_count),
        ("Media", len(filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["Media Date"].isna())])),
        ("CCRFAI", ccrfai_count), 
        ("MO", len(filtered[~filtered["HOP MO DATE"].isna()])),
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
    
    summary_df = pd.DataFrame([{"Milestone": l, "Count": v, "%": f"{v/total_scope*100:.2f}%"} for l, v in kpi_data])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download Summary CSV", summary_df.to_csv(index=False).encode(),
                           f"APTG_Summary.csv", "text/csv", use_container_width=True)
    with col2:
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state.show_summary = False
            st.rerun()
    st.stop()

# ───────────────────── MAIN DASHBOARD UI ─────────────────────
st.markdown("### MW DPR Milestone Progress")

total_scope = len(filtered) if len(filtered) > 0 else 1
rfa_i_offered = len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()])
pri_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"])
ccrfai_count = len(filtered[filtered["RFI Status"].astype(str).str.strip() == "CCRFAI"])

kpi_data = [
    ("Scope", len(filtered)), 
    ("LB", len(filtered[~filtered["PLAN ID"].isna()])),
    ("SR", len(filtered[~filtered["HOP SR Date"].isna()])), 
    ("RFAI", rfa_i_offered),
    ("Survey", len(filtered[~filtered["Survey Date"].isna()])), 
    ("PRI", pri_count),
    ("CRFAI", rfa_i_offered - pri_count),
    ("Media", len(filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["Media Date"].isna())])),
    ("CCRFAI", ccrfai_count), 
    ("MO", len(filtered[~filtered["HOP MO DATE"].isna()])),
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

# RESPONSIVE GRID (5 Columns)
rows = [kpi_data[i:i+5] for i in range(0, len(kpi_data), 5)]
for row in rows:
    cols = st.columns(5)
    for i, (label, value) in enumerate(row):
        with cols[i]:
            pct = f"{value/total_scope*100:.1f}%" if total_scope > 0 else "0.0%"
            accent = "#ef4444" if label in ["PRI", "CCRFAI"] else "#00d4ff"
            st.markdown(f"""
            <div class="kpi-box" style="border-left: 4px solid {accent};">
                <h3 class="kpi-value" style="color: {accent}">{value}</h3>
                <p class="kpi-label">{label}</p>
                <div class="kpi-pct">{pct}</div>
            </div>
            """, unsafe_allow_html=True)

if st.button("Open Full Summary Report", use_container_width=True, type="primary"):
    st.session_state.show_summary = True
    st.rerun()

st.markdown("---")

# ───────────────────── AGING ANALYSIS ─────────────────────
st.markdown("### Aging Analysis")
tab1, tab2, tab3, tab4 = st.tabs([
    "RFAI → MS1 (Integration)", 
    "MS1 → MS2 (HOP AT)", 
    "RFAI → MS2 (End-to-End)",
    "Aging Summary"
])

def calc_aging(df, date_col):
    if df.empty or date_col not in df.columns:
        return pd.Series([0] * len(df))
    dates = pd.to_datetime(df[date_col], errors='coerce')
    return (pd.Timestamp.now() - dates).dt.days

# Initialize variables for summary tab
ms1_pending = pd.DataFrame()
ms2_pending = pd.DataFrame()
end_to_end = pd.DataFrame()

# TAB 1: RFAI to MS1
with tab1:
    st.markdown("#### RFAI → MS1 (Integration) Aging")
    rfai_done = filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()].copy()
    ms1_done = rfai_done[~rfai_done["INTEGRATION DATE"].isna()].copy()
    ms1_pending = rfai_done[rfai_done["INTEGRATION DATE"].isna()].copy()

    if not ms1_pending.empty:
        ms1_pending["Aging Days"] = calc_aging(ms1_pending, "ACTUAL HOP RFAI OFFERED DATE")

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("RFAI Offered", len(rfai_done))
    with col2: st.metric("MS1 Completed", len(ms1_done))
    with col3: st.metric("MS1 Pending", len(ms1_pending))

    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t1c", use_container_width=True)
    show_pend = col2.button("Show Pending", key="t1p", use_container_width=True)

    if show_comp or not show_pend:
        st.markdown("##### Completed MS1")
        if not ms1_done.empty:
            ms1_done_disp = ms1_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "ACTUAL HOP RFAI OFFERED DATE", "INTEGRATION DATE", "CIRCLE_REMARK_1"]].copy()
            ms1_done_disp["Processing Days"] = calc_aging(ms1_done, "ACTUAL HOP RFAI OFFERED DATE")
            st.dataframe(format_date_cols(ms1_done_disp).sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        st.markdown("##### Pending MS1")
        if not ms1_pending.empty:
            pending_disp = ms1_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "ACTUAL HOP RFAI OFFERED DATE", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(format_date_cols(pending_disp).sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pending_disp["Aging Days"].value_counts().sort_index())

# TAB 2: MS1 to MS2
with tab2:
    st.markdown("#### MS1 → MS2 (HOP AT) Aging")
    ms1_done_t2 = filtered[~filtered["INTEGRATION DATE"].isna()].copy()
    ms2_done = ms1_done_t2[~ms1_done_t2["HOP AT DATE"].isna()].copy()
    ms2_pending = ms1_done_t2[ms1_done_t2["HOP AT DATE"].isna()].copy()

    if not ms2_pending.empty:
        ms2_pending["Aging Days"] = calc_aging(ms2_pending, "INTEGRATION DATE")

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("MS1 Done", len(ms1_done_t2))
    with col2: st.metric("MS2 Done", len(ms2_done))
    with col3: st.metric("MS2 Pending", len(ms2_pending))

    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t2c", use_container_width=True)
    show_pend = col2.button("Show Pending", key="t2p", use_container_width=True)

    if show_comp or not show_pend:
        st.markdown("##### Completed MS2")
        if not ms2_done.empty:
            ms2_done_disp = ms2_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "INTEGRATION DATE", "HOP AT DATE", "CIRCLE_REMARK_1"]].copy()
            ms2_done_disp["Processing Days"] = calc_aging(ms2_done, "INTEGRATION DATE")
            st.dataframe(format_date_cols(ms2_done_disp).sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        st.markdown("##### Pending MS2")
        if not ms2_pending.empty:
            pending_disp = ms2_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "INTEGRATION DATE", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(format_date_cols(pending_disp).sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)

# TAB 3: RFAI to End
with tab3:
    st.markdown("#### RFAI → MS2 (End-to-End) Aging")
    end_to_end = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()

    if not end_to_end.empty:
        end_to_end["Total Aging"] = calc_aging(end_to_end, "ACTUAL HOP RFAI OFFERED DATE")

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("RFAI Offered", len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()]))
    with col2: st.metric("HOP AT Done", len(filtered[~filtered["HOP AT DATE"].isna()]))
    with col3: st.metric("Pending", len(end_to_end))

    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t3c", use_container_width=True)
    show_pend = col2.button("Show Pending", key="t3p", use_container_width=True)

    if show_comp or not show_pend:
        completed = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["HOP AT DATE"].isna())]
        if not completed.empty:
            comp_disp = completed[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "ACTUAL HOP RFAI OFFERED DATE", "HOP AT DATE", "CIRCLE_REMARK_1"]].copy()
            comp_disp["Total Days"] = calc_aging(completed, "ACTUAL HOP RFAI OFFERED DATE")
            st.dataframe(format_date_cols(comp_disp).sort_values("Total Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        if not end_to_end.empty:
            pend_disp = end_to_end[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "ACTUAL HOP RFAI OFFERED DATE", "Total Aging", "CIRCLE_REMARK_1"]]
            st.dataframe(format_date_cols(pend_disp).sort_values("Total Aging", ascending=False), use_container_width=True, hide_index=True)

# TAB 4: Summary Stats
with tab4:
    st.markdown("#### Aging Summary Report")
    summary = {
        "Stage": ["RFAI → MS1", "MS1 → MS2", "RFAI → MS2"],
        "Pending": [len(ms1_pending), len(ms2_pending), len(end_to_end)],
        "Max Aging": [
            int(ms1_pending["Aging Days"].max()) if not ms1_pending.empty and "Aging Days" in ms1_pending.columns else 0,
            int(ms2_pending["Aging Days"].max()) if not ms2_pending.empty and "Aging Days" in ms2_pending.columns else 0,
            int(end_to_end["Total Aging"].max()) if not end_to_end.empty and "Total Aging" in end_to_end.columns else 0
        ],
        "Avg Aging": [
            f"{ms1_pending['Aging Days'].mean():.1f}" if not ms1_pending.empty and "Aging Days" in ms1_pending.columns else "0",
            f"{ms2_pending['Aging Days'].mean():.1f}" if not ms2_pending.empty and "Aging Days" in ms2_pending.columns else "0",
            f"{end_to_end['Total Aging'].mean():.1f}" if not end_to_end.empty and "Total Aging" in end_to_end.columns else "0"
        ]
    }
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
    st.download_button("Download Summary", pd.DataFrame(summary).to_csv(index=False).encode(),
                       f"APTG_MW_Aging_Summary_{datetime.now().strftime('%d%b%Y')}.csv", "text/csv", use_container_width=True)

# ───────────────────── FULL SEARCHABLE DATA ─────────────────────
st.markdown("---")
st.markdown("### Full Hop Data")
default_cols = [
    "Circle", "Month", "HOP A-B", "SITE ID A", "SITE ID B",
    "Priority(P0/P1)", "Current Status", "RFI Status", "CIRCLE_REMARK_1", "Final Remarks"
]
selected_cols = st.multiselect("Select columns", filtered.columns.tolist(), default=default_cols)

if selected_cols:
    display_df = format_date_cols(filtered[selected_cols])
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )

    st.download_button(
        "Download Data CSV",
        display_df.to_csv(index=False).encode(),
        f"APTG_Data.csv", "text/csv",
        use_container_width=True,
        type="primary"
    )

# ───────────────────── PENDING HOPS TRACKER ─────────────────────
st.markdown("---")
st.markdown("### Pending Hops")

def get_aging(df, start_col):
    if df.empty or start_col not in df.columns:
        return 0
    return (pd.Timestamp.now() - pd.to_datetime(df[start_col], errors='coerce')).dt.days

# 1. Survey Pending
survey_pend = filtered[
    (~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) &
    (~filtered["Media Date"].isna()) &
    (filtered["Survey Date"].isna())
].copy()

# 2. MO Pending
mo_pend = filtered[
    (~filtered["Survey Date"].isna()) &
    (filtered["HOP MO DATE"].isna()) &
    (filtered["RFI Status"].astype(str).str.strip().str.lower() != "pending")
].copy()

# 3. I&C Pending
ic_pend = filtered[
    (~filtered["HOP MATERIAL DELIVERY DATE"].isna()) &
    (filtered["HOP I&C DATE"].isna())
].copy()

# 4. MS1 Pending
ms1_pend = filtered[
    (~filtered["HOP I&C DATE"].isna()) &
    (filtered["Alignment Date"].isna())
].copy()

# 5. Phy AT Pending
phy_pend = filtered[
    (~filtered["HOP I&C DATE"].isna()) &
    (filtered["PHY-AT ACCEPTANCE DATE"].isna())
].copy()

# 6. Soft AT Pending
soft_pend = filtered[
    (~filtered["Alignment Date"].isna()) &
    (filtered["SOFT AT ACCEPTANCE DATE"].isna())
].copy()

# TABS LAYOUT
t1, t2, t3, t4, t5, t6 = st.tabs([
    f"Survey ({len(survey_pend)})",
    f"MO ({len(mo_pend)})",
    f"I&C ({len(ic_pend)})",
    f"MS1 ({len(ms1_pend)})",
    f"Phy AT ({len(phy_pend)})",
    f"Soft AT ({len(soft_pend)})"
])

def render_pending_tab(tab, df, name, aging_base_col):
    with tab:
        col_head, col_dl = st.columns([3, 1])
        with col_head:
            st.markdown(f"#### 📉 {name} Pending List")
        
        if not df.empty:
            # Calculate Aging
            df["Days Pending"] = get_aging(df, aging_base_col)
            
            # Select columns to display
            base_cols = ["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "CIRCLE_REMARK_1", aging_base_col, "Days Pending"]
            # Filter only columns that actually exist
            show_cols = [c for c in base_cols if c in df.columns]
            
            # Format Dates
            display_tab_df = format_date_cols(df[show_cols])
            
            # Display Table
            st.dataframe(
                display_tab_df.sort_values("Days Pending", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            with col_dl:
                st.download_button(
                    label="📥 Download CSV",
                    data=display_tab_df.to_csv(index=False).encode(),
                    file_name=f"{name.replace(' ', '_')}_Pending.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.success(f"✅ Great job! No hops pending in {name}.")

# Render Tabs
render_pending_tab(t1, survey_pend, "Survey", "ACTUAL HOP RFAI OFFERED DATE")
render_pending_tab(t2, mo_pend, "MO", "Survey Date")
render_pending_tab(t3, ic_pend, "I&C", "HOP MATERIAL DELIVERY DATE")
render_pending_tab(t4, ms1_pend, "MS1", "HOP I&C DATE")
render_pending_tab(t5, phy_pend, "Phy AT", "HOP I&C DATE")
render_pending_tab(t6, soft_pend, "Soft AT", "Alignment Date")

# ───────────────────── CHARTS ─────────────────────
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if "Current Status" in filtered.columns:
        fig = px.pie(filtered["Current Status"].value_counts().reset_index(), names="Current Status", values="count",
                     title="Current Status", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)
with col2:
    if "Circle" in filtered.columns:
        fig2 = px.bar(filtered["Circle"].value_counts().reset_index(), x="Circle", y="count", title="Hops by Circle")
        st.plotly_chart(fig2, use_container_width=True)

# ───────────────────── FOOTER ─────────────────────
st.markdown("---")
st.markdown(f"<p style='text-align:center; color:{sub_text};'>Last refreshed: {datetime.now().strftime('%d %b %y • %H:%M')}</p>", unsafe_allow_html=True)

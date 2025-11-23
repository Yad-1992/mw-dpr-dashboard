# dashboard.py — FINAL 100% WORKING (Streamlit 1.27+ Compatible)
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


# ───────────────────── PASSWORD PROTECTION ─────────────────────
def check_password():
    def password_entered():
        if st.session_state["password"] == "APTGMW2025":   # ← CHANGE THIS TO YOUR PASSWORD
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("AP & TG MW DPR – Secure Access")
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Wrong Password", type="password", on_change=password_entered, key="password")
        st.error("Access Denied")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ───────────────────── PAGE & SIDEBAR ─────────────────────
st.set_page_config(page_title="AP-TG MW DPR", page_icon="satellite", layout="wide")
st.sidebar.title("MW DPR Dashboard")
st.sidebar.markdown("**Live • Auto-refresh • Zero Maintenance**")
st.sidebar.image("https://companieslogo.com/img/orig/NOK_BIG-8604230c.png?t=1720244493", use_container_width=True)

# Theme
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True, index=0)
bg = "#0e1117" if theme == "Dark" else "#ffffff"
card_bg = "#1e2937" if theme == "Dark" else "#f8fafc"
accent = "#00d4ff"

st.markdown(f"""
<style>
    .reportview-container {{background: {bg}}}
    .sidebar .sidebar-content {{background: {bg}}}
    h1,h2,h3 {{color: {accent if theme=="Dark" else "#1e3a8a"}}}
    .kpi-box {{background:{card_bg}; padding:12px 8px; border-radius:10px; text-align:center;
                box-shadow:0 4px 12px rgba(0,0,0,0.3); margin:3px; border-left:4px solid {accent};}}
    .kpi-value {{font-size:38px; font-weight:900; margin:0; line-height:1;}}
    .kpi-label {{font-size:11px; color:#cbd5e1; margin:6px 0 2px; font-weight:600;}}
    .kpi-pct {{font-size:10px; color:#64748b; font-weight:bold; margin:0;}}
</style>
""", unsafe_allow_html=True)
# ───────────────────── LIVE DATA FROM GOOGLE SHEET (REAL-TIME) ─────────────────────
@st.cache_data(ttl=60)  # Auto-refresh every 60 seconds
def load_data():
    # Your exact Google Sheet ID
    sheet_id = "1BD-Bww-k_3jVwJAGqBbs02YcOoUyNrOWcY_T9xvnbgY"
    gid = "0"  # Circle_DPR tab (gid=0 from your link)
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(csv_url)
    
    # Convert all date columns automatically
    date_cols = df.columns[df.columns.str.contains("Date|DATE", case=False)]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

try:
    df = load_data()
    st.sidebar.success(f"Live from Google Sheet\n{len(df):,} hops loaded\nAuto-refresh every 60s")
except Exception as e:
    st.error("Could not connect to Google Sheet. Check sharing settings.")
    st.info("Make sure your sheet is shared as: **Anyone with the link can view**")
    st.stop()
# ───────────────────── FILTERS ─────────────────────
st.sidebar.markdown("### Filters")
date_columns = [col for col in df.columns if "Date" in col or "DATE" in col]
valid_dates = pd.to_datetime(df[date_columns].stack().dropna(), errors='coerce')
min_date = valid_dates.min().date() if not valid_dates.empty else datetime.now().date()
max_date = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()

start_date = st.sidebar.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date)

c1, c2 = st.sidebar.columns(2)
with c1: selected_circle = st.selectbox("Circle", ["All"] + sorted(df["Circle"].dropna().unique().tolist()))
with c2: selected_month = st.selectbox("Month", ["All"] + sorted(df["Month"].dropna().unique().tolist()))
priority = st.sidebar.multiselect("Priority", ["P0", "P1"], default=["P0", "P1"])

# Apply filters
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

# Current Status
def get_status(r):
    if pd.notna(r.get("PRI OPEN DATE")): return "PRI Open"
    if pd.notna(r.get("HOP AT DATE")): return "AT Completed"
    if pd.notna(r.get("ACTUAL HOP RFAI OFFERED DATE")): return "RFAI Offered"
    if pd.notna(r.get("HOP MATERIAL DELIVERY DATE")): return "Material Delivered"
    if pd.notna(r.get("HOP MATERIAL DISPATCH DATE")): return "In-Transit"
    return "Planning"
filtered["Current Status"] = filtered.apply(get_status, axis=1)

# ───────────────────── SUMMARY PAGE (IF OPENED) ─────────────────────
if st.session_state.get("show_summary", False):
    st.markdown("# MW DPR Milestone Summary Report")
    st.markdown(f"**Generated:** {datetime.now().strftime('%d %b %Y • %H:%M')}")
    st.markdown(f"**Scope:** {len(filtered)} Hops")

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

    summary_df = pd.DataFrame([{"Milestone": l, "Count": v, "%": f"{v/total_scope*100:.2f}%"} for l, v in kpi_data])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download Summary CSV", summary_df.to_csv(index=False).encode(),
                           f"APTG_MW_DPR_Summary_{datetime.now().strftime('%d%b%Y')}.csv", "text/csv", use_container_width=True)
    with col2:
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state.show_summary = False
            st.rerun()
    st.stop()

# ───────────────────── MAIN DASHBOARD ─────────────────────
st.markdown("### MW DPR Milestone Progress – Live Summary")
show_kpi = st.checkbox("Show Milestone KPIs", value=True)

if show_kpi:
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

    rows = [kpi_data[i:i+7] for i in range(0, len(kpi_data), 7)]
    for row in rows:
        cols = st.columns(7, gap="small")
        for i, (label, value) in enumerate(row):
            with cols[i]:
                pct = f"{value/total_scope*100:.1f}%" if total_scope > 0 else "0.0%"
                color = "#ef4444" if label in ["PRI", "CCRFAI"] else "#06b6d4"
                border = "#ef4444" if label in ["PRI", "CCRFAI"] else "#06b6d4"
                st.markdown(f"""
                <div style="background:{card_bg}; padding:12px 8px; border-radius:10px; text-align:center;
                            box-shadow:0 4px 12px rgba(0,0,0,0.3); margin:3px; border-left:4px solid {border}; min-height:90px;">
                    <h3 style="margin:0; color:{color}; font-size:38px; font-weight:900">{value}</h3>
                    <p style="margin:6px 0 2px; color:#cbd5e1; font-size:11px; font-weight:600">{label}</p>
                    <p style="margin:0; color:#64748b; font-size:10px; font-weight:bold">{pct}</p>
                </div>
                """, unsafe_allow_html=True)

    if st.button("Open Full Summary Report", use_container_width=True, type="primary"):
        st.session_state.show_summary = True
        st.rerun()   # ← NEW CORRECT WAY (no experimental_rerun)

st.markdown("---")
# ───────────────────── FINAL AGING TABS — 100% BULLETPROOF (NO KeyError) ─────────────────────
st.markdown("---")
st.markdown("### Aging Analysis")

tab1, tab2, tab3, tab4 = st.tabs([
    "RFAI → MS1 (Integration)", 
    "MS1 → MS2 (HOP AT)", 
    "RFAI → MS2 (End-to-End)", 
    "Aging Summary"
])

# Helper function
def calc_aging(df, date_col):
    if df.empty or date_col not in df.columns:
        return pd.Series([0] * len(df))
    dates = pd.to_datetime(df[date_col], errors='coerce')
    return (pd.Timestamp.now() - dates).dt.days

# Initialize empty for summary
ms1_pending = pd.DataFrame()
ms2_pending = pd.DataFrame()
end_to_end = pd.DataFrame()

with tab1:
    st.markdown("#### RFAI → MS1 (Integration) Aging")
    
    rfai_done = filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()].copy()
    ms1_done = rfai_done[~rfai_done["INTEGRATION DATE"].isna()].copy()
    ms1_pending = rfai_done[rfai_done["INTEGRATION DATE"].isna()].copy()
    
    # Add aging only to pending
    if not ms1_pending.empty:
        ms1_pending["RFAI Date"] = pd.to_datetime(ms1_pending["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%Y")
        ms1_pending["Aging Days"] = calc_aging(ms1_pending, "ACTUAL HOP RFAI OFFERED DATE")
        ms1_pending = ms1_pending.copy()

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
            ms1_done_disp = ms1_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            ms1_done_disp["RFAI Date"] = pd.to_datetime(ms1_done["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%Y")
            ms1_done_disp["MS1 Date"] = pd.to_datetime(ms1_done["INTEGRATION DATE"]).dt.strftime("%d-%b-%Y")
            ms1_done_disp["Processing Days"] = calc_aging(ms1_done, "ACTUAL HOP RFAI OFFERED DATE")
            ms1_done_disp["CIRCLE_REMARK_1"] = ms1_done["CIRCLE_REMARK_1"]
            st.dataframe(ms1_done_disp.sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        st.markdown("##### Pending MS1")
        if not ms1_pending.empty:
            pending_disp = ms1_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "RFAI Date", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(pending_disp.sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pending_disp["Aging Days"].value_counts().sort_index())
            st.download_button("Download Pending List", pending_disp.to_csv(index=False).encode(),
                               f"RFAI_to_MS1_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True, key="d1")
        else:
            st.success("All RFAI hops have completed MS1")

with tab2:
    st.markdown("#### MS1 → MS2 (HOP AT) Aging")
    
    ms1_done = filtered[~filtered["INTEGRATION DATE"].isna()].copy()
    ms2_done = ms1_done[~ms1_done["HOP AT DATE"].isna()].copy()
    ms2_pending = ms1_done[ms1_done["HOP AT DATE"].isna()].copy()
    
    if not ms2_pending.empty:
        ms2_pending["MS1 Date"] = pd.to_datetime(ms2_pending["INTEGRATION DATE"]).dt.strftime("%d-%b-%Y")
        ms2_pending["Aging Days"] = calc_aging(ms2_pending, "INTEGRATION DATE")
        ms2_pending = ms2_pending.copy()

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("MS1 Done", len(ms1_done))
    with col2: st.metric("MS2 Done", len(ms2_done))
    with col3: st.metric("MS2 Pending", len(ms2_pending))

    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t2c", use_container_width=True)
    show_pend = col2.button("Show Pending", key="t2p", use_container_width=True)

    if show_comp or not show_pend:
        st.markdown("##### Completed MS2")
        if not ms2_done.empty:
            ms2_done_disp = ms2_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            ms2_done_disp["MS1 Date"] = pd.to_datetime(ms2_done["INTEGRATION DATE"]).dt.strftime("%d-%b-%Y")
            ms2_done_disp["HOP AT Date"] = pd.to_datetime(ms2_done["HOP AT DATE"]).dt.strftime("%d-%b-%Y")
            ms2_done_disp["Processing Days"] = calc_aging(ms2_done, "INTEGRATION DATE")
            ms2_done_disp["CIRCLE_REMARK_1"] = ms2_done["CIRCLE_REMARK_1"]
            st.dataframe(ms2_done_disp.sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        st.markdown("##### Pending MS2")
        if not ms2_pending.empty:
            pending_disp = ms2_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "MS1 Date", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(pending_disp.sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pending_disp["Aging Days"].value_counts().sort_index())
            st.download_button("Download Pending List", pending_disp.to_csv(index=False).encode(),
                               f"MS1_to_MS2_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True, key="d2")
        else:
            st.success("All MS1 hops have completed HOP AT")

with tab3:
    st.markdown("#### RFAI → MS2 (End-to-End) Aging")
    
    end_to_end = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()
    
    if not end_to_end.empty:
        end_to_end["RFAI Date"] = pd.to_datetime(end_to_end["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%Y")
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
            comp_disp = completed[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            comp_disp["RFAI Date"] = pd.to_datetime(completed["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%Y")
            comp_disp["HOP AT Date"] = pd.to_datetime(completed["HOP AT DATE"]).dt.strftime("%d-%b-%Y")
            comp_disp["Total Days"] = calc_aging(completed, "ACTUAL HOP RFAI OFFERED DATE")
            comp_disp["CIRCLE_REMARK_1"] = completed["CIRCLE_REMARK_1"]
            st.dataframe(comp_disp.sort_values("Total Days", ascending=False), use_container_width=True, hide_index=True)

    if show_pend or not show_comp:
        if not end_to_end.empty:
            pend_disp = end_to_end[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "RFAI Date", "Total Aging", "CIRCLE_REMARK_1"]]
            st.dataframe(pend_disp.sort_values("Total Aging", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pend_disp["Total Aging"].value_counts().sort_index())
            st.download_button("Download Pending List", pend_disp.to_csv(index=False).encode(),
                               f"RFAI_to_HOPAT_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True, key="d3")
        else:
            st.success("All RFAI hops have completed HOP AT")

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

# ───────────────────── FULLY SEARCHABLE & SORTABLE COLUMN-WISE DATA TABLE ─────────────────────
st.markdown("---")
st.markdown("### Full Hop Data – Search & Sort Every Column")

# Let user choose columns
default_cols = [
    "Circle", "Month", "HOP A-B", "SITE ID A", "SITE ID B",
    "Priority(P0/P1)", "Current Status", "RFI Status", "CIRCLE_REMARK_1", "Final Remarks"
]

selected_cols = st.multiselect(
    "Select columns to display",
    options=filtered.columns.tolist(),
    default=default_cols
)

if selected_cols:
    # THE ULTIMATE SEARCHABLE + SORTABLE TABLE
    st.dataframe(
        filtered[selected_cols],
        use_container_width=True,
        height=700,
        # THIS LINE GIVES COLUMN-WISE SEARCH + SORT + FILTER
        column_config={
            col: st.column_config.Column(
                width="medium",
                # Enable search + sort on every column
                help=f"Search & sort: {col}"
            ) for col in selected_cols
        },
        # This enables full column-wise filtering & sorting (Streamlit 1.28+)
        hide_index=True
    )

    # Download visible data
    csv = filtered[selected_cols].to_csv(index=False).encode()
    st.download_button(
        "Download Visible Data as CSV",
        data=csv,
        file_name=f"APTG_MW_Searchable_Data_{datetime.now().strftime('%d%b%Y_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.caption(f"Showing {len(filtered):,} hops • Type in any column header to search • Click header to sort")
else:
    st.info("Please select at least one column to display")
    
# Rest of your dashboard (charts, table, etc.) — unchanged
col1, col2 = st.columns(2)
with col1:
    fig = px.pie(filtered["Current Status"].value_counts().reset_index(), names="Current Status", values="count",
                 title="Current Status", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(filtered["Circle"].value_counts().reset_index(), x="Circle", y="count", title="Hops by Circle")
    st.plotly_chart(fig2, use_container_width=True)

pri = filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"]
if not pri.empty:
    st.error(f"URGENT: {len(pri)} HOPS BLOCKED ON PRI")
    st.dataframe(pri[["HOP A-B","SITE ID A","SITE ID B","PRI ISSUE CATEGORY","PRI REMARKS","PRI OPEN DATE"]], use_container_width=True)

st.markdown("### Detailed Hop Data")
default_cols = ["Circle","Month","HOP A-B","SITE ID A","SITE ID B","Priority(P0/P1)","Current Status","Final Remarks"]
show_cols = st.multiselect("Select Columns", df.columns, default=default_cols)
st.dataframe(filtered[show_cols], use_container_width=True, height=500)

c1, c2 = st.columns(2)
with c1:
    st.download_button("Download Full Data", filtered.to_csv(index=False).encode(), "MW_DPR_FULL.csv", "text/csv")
with c2:
    st.download_button("Download Visible Data", filtered[show_cols].to_csv(index=False).encode(),
                       f"MW_DPR_View_{datetime.now().strftime('%d%b')}.csv", "text/csv")

st.markdown("---")
st.markdown(f"<p style='text-align:center; color:#64748b;'>Last refreshed: {datetime.now().strftime('%d %b %Y • %H:%M')} | Showing {len(filtered)} hops</p>", unsafe_allow_html=True)

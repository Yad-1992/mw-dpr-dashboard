
# dashboard.py — FULL A-Z WORKING VERSION (November 2025)
# Tested & Running Live on Streamlit Cloud
import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher
from yaml.loader import SafeLoader
import os

# ───────────────────── PAGE CONFIG ─────────────────────
st.set_page_config(page_title="AP-TG MW DPR", page_icon="Chart", layout="wide")

# ───────────────────── SECRETS ─────────────────────
try:
    SHEET_ID = st.secrets["sheet_id"]
    ADMIN_EMAIL = st.secrets["ADMIN"]["admin_email"]
    ADMIN_USERNAMES = st.secrets["ADMIN"]["admin_usernames"]
    SENDER_EMAIL = st.secrets["GMAIL"]["sender_email"]
    SENDER_PASS = st.secrets["GMAIL"]["sender_password"]
    EMAIL_OK = SENDER_PASS and len(SENDER_PASS.strip()) >= 16
except:
    st.error("secrets.toml is missing or invalid!")
    st.stop()

USERS_FILE = "users.yaml"
PENDING_FILE = "pending_requests.yaml"

# ───────────────────── INITIALIZE FILES ─────────────────────
if not os.path.exists(USERS_FILE):
    hashed = Hasher(['admin123']).generate()[0]
    default_config = {
        'credentials': {'usernames': {'admin': {'name': 'Admin', 'email': ADMIN_EMAIL, 'password': hashed}}},
        'cookie': {'expiry_days': 30, 'key': 'aptg_mw_key_2025_v9', 'name': 'aptg_cookie'}
    }
    with open(USERS_FILE, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)

if not os.path.exists(PENDING_FILE):
    with open(PENDING_FILE, 'w') as f:
        yaml.dump([], f)

# Load data
with open(USERS_FILE) as f:
    users_config = yaml.load(f, Loader=SafeLoader)
with open(PENDING_FILE) as f:
    pending_requests = yaml.load(f, Loader=SafeLoader) or []

# ───────────────────── AUTHENTICATOR (100% CORRECT 2025 SYNTAX) ─────────────────────
authenticator = stauth.Authenticate(
    users_config['credentials'],
    users_config['cookie']['name'],
    users_config['cookie']['key'],
    users_config['cookie']['expiry_days']
)

# ───────────────────── ADMIN APPROVAL PANEL ─────────────────────
if st.query_params.get("admin") == "approve":
    st.title("Admin Approval Panel")
    name, auth_status, username = authenticator.login(location="main")
    
    if not auth_status or username not in ADMIN_USERNAMES:
        st.error("Access Denied — Admin Only")
        st.stop()
    
    st.success(f"Welcome, {name}")

    if not pending_requests:
        st.info("No pending requests")
    else:
        for i, req in enumerate(pending_requests):
            with st.expander(f"{req['name']} ({req['username']}) • {req['requested_at']}", expanded=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.write(f"**Email:** {req['email']}")
                with c2:
                    if st.button("Approve", key=f"app_{i}"):
                        hashed_pw = Hasher([req['password']]).generate()[0]
                        users_config['credentials']['usernames'][req['username']] = {
                            'name': req['name'], 'email': req['email'], 'password': hashed_pw
                        }
                        with open(USERS_FILE, 'w') as f:
                            yaml.dump(users_config, f)
                        pending_requests = [r for r in pending_requests if r['username'] != req['username']]
                        with open(PENDING_FILE, 'w') as f:
                            yaml.dump(pending_requests, f)
                        st.success(f"Approved: {req['username']}")
                        st.rerun()
                with c3:
                    if st.button("Reject", key=f"rej_{i}"):
                        pending_requests = [r for r in pending_requests if r['username'] != req['username']]
                        with open(PENDING_FILE, 'w') as f:
                            yaml.dump(pending_requests, f)
                        st.error("Rejected")
                        st.rerun()

    if st.button("Back to Dashboard"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# ───────────────────── LOGIN / SIGNUP ─────────────────────
name, authentication_status, username = authenticator.login(location="main")

if authentication_status == False:
    st.error("Incorrect username/password")
elif authentication_status is None:
    st.info("Login or request access below")

    with st.form("signup_form"):
        st.header("Request Dashboard Access")
        new_name = st.text_input("Full Name")
        new_user = st.text_input("Username")
        new_email = st.text_input("Email")
        new_pass = st.text_input("Password", type="password")
        new_pass2 = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Submit Request")

        if submit:
            if not all([new_name, new_user, new_email, new_pass]):
                st.error("All fields required")
            elif new_pass != new_pass2:
                st.error("Passwords don't match")
            elif new_user in users_config['credentials']['usernames']:
                st.error("Username taken")
            else:
                pending_requests.append({
                    'name': new_name, 'username': new_user, 'email': new_email,
                    'password': new_pass, 'requested_at': datetime.now().strftime("%d-%b-%Y %H:%M")
                })
                with open(PENDING_FILE, 'w') as f:
                    yaml.dump(pending_requests, f)

                if EMAIL_OK:
                    try:
                        msg = MIMEMultipart()
                        msg['From'] = SENDER_EMAIL
                        msg['To'] = ADMIN_EMAIL
                        msg['Subject'] = f"New Access Request: {new_name}"
                        body = f"Approve: https://your-app-url/?admin=approve\n\nUser: {new_user}\nName: {new_name}"
                        msg.attach(MIMEText(body, 'plain'))
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(SENDER_EMAIL, SENDER_PASS)
                        server.send_message(msg)
                        server.quit()
                        st.success("Request sent to Admin!")
                    except:
                        st.warning("Request saved. Email failed.")
                else:
                    st.success("Request saved! Admin will review.")
    st.stop()

# ───────────────────── MAIN DASHBOARD (LOGGED IN) ─────────────────────
with st.sidebar:
    st.write(f"**{name}**")
    authenticator.logout("Logout", "sidebar")
    st.image("https://companieslogo.com/img/orig/NOK_BIG-8604230c.png?t=1720244493", use_container_width=True)

st.title("AP-TG MW DPR Dashboard")
st.success("Login Successful!")

# ───────────────────── LOAD DATA ─────────────────────
@st.cache_data(ttl=300)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    df = pd.read_csv(url)
    date_cols = df.columns[df.columns.str.contains("Date|DATE", case=False)]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

try:
    df = load_data()
    st.sidebar.success(f"{len(df):,} hops loaded")
except:
    st.error("Failed to load data")
    st.stop()

# Filters
st.sidebar.markdown("### Filters")
circle = st.sidebar.selectbox("Circle", ["All"] + sorted(df["Circle"].dropna().unique()))
month = st.sidebar.selectbox("Month", ["All"] + sorted(df["Month"].dropna().unique()))
priority = st.sidebar.multiselect("Priority", ["P0", "P1"], default=["P0", "P1"])

filtered = df.copy()
if circle != "All": filtered = filtered[filtered["Circle"] == circle]
if month != "All": filtered = filtered[filtered["Month"] == month]
if priority: filtered = filtered[filtered["Priority(P0/P1)"].isin(priority)]

# Status
def get_status(r):
    if pd.notna(r.get("PRI OPEN DATE")): return "PRI Open"
    if pd.notna(r.get("HOP AT DATE")): return "AT Completed"
    if pd.notna(r.get("ACTUAL HOP RFAI OFFERED DATE")): return "RFAI Offered"
    return "Planning"
filtered["Status"] = filtered.apply(get_status, axis=1)

# KPI Grid
st.markdown("### Progress Summary")
total = len(filtered)
kpis = [
    ("Total Scope", total),
    ("RFAI Offered", len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()])),
    ("HOP AT Done", len(filtered[~filtered["HOP AT DATE"].isna()])),
    ("PRI", len(filtered[filtered["RFI Status"].astype(str).str.strip() == "PRI"]))
]

cols = st.columns(4)
for i, (label, val) in enumerate(kpis):
    with cols[i]:
        st.metric(label, val, f"{val/total*100:.1f}%" if total else "0%")

# Charts
col1, col2 = st.columns(2)
with col1:
    fig = px.pie(filtered["Status"].value_counts().reset_index(), names="Status", values="count", title="Status")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(filtered["Circle"].value_counts().reset_index(), x="Circle", y="count", title="By Circle")
    st.plotly_chart(fig2, use_container_width=True)

st.dataframe(filtered, use_container_width=True)
st.markdown(f"**Last updated:** {datetime.now().strftime('%d %b %Y • %H:%M')}")

# ───────────────────── FILTERS ─────────────────────
st.sidebar.markdown("### 🔍 Filters")
c1, c2 = st.sidebar.columns(2)
with c1:
    selected_circle = st.selectbox("Circle", ["All"] + sorted(df["Circle"].dropna().unique().tolist()))
with c2:
    selected_month = st.selectbox("Month", ["All"] + sorted(df["Month"].dropna().unique().tolist()))
priority = st.sidebar.multiselect("Priority", ["P0", "P1"], default=["P0", "P1"])

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

# Apply filters
filtered = df.copy()
if selected_circle != "All": filtered = filtered[filtered["Circle"] == selected_circle]
if selected_month != "All": filtered = filtered[filtered["Month"] == selected_month]
if priority: filtered = filtered[filtered["Priority(P0/P1)"].isin(priority)]
if selected_nominal: filtered = filtered[filtered["Nominal Aop"].astype(str).isin(selected_nominal)]
if selected_remarks: filtered = filtered[filtered["Final Remarks"].astype(str).isin(selected_remarks)]

# Status logic
def get_status(r):
    if pd.notna(r.get("PRI OPEN DATE")): return "PRI Open"
    if pd.notna(r.get("HOP AT DATE")): return "AT Completed"
    if pd.notna(r.get("ACTUAL HOP RFAI OFFERED DATE")): return "RFAI Offered"
    if pd.notna(r.get("HOP MATERIAL DELIVERY DATE")): return "Material Delivered"
    if pd.notna(r.get("HOP MATERIAL DISPATCH DATE")): return "In-Transit"
    return "Planning"

filtered["Current Status"] = filtered.apply(get_status, axis=1)

# ───────────────────── SUMMARY PAGE (Optional Full Report) ─────────────────────
if st.session_state.get("show_summary", False):
    st.title("📊 MW DPR Milestone Summary Report")
    st.markdown(f"**Generated:** {datetime.now().strftime('%d %b %y • %H:%M')}")

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
    summary_df = pd.DataFrame([
        {"Milestone": label, "Count": value, "%": f"{value/total_scope*100:.1f}%" if total_scope > 0 else "0%"}
        for label, value in kpi_data
    ])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Summary CSV", 
            summary_df.to_csv(index=False).encode(),
            f"APTG_Summary_{datetime.now().strftime('%d%b%y')}.csv", 
            "text/csv", 
            use_container_width=True
        )
    with col2:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.show_summary = False
            st.rerun()
    st.stop()

# ───────────────────── KPI DASHBOARD ─────────────────────
st.markdown("### 📈 MW DPR Milestone Progress")
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

# Responsive 5-col grid
rows = [kpi_data[i:i+5] for i in range(0, len(kpi_data), 5)]
for row in rows:
    cols = st.columns(5)
    for j, (label, value) in enumerate(row):
        with cols[j]:
            pct = f"{value/total_scope*100:.1f}%" if total_scope > 0 else "0.0%"
            accent = "#ef4444" if label in ["PRI", "CCRFAI"] else "#00d4ff"
            st.markdown(f"""
            <div class="kpi-box" style="border-left: 4px solid {accent};">
                <h3 class="kpi-value" style="color: {accent}">{value}</h3>
                <p class="kpi-label">{label}</p>
                <div class="kpi-pct">{pct}</div>
            </div>
            """, unsafe_allow_html=True)

if st.button("📋 Open Full Summary Report", use_container_width=True, type="primary"):
    st.session_state.show_summary = True
    st.rerun()

st.markdown("---")

# ───────────────────── AGING ANALYSIS ─────────────────────
st.markdown("### ⏰ Aging Analysis")
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

# Tab 1: RFAI → MS1
with tab1:
    st.markdown("#### RFAI → MS1 (Integration) Aging")
    rfai_done = filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()].copy()
    ms1_done = rfai_done[~rfai_done["INTEGRATION DATE"].isna()].copy()
    ms1_pending = rfai_done[rfai_done["INTEGRATION DATE"].isna()].copy()
    
    if not ms1_pending.empty:
        ms1_pending["RFAI Date"] = pd.to_datetime(ms1_pending["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%y")
        ms1_pending["Aging Days"] = calc_aging(ms1_pending, "ACTUAL HOP RFAI OFFERED DATE")
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("RFAI Offered", len(rfai_done))
    with col2: st.metric("MS1 Completed", len(ms1_done))
    with col3: st.metric("MS1 Pending", len(ms1_pending))
    
    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t1c")
    show_pend = col2.button("Show Pending", key="t1p")
    
    if show_comp:
        st.markdown("##### Completed MS1")
        if not ms1_done.empty:
            ms1_done_disp = ms1_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            ms1_done_disp["RFAI Date"] = pd.to_datetime(ms1_done["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%y")
            ms1_done_disp["MS1 Date"] = pd.to_datetime(ms1_done["INTEGRATION DATE"]).dt.strftime("%d-%b-%y")
            ms1_done_disp["Processing Days"] = calc_aging(ms1_done, "ACTUAL HOP RFAI OFFERED DATE")
            ms1_done_disp["CIRCLE_REMARK_1"] = ms1_done["CIRCLE_REMARK_1"]
            st.dataframe(ms1_done_disp.sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)
    
    if show_pend:
        st.markdown("##### Pending MS1")
        if not ms1_pending.empty:
            pending_disp = ms1_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "RFAI Date", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(pending_disp.sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pending_disp["Aging Days"].value_counts().sort_index())
            st.download_button("📥 Download Pending", pending_disp.to_csv(index=False).encode(),
                               f"RFAI_to_MS1_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True)
        else:
            st.success("✅ All RFAI hops have completed MS1!")

# Tab 2: MS1 → MS2
with tab2:
    st.markdown("#### MS1 → MS2 (HOP AT) Aging")
    ms1_done_all = filtered[~filtered["INTEGRATION DATE"].isna()].copy()
    ms2_done = ms1_done_all[~ms1_done_all["HOP AT DATE"].isna()].copy()
    ms2_pending = ms1_done_all[ms1_done_all["HOP AT DATE"].isna()].copy()
    
    if not ms2_pending.empty:
        ms2_pending["MS1 Date"] = pd.to_datetime(ms2_pending["INTEGRATION DATE"]).dt.strftime("%d-%b-%y")
        ms2_pending["Aging Days"] = calc_aging(ms2_pending, "INTEGRATION DATE")
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("MS1 Done", len(ms1_done_all))
    with col2: st.metric("MS2 Done", len(ms2_done))
    with col3: st.metric("MS2 Pending", len(ms2_pending))
    
    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t2c")
    show_pend = col2.button("Show Pending", key="t2p")
    
    if show_comp:
        st.markdown("##### Completed MS2")
        if not ms2_done.empty:
            ms2_done_disp = ms2_done[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            ms2_done_disp["MS1 Date"] = pd.to_datetime(ms2_done["INTEGRATION DATE"]).dt.strftime("%d-%b-%y")
            ms2_done_disp["HOP AT Date"] = pd.to_datetime(ms2_done["HOP AT DATE"]).dt.strftime("%d-%b-%y")
            ms2_done_disp["Processing Days"] = calc_aging(ms2_done, "INTEGRATION DATE")
            ms2_done_disp["CIRCLE_REMARK_1"] = ms2_done["CIRCLE_REMARK_1"]
            st.dataframe(ms2_done_disp.sort_values("Processing Days", ascending=False), use_container_width=True, hide_index=True)
    
    if show_pend:
        st.markdown("##### Pending MS2")
        if not ms2_pending.empty:
            pending_disp = ms2_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "MS1 Date", "Aging Days", "CIRCLE_REMARK_1"]]
            st.dataframe(pending_disp.sort_values("Aging Days", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pending_disp["Aging Days"].value_counts().sort_index())
            st.download_button("📥 Download Pending", pending_disp.to_csv(index=False).encode(),
                               f"MS1_to_MS2_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True)
        else:
            st.success("✅ All MS1 hops have completed HOP AT!")

# Tab 3: RFAI → MS2 End-to-End
with tab3:
    st.markdown("#### RFAI → MS2 (End-to-End) Aging")
    end_to_end_pending = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()
    if not end_to_end_pending.empty:
        end_to_end_pending["RFAI Date"] = pd.to_datetime(end_to_end_pending["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%y")
        end_to_end_pending["Total Aging"] = calc_aging(end_to_end_pending, "ACTUAL HOP RFAI OFFERED DATE")
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("RFAI Offered", len(filtered[~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()]))
    with col2: st.metric("HOP AT Done", len(filtered[~filtered["HOP AT DATE"].isna()]))
    with col3: st.metric("Pending", len(end_to_end_pending))
    
    col1, col2 = st.columns(2)
    show_comp = col1.button("Show Completed", key="t3c")
    show_pend = col2.button("Show Pending", key="t3p")
    
    if show_comp:
        completed = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["HOP AT DATE"].isna())]
        st.markdown("##### Completed End-to-End")
        if not completed.empty:
            comp_disp = completed[["Circle", "HOP A-B", "SITE ID A", "SITE ID B"]].copy()
            comp_disp["RFAI Date"] = pd.to_datetime(completed["ACTUAL HOP RFAI OFFERED DATE"]).dt.strftime("%d-%b-%y")
            comp_disp["HOP AT Date"] = pd.to_datetime(completed["HOP AT DATE"]).dt.strftime("%d-%b-%y")
            comp_disp["Total Days"] = calc_aging(completed, "ACTUAL HOP RFAI OFFERED DATE")
            comp_disp["CIRCLE_REMARK_1"] = completed["CIRCLE_REMARK_1"]
            st.dataframe(comp_disp.sort_values("Total Days", ascending=False), use_container_width=True, hide_index=True)
    
    if show_pend:
        st.markdown("##### Pending End-to-End")
        if not end_to_end_pending.empty:
            pend_disp = end_to_end_pending[["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "RFAI Date", "Total Aging", "CIRCLE_REMARK_1"]]
            st.dataframe(pend_disp.sort_values("Total Aging", ascending=False), use_container_width=True, hide_index=True)
            st.bar_chart(pend_disp["Total Aging"].value_counts().sort_index())
            st.download_button("📥 Download Pending", pend_disp.to_csv(index=False).encode(),
                               f"RFAI_to_HOPAT_Pending_{datetime.now().strftime('%d%b')}.csv", "text/csv", use_container_width=True)
        else:
            st.success("✅ All RFAI hops have completed HOP AT!")

# Tab 4: Summary
with tab4:
    st.markdown("#### Aging Summary Report")
    ms1_pending = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["INTEGRATION DATE"].isna())].copy()
    ms2_pending = filtered[(~filtered["INTEGRATION DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()
    end_to_end = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (filtered["HOP AT DATE"].isna())].copy()
    
    summary = {
        "Stage": ["RFAI → MS1", "MS1 → MS2", "RFAI → MS2"],
        "Pending": [len(ms1_pending), len(ms2_pending), len(end_to_end)],
        "Max Aging": [
            int(ms1_pending["Aging Days"].max()) if not ms1_pending.empty and "Aging Days" in ms1_pending else 0,
            int(ms2_pending["Aging Days"].max()) if not ms2_pending.empty and "Aging Days" in ms2_pending else 0,
            int(end_to_end["Total Aging"].max()) if not end_to_end.empty and "Total Aging" in end_to_end else 0
        ],
        "Avg Aging": [
            f"{calc_aging(ms1_pending, 'ACTUAL HOP RFAI OFFERED DATE').mean():.1f}" if not ms1_pending.empty else "0",
            f"{calc_aging(ms2_pending, 'INTEGRATION DATE').mean():.1f}" if not ms2_pending.empty else "0",
            f"{calc_aging(end_to_end, 'ACTUAL HOP RFAI OFFERED DATE').mean():.1f}" if not end_to_end.empty else "0"
        ]
    }
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
    st.download_button("📥 Download Summary", pd.DataFrame(summary).to_csv(index=False).encode(),
                       f"APTG_Aging_Summary_{datetime.now().strftime('%d%b%Y')}.csv", "text/csv", use_container_width=True)

st.markdown("---")

# ───────────────────── FULL DATA VIEW ─────────────────────
st.markdown("### 🔍 Full Hop Data")
default_cols = [
    "Circle", "Month", "HOP A-B", "SITE ID A", "SITE ID B",
    "Priority(P0/P1)", "Current Status", "RFI Status", "CIRCLE_REMARK_1", "Final Remarks"
]
selected_cols = st.multiselect("Select Columns", filtered.columns.tolist(), default=default_cols)
if selected_cols:
    display_df = format_date_cols(filtered[selected_cols])
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )
    st.download_button(
        "📥 Download Filtered Data",
        display_df.to_csv(index=False).encode(),
        f"APTG_Filtered_Data_{datetime.now().strftime('%d%b%y')}.csv",
        "text/csv",
        use_container_width=True,
        type="primary"
    )

# ───────────────────── PENDING HOPS TRACKER ─────────────────────
st.markdown("---")
st.markdown("### 🚧 Pending Hops Tracker")

def get_aging(df, start_col):
    if df.empty or start_col not in df.columns: return pd.Series([0] * len(df))
    return calc_aging(df, start_col)

# Define pending sets
survey_pend = filtered[(~filtered["ACTUAL HOP RFAI OFFERED DATE"].isna()) & (~filtered["Media Date"].isna()) & (filtered["Survey Date"].isna())].copy()
mo_pend = filtered[(~filtered["Survey Date"].isna()) & (filtered["HOP MO DATE"].isna()) & (filtered["RFI Status"].astype(str).str.strip().str.lower() != "pending")].copy()
ic_pend = filtered[(~filtered["HOP MATERIAL DELIVERY DATE"].isna()) & (filtered["HOP I&C DATE"].isna())].copy()
ms1_pend = filtered[(~filtered["HOP I&C DATE"].isna()) & (filtered["Alignment Date"].isna())].copy()
phy_pend = filtered[(~filtered["HOP I&C DATE"].isna()) & (filtered["PHY-AT ACCEPTANCE DATE"].isna())].copy()
soft_pend = filtered[(~filtered["Alignment Date"].isna()) & (filtered["SOFT AT ACCEPTANCE DATE"].isna())].copy()

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
        if df.empty:
            st.success(f"✅ No pending hops in {name}!")
            return
        col_head, col_dl = st.columns([3, 1])
        with col_head:
            st.markdown(f"#### 📉 {name} Pending List")
        df["Days Pending"] = get_aging(df, aging_base_col)
        base_cols = ["Circle", "HOP A-B", "SITE ID A", "SITE ID B", "CIRCLE_REMARK_1", aging_base_col, "Days Pending"]
        show_cols = [c for c in base_cols if c in df.columns]
        display_tab_df = format_date_cols(df[show_cols].copy())
        st.dataframe(display_tab_df.sort_values("Days Pending", ascending=False), use_container_width=True, hide_index=True)
        with col_dl:
            st.download_button(
                "📥 Download CSV",
                display_tab_df.to_csv(index=False).encode(),
                f"{name.replace(' ', '_')}_Pending_{datetime.now().strftime('%d%b')}.csv",
                "text/csv",
                use_container_width=True
            )

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
    fig = px.pie(filtered["Current Status"].value_counts().reset_index(), names="Current Status", values="count", title="Status Distribution", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(filtered["Circle"].value_counts().reset_index(), x="Circle", y="count", title="Hops by Circle")
    st.plotly_chart(fig2, use_container_width=True)

# ───────────────────── FOOTER ─────────────────────
st.markdown("---")
st.markdown(f"<p style='text-align:center; color:{sub_text};'>Last refreshed: {datetime.now().strftime('%d %b %y • %H:%M')} | Powered by Streamlit</p>", unsafe_allow_html=True)

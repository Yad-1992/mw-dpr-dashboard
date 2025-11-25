import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import uuid

# ------------------------------
# GOOGLE SHEET SETTINGS
# ------------------------------
SHEET_ID = "1BD-Bww-k_3jVwJAGqBbs02YcOoUyNrOWcY_T9xvnbgY"
SHEET_NAME = "User"

# ------------------------------
# GOOGLE AUTHENTICATION
# ------------------------------
creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# ------------------------------
# LOAD USERS
# ------------------------------
def load_users():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# ------------------------------
# ADD USER TO SHEET
# ------------------------------
def add_user(name, email, password):
    new_id = str(uuid.uuid4())
    row = [new_id, name, email.lower(), password]
    sheet.append_row(row)

# ------------------------------
# UI
# ------------------------------
st.title("Login System")

page = st.sidebar.selectbox("Menu", ["Signup", "Login"])

# ------------------------------
# SIGNUP
# ------------------------------
if page == "Signup":
    st.subheader("Create Account")

    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        users = load_users()

        if not users.empty and email.lower() in users["email"].astype(str).str.lower().values:
            st.error("Email already registered")
        else:
            add_user(name, email, password)
            st.success("Account created successfully")

# ------------------------------
# LOGIN
# ------------------------------
if page == "Login":
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if users.empty:
            st.error("No users found")
        else:
            user = users[
                (users["email"].str.lower() == email.lower()) &
                (users["password"] == password)
            ]

            if len(user) == 1:
                st.success("Login Successful")
            else:
                st.error("Invalid email or password")

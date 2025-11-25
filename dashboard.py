import streamlit as st
import pandas as pd
import uuid
import requests

# ------------------------------
# GOOGLE SHEET DETAILS
# ------------------------------
SHEET_ID = "1BD-Bww-k_3jVwJAGqBbs02YcOoUyNrOWcY_T9xvnbgY"
SHEET_NAME = "User"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# Your Google Apps Script Web App URL
SCRIPT_URL = "YOUR_WEB_APP_URL_HERE"  # Replace this


# ------------------------------
# LOAD ALL USERS
# ------------------------------
def load_users():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except:
        return pd.DataFrame(columns=["id", "name", "email", "password"])


# ------------------------------
# SAVE USER IN GOOGLE SHEET
# ------------------------------
def save_user(name, email, password):
    new_id = str(uuid.uuid4())
    params = {
        "type": "add_user",
        "id": new_id,
        "name": name,
        "email": email,
        "password": password
    }
    requests.get(SCRIPT_URL, params=params)


# ------------------------------
# UI
# ------------------------------
st.title("User Login System")

page = st.sidebar.selectbox("Menu", ["Signup", "Login"])


# ------------------------------
# SIGNUP PAGE
# ------------------------------
if page == "Signup":
    st.subheader("Create Account")

    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up"):
        users = load_users()

        if email in users["email"].astype(str).values:
            st.error("Email already exists")
        else:
            save_user(name, email, password)
            st.success("Account created")


# ------------------------------
# LOGIN PAGE
# ------------------------------
if page == "Login":
    st.subheader("Sign In")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        row = users[
            (users["email"] == email) &
            (users["password"] == password)
        ]

        if len(row) == 1:
            st.success("Login successful")
        else:
            st.error("Wrong email or password")


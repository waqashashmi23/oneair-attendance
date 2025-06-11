import streamlit as st
import pandas as pd
from datetime import datetime
from pytz import timezone
import os

# Page Config
st.set_page_config(page_title="OneAir Attendance", layout="centered")

# Custom CSS
st.markdown("""
    <style>
        body {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', sans-serif;
        }
        .title {
            color: #e63946;
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .stTextInput > div > label,
        .stSelectbox > div > label,
        .stRadio > div > label,
        .stTextArea > div > label {
            font-weight: 600;
            color: #1d3557;
        }
        .stButton button {
            background-color: #e63946;
            color: white;
            border-radius: 8px;
            padding: 0.6em 1.2em;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<div class='title'>OneAir Attendance Portal</div>", unsafe_allow_html=True)

# Attendance Form
with st.form("attendance_form"):
    name = st.text_input("👤 Name")
    group = st.selectbox("👥 Group", ["Sales", "Office", "Management", "Other"])
    status = st.radio("🕒 Attendance Type", ["Start Time (Check-In)", "End Time (Check-Out)"])
    remarks = st.text_area("📝 Remarks (optional)")
    submitted = st.form_submit_button("Submit Attendance")

    if submitted:
        if not name:
            st.error("❗ Please enter your name.")
        else:
            pk_tz = timezone("Asia/Karachi")
            timestamp = datetime.now(pk_tz).strftime("%Y-%m-%d %I:%M:%S %p")

            new_data = pd.DataFrame([{
                "Name": name,
                "Group": group,
                "Status": status,
                "Timestamp": timestamp,
                "Remarks": remarks
            }])

            file_path = "attendance_records.xlsx"
            if os.path.exists(file_path):
                existing = pd.read_excel(file_path)
                df = pd.concat([existing, new_data], ignore_index=True)
            else:
                df = new_data

            df.to_excel(file_path, index=False)
            st.success("✅ Attendance recorded successfully!")

# Display Attendance Records
if os.path.exists("attendance_records.xlsx"):
    st.markdown("<h3 style='color:#1d3557;'>📊 Current Attendance Records</h3>", unsafe_allow_html=True)
    df = pd.read_excel("attendance_records.xlsx")
    st.dataframe(df, use_container_width=True)

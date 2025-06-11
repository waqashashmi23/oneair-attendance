import streamlit as st
import pandas as pd
from datetime import datetime
from pytz import timezone
import os

# Set up the page
st.set_page_config(page_title="OneAir Attendance", layout="centered")
st.markdown("<h1 style='color:red;'>OneAir Attendance Portal</h1>", unsafe_allow_html=True)

# Attendance form
with st.form("attendance_form"):
    name = st.text_input("Name")
    group = st.selectbox("Group", ["Sales", "Office", "Management", "Other"])
    status = st.radio("Attendance Type", ["Start Time (Check-In)", "End Time (Check-Out)"])
    remarks = st.text_area("Remarks (optional)")
    submitted = st.form_submit_button("Submit Attendance")

    if submitted:
        if not name:
            st.error("❗ Please enter your name.")
        else:
            # Get current time in Pakistan timezone
            pk_tz = timezone("Asia/Karachi")
            timestamp = datetime.now(pk_tz).strftime("%Y-%m-%d %I:%M:%S %p")

            # Record new data
            new_data = pd.DataFrame([{
                "Name": name,
                "Group": group,
                "Status": status,
                "Timestamp": timestamp,
                "Remarks": remarks
            }])

            # Save to Excel
            file_path = "attendance_records.xlsx"
            if os.path.exists(file_path):
                existing = pd.read_excel(file_path)
                df = pd.concat([existing, new_data], ignore_index=True)
            else:
                df = new_data

            df.to_excel(file_path, index=False)
            st.success("✅ Attendance recorded successfully!")

# Show recorded data if exists
if os.path.exists("attendance_records.xlsx"):
    st.subheader("📊 Current Attendance Records")
    df = pd.read_excel("attendance_records.xlsx")
    st.dataframe(df)

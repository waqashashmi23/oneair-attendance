import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from geopy.geocoders import Nominatim
import pandas as pd
from datetime import datetime
from pytz import timezone
import os

# Set up the page
st.set_page_config(page_title="OneAir Attendance", layout="centered")
st.markdown("<h1 style='color:red;'>OneAir Attendance Portal</h1>", unsafe_allow_html=True)

# Prompt for location permission
st.write("📍 Please allow location access in your browser to mark attendance.")

# Get browser location
location = streamlit_js_eval(js_expressions="navigator.geolocation", key="get_location")

# Check for location
address = None
if not location or not location.get("coords"):
    st.warning("⚠️ Could not detect your location. Please allow location access and refresh the page.")
else:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    try:
        geolocator = Nominatim(user_agent="oneair-attendance")
        location_name = geolocator.reverse((lat, lon), language='en')
        address = location_name.address if location_name else "Location not found"
    except:
        address = "Location lookup failed"

# Attendance form
with st.form("attendance_form"):
    name = st.text_input("Name")
    group = st.selectbox("Group", ["Sales", "Office", "Management", "Other"])
    status = st.radio("Attendance Type", ["Start Time (Check-In)", "End Time (Check-Out)"])
    remarks = st.text_area("Remarks (optional)")
    submitted = st.form_submit_button("Submit Attendance")

    if submitted:
        if not name or not address or address in ["Location not found", "Location lookup failed"]:
            st.error("❗ Please fill all fields and ensure location is enabled.")
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
                "Location": address,
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

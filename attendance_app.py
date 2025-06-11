import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from geopy.geocoders import Nominatim
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="OneAir Attendance", layout="centered")

st.markdown("<h1 style='color:red;'>OneAir Attendance Portal</h1>", unsafe_allow_html=True)

st.write("📍 Please allow location access in your browser to mark attendance.")

# Get location from browser
location = streamlit_js_eval(js_expressions="navigator.geolocation", key="get_location")

if location and location.get("coords"):
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]

    # Get location name using geopy
    geolocator = Nominatim(user_agent="oneair-attendance")
    location_name = geolocator.reverse((lat, lon), language='en')
    address = location_name.address if location_name else "Location not found"
else:
    address = None

# Attendance Form
with st.form("attendance_form"):
    name = st.text_input("Name")
    group = st.selectbox("Group", ["Sales", "Office", "Management", "Other"])
    status = st.radio("Attendance Type", ["Start Time (Check-In)", "End Time (Check-Out)"])
    remarks = st.text_area("Remarks (e.g., Late, On the Way, etc.)")

    submitted = st.form_submit_button("Submit Attendance")

    if submitted:
        if not name or not address:
            st.error("Please fill all fields and ensure location is enabled.")
        else:
            from pytz import timezone
              pakistan_tz = timezone("Asia/Karachi")
              timestamp = datetime.now(pakistan_tz).strftime("%Y-%m-%d %I:%M:%S %p")
            new_data = pd.DataFrame([{
                "Name": name,
                "Group": group,
                "Status": status,
                "Timestamp": timestamp,
                "Location": address,
                "Remarks": remarks
            }])
            file = "attendance_records.xlsx"
            if os.path.exists(file):
                existing = pd.read_excel(file)
                df = pd.concat([existing, new_data], ignore_index=True)
            else:
                df = new_data
            df.to_excel(file, index=False)
            st.success("✅ Attendance recorded!")

# Show current records
if os.path.exists("attendance_records.xlsx"):
    df = pd.read_excel("attendance_records.xlsx")
    st.subheader("📊 Current Attendance Records")
    st.dataframe(df)


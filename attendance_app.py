import streamlit as st
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
import pandas as pd
from datetime import datetime
from pytz import timezone
import os
import json

# Set up the page
st.set_page_config(page_title="OneAir Attendance", layout="centered")
st.markdown("<h1 style='color:red;'>OneAir Attendance Portal</h1>", unsafe_allow_html=True)

st.write("📍 Please allow location access in your browser to mark attendance.")

# JavaScript to get location and send to Streamlit
components.html("""
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const coords = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };
            const streamlitEvent = new CustomEvent("streamlit:location", {
                detail: coords
            });
            window.dispatchEvent(streamlitEvent);
        },
        function(error) {
            const streamlitEvent = new CustomEvent("streamlit:location", {
                detail: {error: error.message}
            });
            window.dispatchEvent(streamlitEvent);
        }
    );
    </script>
""", height=0)

# Location input placeholder
location_data = st.experimental_get_query_params().get("location")

# Use session state to cache location
if "coords" not in st.session_state:
    st.session_state.coords = None

# Capture event from browser
location_event = st.experimental_get_query_params()
if "lat" in location_event and "lon" in location_event:
    st.session_state.coords = {
        "latitude": float(location_event["lat"][0]),
        "longitude": float(location_event["lon"][0])
    }

address = None
lat = lon = None
if st.session_state.coords:
    lat = st.session_state.coords["latitude"]
    lon = st.session_state.coords["longitude"]
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

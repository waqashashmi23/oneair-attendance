import streamlit as st
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
import os
import base64
import json

# Set page config
st.set_page_config(page_title="OneAir Attendance", page_icon="📅", layout="centered")

# JavaScript to get geolocation
def get_location_script():
    return """
    <script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const coords = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };
            const input = document.getElementById("geo-data");
            input.value = JSON.stringify(coords);
            input.dispatchEvent(new Event("input", { bubbles: true }));
        }
    );
    </script>
    """

# Title & Branding
st.markdown("""
    <h1 style='text-align: center; color: red;'>OneAir Attendance System</h1>
    <h4 style='text-align: center;'>Submit your Check-In / Check-Out attendance with location</h4>
""", unsafe_allow_html=True)

# Form
with st.form("attendance_form"):
    name = st.text_input("Full Name")
    group = st.text_input("Department / Group")
    action_type = st.selectbox("Action", ["Check-In", "Check-Out"])
    remarks = st.text_area("Remarks (e.g., Late, On the Way, Left Early, etc.)")

    # Hidden input for JS location
    geo_input = st.text_input("Geo", key="geo_data", value="", label_visibility="collapsed")
    st.markdown(get_location_script(), unsafe_allow_html=True)

    submit = st.form_submit_button("Submit Attendance")

# Handle submission
if submit:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    location_name = "Unknown"

    try:
        geo = json.loads(geo_input)
        lat, lon = geo["lat"], geo["lon"]

        # Get location name
        geolocator = Nominatim(user_agent="oneair_attendance")
        location = geolocator.reverse((lat, lon), timeout=10)
        if location:
            location_name = location.address
    except Exception as e:
        st.warning("Could not detect location automatically.")
        location_name = "Location fetch failed"

    # Save attendance
    data = {
        "Name": name,
        "Group": group,
        "Action": action_type,
        "Timestamp": timestamp,
        "Location": location_name,
        "Remarks": remarks
    }

    file_path = "attendance_records.xlsx"
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])

    df.to_excel(file_path, index=False)
    st.success("\u2705 Attendance successfully recorded!")

    # Download link
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="attendance_records.xlsx">\ud83d\udcc4 Download Excel File</a>'
        st.markdown(href, unsafe_allow_html=True)

# Footer
st.markdown("""
    <hr>
    <div style='text-align: center;'>
        <small>Powered by OneAir IT | Location enabled attendance system</small>
    </div>
""", unsafe_allow_html=True)
if os.path.exists("attendance_records.xlsx"):
    df_data = pd.read_excel("attendance_records.xlsx")
    st.subheader("📊 Current Attendance Records")
    st.dataframe(df_data)
else:
    st.warning("No attendance data found yet.")

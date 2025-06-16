import streamlit as st
import pandas as pd
from datetime import datetime, time
from pytz import timezone
import os
from streamlit_js_eval import streamlit_js_eval
from geopy.geocoders import Nominatim

# Page Config
st.set_page_config(page_title="OneAir Attendance", layout="centered")

# CSS Styling
st.markdown("""
    <style>
        html, body, .main {
            background: linear-gradient(to right, #f0f4f8, #d9e2ec);
            font-family: 'Segoe UI', sans-serif;
            color: #1e1e2f;
        }

        .block-container {
            background: linear-gradient(135deg, #fdfbfb, #ebedee);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.07);
            margin-top: 2rem;
            transition: all 0.3s ease-in-out;
        }

        @media (prefers-color-scheme: dark) {
            html, body, .main {
                background: linear-gradient(to right, #1a1a1a, #2c2c2c);
                color: #f8f9fa;
            }

            .block-container {
                background: linear-gradient(135deg, #2a2a2a, #1e1e1e);
                box-shadow: 0 6px 24px rgba(255, 255, 255, 0.05);
            }
        }

        .title {
            color: #e63946;
            text-align: center;
            font-size: 2.8em;
            font-weight: bold;
            margin: 20px 0 30px 0;
        }

        label, .stTextInput > div > label, .stSelectbox > div > label, .stRadio > div > label, .stTextArea > div > label {
            font-weight: 600;
            color: #1d3557;
        }

        @media (prefers-color-scheme: dark) {
            label {
                color: #a9bcd0;
            }
        }

        input, textarea, select {
            background-color: #f8f9fa !important;
            color: #212529 !important;
            border: 1px solid #ced4da !important;
            border-radius: 6px;
            padding: 0.5rem;
        }

        @media (prefers-color-scheme: dark) {
            input, textarea, select {
                background-color: #2b2b3c !important;
                color: #f8f9fa !important;
                border: 1px solid #444;
            }
        }

        .stButton button {
            background-color: #e63946;
            color: white;
            border-radius: 10px;
            padding: 0.7em 1.5em;
            font-weight: bold;
            transition: background 0.3s ease;
            border: none;
        }

        .stButton button:hover {
            background-color: #c62828;
        }

        thead tr th, tbody tr td {
            font-size: 0.95rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        .dataframe td, .dataframe th {
            padding: 0.6rem;
            border: 1px solid #dee2e6;
        }

        .stRadio > div {
            flex-direction: row;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>OneAir Attendance Portal</div>", unsafe_allow_html=True)

# Get Location via JS
location_data = streamlit_js_eval(
    js_expressions="""
        new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude
                }),
                (err) => resolve({ error: err.message })
            );
        })
    """,
    key="get_location",
)

latitude, longitude, address = None, None, ""
if location_data and location_data.get("latitude") and location_data.get("longitude"):
    latitude = location_data["latitude"]
    longitude = location_data["longitude"]
    try:
        geolocator = Nominatim(user_agent="streamlit_app")
        location_info = geolocator.reverse((latitude, longitude), language="en")
        address = location_info.address if location_info else "Address not found"
    except:
        address = "Could not fetch address"
else:
    address = "Location not available"

# Excel file setup
file_path = "attendance_records.xlsx"
if not os.path.exists(file_path):
    df = pd.DataFrame(columns=[
        "Name", "Group", "Action", "Status", "Date", "Time", "Mode",
        "Location", "Remarks", "Auto Status", "Visit Number"
    ])
    df.to_excel(file_path, index=False)

# Helper functions
def count_visits(df, name, date):
    return len(df[(df["Name"] == name) & (df["Date"] == date) &
                  (df["Mode"] == "Visit") & (df["Action"].str.contains("Start"))])

def find_open_visit(df, name, date):
    visits = df[(df["Name"] == name) & (df["Date"] == date) & (df["Mode"] == "Visit")]
    for i in range(1, 100):
        start = visits[visits["Action"] == f"Visit {i} Start"]
        end = visits[visits["Action"] == f"Visit {i} End"]
        if not start.empty and end.empty:
            return i
    return None

# Attendance Form
with st.form("attendance_form"):
    mode = st.selectbox("📍 Attendance Mode", ["Office", "Visit"])
    name = st.text_input("👤 Name")
    Department = st.selectbox("👥 Department", ["Sales", "Services", "After Market"])
    Team = st.selectbox("👥 Team", ["Pumps", "Compressor"])
    status = st.radio("🕒 Attendance Type", ["Check In", "Check Out", "Start Time", "End Time", "On Leave"], horizontal=True)
    remarks = st.text_area("📝 Remarks (optional)")
    submitted = st.form_submit_button("Submit Attendance")

    if submitted:
        if not name:
            st.error("❗ Please enter your name.")
            st.stop()

        pk_tz = timezone("Asia/Karachi")
        now = datetime.now(pk_tz)
        date_today = now.strftime("%Y-%m-%d")
        time_now = now.strftime("%I:%M:%S %p")

        df = pd.read_excel(file_path)
        already_on_leave = ((df["Name"] == name) & (df["Date"] == date_today) & (df["Status"] == "On Leave")).any()

        action_text, auto_status, visit_number = "", "-", ""

        if status == "On Leave":
            if already_on_leave:
                st.warning("⚠️ Already marked 'On Leave'.")
                st.stop()
            if ((df["Name"] == name) & (df["Date"] == date_today)).any():
                st.error("❌ Cannot mark 'On Leave' after Check In/Out.")
                st.stop()
            action_text, auto_status = "-", "Leave"

        elif mode == "Office":
            if status == "Check In":
                if ((df["Name"] == name) & (df["Date"] == date_today) &
                    (df["Action"] == "Check In") & (df["Mode"] == "Office")).any():
                    st.warning("⚠️ Already checked in today.")
                    st.stop()
                action_text = "Check In"
                auto_status = "On Time" if time(9, 0) <= now.time() <= time(9, 30) else "Late"

            elif status == "Check Out":
                if not ((df["Name"] == name) & (df["Date"] == date_today) & (df["Action"] == "Check In")).any():
                    st.error("❌ Must Check In before Check Out.")
                    st.stop()
                if ((df["Name"] == name) & (df["Date"] == date_today) &
                    (df["Action"] == "Check Out") & (df["Mode"] == "Office")).any():
                    st.warning("⚠️ Already checked out today.")
                    st.stop()
                action_text = "Check Out"
                current_time = now.time()
                auto_status = "Overtime" if current_time > time(17, 30) or current_time < time(6, 0) else "-"

            else:
                st.warning("⚠️ Invalid action for Office mode.")
                st.stop()

        elif mode == "Visit":
            if status == "Start Time":
                visit_number = count_visits(df, name, date_today) + 1
                action_text = f"Visit {visit_number} Start"
            elif status == "End Time":
                open_visit = find_open_visit(df, name, date_today)
                if not open_visit:
                    st.error("❌ No active visit to end.")
                    st.stop()
                visit_number = open_visit
                action_text = f"Visit {visit_number} End"
            else:
                st.warning("⚠️ Invalid action for Visit mode.")
                st.stop()
        else:
            st.error("❌ Unknown mode.")
            st.stop()

        new_row = pd.DataFrame([{
            "Name": name,
            "Department": Department,
            "Team": Team,
            "Action": action_text,
            "Status": status,
            "Date": date_today,
            "Time": time_now,
            "Mode": mode,
            "Location": address if address and "not available" not in address.lower() else "Location not available",
            "Remarks": remarks,
            "Auto Status": auto_status,
            "Visit Number": visit_number,

        }])

        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(file_path, index=False)
        st.success("✅ Attendance recorded successfully!")

# View Records
if os.path.exists(file_path):
    st.markdown("### 🔐 View Attendance Records")
    role = st.radio("Select your role", ["Employee", "Admin"], horizontal=True)
    
    df = pd.read_excel(file_path)
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed|^0$")]

    def highlight_status(val):
        color = {"On Time": "#74b884", "Late": "#e87e89", "Overtime": "#77ade6", "Leave": "#a783ea"}.get(val, "")
        if "Visit" in str(val):
            color = "#f0b07c"
        return f"background-color: {color}; color: white; font-weight: bold; text-align: center" if color else ""

    if role == "Employee":
        employee_name = st.text_input("🔍 Enter your name")
        if employee_name:
            filtered_df = df[df["Name"].str.lower() == employee_name.strip().lower()]
            if not filtered_df.empty:
                st.markdown(f"### 📄 Attendance for **{employee_name.title()}**")
                st.dataframe(filtered_df.style.applymap(highlight_status, subset=["Auto Status"]), use_container_width=True)
            else:
                st.info("ℹ️ No records found.")

    elif role == "Admin":
        admin_password = st.text_input("🔑 Enter admin password", type="password")
        if admin_password == "OneAir@123":
            st.success("✅ Access granted")

            st.markdown("### 📅 Filter Records by Date or Range")
            date_range = st.date_input("📆 Select date(s)", value=(datetime.now(), datetime.now()))

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start, end = date_range
                if start and end:
                    start_str = start.strftime("%Y-%m-%d")
                    end_str = end.strftime("%Y-%m-%d")
                    filtered_admin_df = df[(df["Date"] >= start_str) & (df["Date"] <= end_str)]
                    if not filtered_admin_df.empty:
                        label = f"**{start_str}**" if start_str == end_str else f"from **{start_str}** to **{end_str}**"
                        st.markdown(f"### 📋 Attendance Records {label}")
                        st.dataframe(filtered_admin_df.style.applymap(highlight_status, subset=["Auto Status"]), use_container_width=True)
                    else:
                        st.info(f"ℹ️ No records from {start_str} to {end_str}.")
                else:
                    st.warning("⚠️ Please select both a start and end date.")
            else:
                st.warning("⚠️ Please select both a start and end date.")
        elif admin_password:
            st.error("❌ Incorrect password.")

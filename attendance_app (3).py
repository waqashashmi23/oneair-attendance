import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# OneAir Attendance Portal
# ---------------------------------------------------------
st.set_page_config(page_title="OneAir Attendance", page_icon="🕒", layout="centered")

DATA_FILE = "attendance_records.xlsx"
PK_TZ = ZoneInfo("Asia/Karachi")
COLUMNS = [
    "Name", "Department", "Team", "Action", "Status", "Date", "Time",
    "Mode", "Location", "Remarks", "Auto Status", "Visit Number"
]

# Set ONEAIR_ADMIN_PASSWORD in Streamlit Cloud > App > Settings > Secrets.
# Local fallback is provided for convenience; change it before deployment.
ADMIN_PASSWORD = st.secrets.get("ONEAIR_ADMIN_PASSWORD", os.getenv("ONEAIR_ADMIN_PASSWORD", "CHANGE_ME_NOW"))

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to right, #f0f4f8, #d9e2ec);
        color: #1e1e2f;
    }
    .block-container {
        max-width: 900px;
        padding: 2rem 2rem 3rem;
        background: rgba(255,255,255,0.88);
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.07);
        margin-top: 1.5rem;
    }
    .oneair-title {
        color: #e63946;
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0.4rem 0 1.5rem;
    }
    .stButton button, .stFormSubmitButton button {
        background: #e63946;
        color: white;
        border: 0;
        border-radius: 9px;
        font-weight: 700;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        background: #c62828;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='oneair-title'>OneAir Attendance Portal</div>", unsafe_allow_html=True)
st.caption("Enter your details carefully. Use Office for office attendance and Visit for field visits.")

def load_records():
    """Load records and safely handle older Excel files with missing columns."""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(DATA_FILE, index=False)
        return df

    try:
        df = pd.read_excel(DATA_FILE, dtype={"Date": str})
    except Exception as exc:
        st.error(f"Could not read {DATA_FILE}: {exc}")
        st.stop()

    # Add any columns missing from older versions, including Department and Team.
    for column in COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[COLUMNS].copy()

def save_records(df):
    """Save all records to the Excel file."""
    try:
        df[COLUMNS].to_excel(DATA_FILE, index=False)
    except PermissionError:
        st.error("The Excel file is open or locked. Close it and submit again.")
        st.stop()
    except Exception as exc:
        st.error(f"Could not save attendance: {exc}")
        st.stop()

def count_visits(df, name, date_today):
    mask = (
        df["Name"].astype(str).str.casefold().eq(name.casefold())
        & df["Date"].astype(str).eq(date_today)
        & df["Mode"].astype(str).eq("Visit")
        & df["Action"].astype(str).str.endswith(" Start")
    )
    return int(mask.sum())

def find_open_visit(df, name, date_today):
    rows = df[
        df["Name"].astype(str).str.casefold().eq(name.casefold())
        & df["Date"].astype(str).eq(date_today)
        & df["Mode"].astype(str).eq("Visit")
    ]
    starts = {}
    ended = set()
    for action in rows["Action"].astype(str):
        if action.startswith("Visit ") and action.endswith(" Start"):
            try:
                visit_no = int(action.split()[1])
                starts[visit_no] = True
            except (ValueError, IndexError):
                pass
        elif action.startswith("Visit ") and action.endswith(" End"):
            try:
                ended.add(int(action.split()[1]))
            except (ValueError, IndexError):
                pass
    open_visits = sorted(set(starts) - ended)
    return open_visits[0] if open_visits else None

def name_date_mask(df, name, date_today):
    return (
        df["Name"].astype(str).str.casefold().eq(name.casefold())
        & df["Date"].astype(str).eq(date_today)
    )

def highlight_status(value):
    colors = {
        "On Time": "#74b884",
        "Late": "#e87e89",
        "Overtime": "#77ade6",
        "Leave": "#a783ea",
    }
    value = str(value)
    color = colors.get(value, "#f0b07c" if "Visit" in value else "")
    if not color:
        return ""
    return f"background-color: {color}; color: white; font-weight: bold; text-align: center"

records = load_records()

st.subheader("📝 Submit Attendance")
with st.form("attendance_form", clear_on_submit=False):
    mode = st.selectbox("📍 Attendance Mode", ["Office", "Visit"])
    name = st.text_input("👤 Employee name").strip()
    department = st.selectbox("👥 Department", ["Sales", "Services", "After Market"])
    team = st.selectbox("👥 Team", ["Pumps", "Compressor"])
    if mode == "Office":
        status = st.radio(
            "🕒 Attendance Type",
            ["Check In", "Check Out", "On Leave"],
            horizontal=True,
        )
    else:
        status = st.radio(
            "🕒 Visit Type",
            ["Start Time", "End Time"],
            horizontal=True,
        )
    location = st.text_input("📌 Location (enter office / customer / area)")
    remarks = st.text_area("📝 Remarks (optional)")
    submitted = st.form_submit_button("Submit Attendance", use_container_width=True)

if submitted:
    if not name:
        st.error("Please enter your name.")
        st.stop()

    now = datetime.now(PK_TZ)
    date_today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%I:%M:%S %p")
    current_time = now.time().replace(tzinfo=None)
    records = load_records()
    person_today = name_date_mask(records, name, date_today)
    today_records = records[person_today]
    already_on_leave = today_records["Status"].astype(str).eq("On Leave").any()

    action_text = ""
    auto_status = "-"
    visit_number = ""

    if status == "On Leave":
        if already_on_leave:
            st.warning("You have already marked On Leave today.")
            st.stop()
        if not today_records.empty:
            st.error("You cannot mark On Leave after another attendance action today.")
            st.stop()
        action_text = "-"
        auto_status = "Leave"

    elif mode == "Office" and status == "Check In":
        if today_records[
            today_records["Mode"].astype(str).eq("Office")
            & today_records["Action"].astype(str).eq("Check In")
        ].shape[0] > 0:
            st.warning("You have already checked in today.")
            st.stop()
        action_text = "Check In"
        auto_status = "On Time" if time(9, 0) <= current_time <= time(9, 30) else "Late"

    elif mode == "Office" and status == "Check Out":
        office_check_in = today_records[
            today_records["Mode"].astype(str).eq("Office")
            & today_records["Action"].astype(str).eq("Check In")
        ]
        if office_check_in.empty:
            st.error("You must Check In at the office before Check Out.")
            st.stop()
        if today_records[
            today_records["Mode"].astype(str).eq("Office")
            & today_records["Action"].astype(str).eq("Check Out")
        ].shape[0] > 0:
            st.warning("You have already checked out today.")
            st.stop()
        action_text = "Check Out"
        auto_status = "Overtime" if current_time > time(17, 30) else "-"

    elif mode == "Visit" and status == "Start Time":
        visit_number = count_visits(records, name, date_today) + 1
        action_text = f"Visit {visit_number} Start"

    elif mode == "Visit" and status == "End Time":
        open_visit = find_open_visit(records, name, date_today)
        if open_visit is None:
            st.error("No active visit found. Start a visit before ending it.")
            st.stop()
        visit_number = open_visit
        action_text = f"Visit {visit_number} End"

    else:
        st.error("Invalid attendance action for the selected mode.")
        st.stop()

    new_row = {
        "Name": name,
        "Department": department,
        "Team": team,
        "Action": action_text,
        "Status": status,
        "Date": date_today,
        "Time": time_now,
        "Mode": mode,
        "Location": location.strip() or "Not provided",
        "Remarks": remarks.strip(),
        "Auto Status": auto_status,
        "Visit Number": visit_number,
    }
    records = pd.concat([records, pd.DataFrame([new_row])], ignore_index=True)
    save_records(records)
    st.success(f"Attendance recorded successfully for {name} at {time_now}.")
    st.rerun()

st.divider()
st.subheader("🔐 View Attendance Records")
role = st.radio("Select your role", ["Employee", "Admin"], horizontal=True, key="view_role")
records = load_records()

if role == "Employee":
    st.info("Employee view is name-based and is not private. Add employee login/password authentication before using this for sensitive records.")
    employee_name = st.text_input("🔎 Enter your name to find records", key="employee_search").strip()
    if employee_name:
        filtered = records[
            records["Name"].astype(str).str.casefold().eq(employee_name.casefold())
        ].copy()
        if filtered.empty:
            st.info("No records found for that name.")
        else:
            st.dataframe(
                filtered.style.applymap(highlight_status, subset=["Auto Status"]),
                use_container_width=True,
                hide_index=True,
            )

else:
    admin_password = st.text_input("🔑 Admin password", type="password", key="admin_password")
    if admin_password and ADMIN_PASSWORD == "CHANGE_ME_NOW":
        st.warning("Set ONEAIR_ADMIN_PASSWORD in Streamlit Cloud Secrets before using Admin access.")
    elif admin_password == ADMIN_PASSWORD and ADMIN_PASSWORD != "CHANGE_ME_NOW":
        st.success("Admin access granted.")
        today = datetime.now(PK_TZ).date()
        date_range = st.date_input(
            "📅 Select date range",
            value=(today, today),
            key="admin_date_range",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        filtered = records[
            records["Date"].astype(str).between(start_str, end_str, inclusive="both")
        ].copy()
        if filtered.empty:
            st.info(f"No records found from {start_str} to {end_str}.")
        else:
            st.dataframe(
                filtered.style.applymap(highlight_status, subset=["Auto Status"]),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "⬇️ Download filtered records (CSV)",
                data=filtered.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"oneair_attendance_{start_str}_to_{end_str}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    elif admin_password:
        st.error("Incorrect admin password.")

st.caption("Time zone: Pakistan Standard Time (Asia/Karachi).")
st.warning(
    "Deployment note: this version stores records in a local Excel file. "
    "On Streamlit Cloud, local files may not be durable across app restarts/redeployments. "
    "For reliable company attendance history, connect persistent storage such as a database or Google Sheets."
)

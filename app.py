import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os


import plotly.express as px
from datetime import datetime, timedelta
import os
import base64

# Set page configuration
st.set_page_config(
    page_title="Work Time Tracking",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the app
st.title("📊 Work Time Tracking App")

# Function to get the start of the current week (Monday)
def get_week_dates(start_date=None):
    if start_date is None:
        start_date = datetime.today()
    start_of_week = start_date - timedelta(days=start_date.weekday())  # Monday
    week_dates = [start_of_week + timedelta(days=i) for i in range(5)]  # Mon-Fri
    return week_dates

# Generate a unique code based on the current year, month, and ISO week number
def generate_unique_code(date):
    year = date.year
    month = date.month
    week_number = date.isocalendar()[1]
    return f"{year}_M{month:02d}_W{week_number:02d}"

# Initialize session state for dates and unique code
if 'week_dates' not in st.session_state:
    st.session_state.week_dates = get_week_dates()
    st.session_state.unique_code = generate_unique_code(datetime.today())

# Display the dates
week_dates = st.session_state.week_dates
date_strings = [date.strftime("%Y-%m-%d") for date in week_dates]

# Prepare data storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, f"work_log_{st.session_state.unique_code}.csv")

# Initialize data
def load_existing_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "Date", "Project Name", "Task", "Effort Spent (hrs)",
            "Task Summary", "Internal Meetings Time (hrs)", "Client Meetings Time (hrs)"
        ])

existing_data = load_existing_data()

# Ensure consistent data types
def enforce_data_types(df):
    df["Date"] = df["Date"].astype(str)
    df["Project Name"] = df["Project Name"].astype(str)
    df["Task"] = df["Task"].astype(str)
    df["Effort Spent (hrs)"] = pd.to_numeric(df["Effort Spent (hrs)"], errors='coerce').fillna(0.0)
    df["Task Summary"] = df["Task Summary"].astype(str)
    df["Internal Meetings Time (hrs)"] = pd.to_numeric(df["Internal Meetings Time (hrs)"], errors='coerce').fillna(0.0)
    df["Client Meetings Time (hrs)"] = pd.to_numeric(df["Client Meetings Time (hrs)"], errors='coerce').fillna(0.0)
    return df

existing_data = enforce_data_types(existing_data)

# Initialize a new DataFrame for the current week if no existing data
if existing_data.empty:
    current_week_data = pd.DataFrame(columns=[
        "Date", "Project Name", "Task", "Effort Spent (hrs)",
        "Task Summary", "Internal Meetings Time (hrs)", "Client Meetings Time (hrs)"
    ])
    # Optionally, pre-populate with one row per date
    for date_str in date_strings:
        current_week_data = pd.concat([
            current_week_data,
            pd.DataFrame([{
                "Date": date_str,
                "Project Name": "",
                "Task": "",
                "Effort Spent (hrs)": 0.0,
                "Task Summary": "",
                "Internal Meetings Time (hrs)": 0.0,
                "Client Meetings Time (hrs)": 0.0
            }])
        ], ignore_index=True)
else:
    current_week_data = existing_data

# Store current_week_data in session state to handle dynamic updates
if 'current_week_data' not in st.session_state:
    st.session_state.current_week_data = current_week_data
else:
    current_week_data = st.session_state.current_week_data

# Sidebar with Add Entry buttons for each date
st.sidebar.header("Add Entries")
for date_str in date_strings:
    if st.sidebar.button(f"Add Entry for {date_str}"):
        # Define the new row
        new_row = {
            "Date": date_str,
            "Project Name": "",
            "Task": "",
            "Effort Spent (hrs)": 0.0,
            "Task Summary": "",
            "Internal Meetings Time (hrs)": 0.0,
            "Client Meetings Time (hrs)": 0.0
        }
        # Create a DataFrame for the new row
        new_row_df = pd.DataFrame([new_row])
        # Concatenate the new row
        current_week_data = pd.concat([current_week_data, new_row_df], ignore_index=True)
        # Update session state
        st.session_state.current_week_data = current_week_data

# Input form
st.header("Enter Your Work Details")

# Define the allowed dates for the dropdown
allowed_dates = date_strings

# Editable data table with enhanced configuration
edited_data = st.data_editor(
    current_week_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_order=[
        "Date", "Project Name", "Task", "Effort Spent (hrs)",
        "Task Summary", "Internal Meetings Time (hrs)", "Client Meetings Time (hrs)"
    ],
    column_config={
        "Date": st.column_config.SelectboxColumn(
            "Date",
            options=allowed_dates,
            default=allowed_dates[0],
        ),
        "Project Name": st.column_config.TextColumn("Project Name"),
        "Task": st.column_config.TextColumn("Task"),
        "Effort Spent (hrs)": st.column_config.NumberColumn(
            "Effort Spent (hrs)", min_value=0.0, step=0.5
        ),
        "Task Summary": st.column_config.TextColumn("Task Summary"),
        "Internal Meetings Time (hrs)": st.column_config.NumberColumn(
            "Internal Meetings Time (hrs)", min_value=0.0, step=0.5
        ),
        "Client Meetings Time (hrs)": st.column_config.NumberColumn(
            "Client Meetings Time (hrs)", min_value=0.0, step=0.5
        ),
    }
)

# Update session state with edited data
st.session_state.current_week_data = edited_data

# Save button
if st.button("Save"):
    # Save the edited data
    edited_data = enforce_data_types(edited_data)
    edited_data.to_csv(DATA_FILE, index=False)
    st.success("Work time data saved successfully!")

# Display existing data
st.header("Existing Work Time Data")
if not existing_data.empty:
    st.dataframe(existing_data)
else:
    st.write("No data available yet.")
    
    
# ----------------------------
# New Feature: Weekly Effort Pie Chart
# ----------------------------
st.header("📈 Weekly Effort Summary")

# Calculate total effort spent in the week
total_effort = edited_data["Effort Spent (hrs)"].sum()
denominator = 40  # Total available hours in a standard workweek
remaining = denominator - total_effort
remaining = max(remaining, 0)  # Ensure remaining hours don't go negative

# Prepare data for pie chart
pie_data_weekly = {
    "Category": ["Effort Spent (hrs)", "Remaining (hrs)"],
    "Hours": [total_effort, remaining]
}

# Create pie chart using Plotly Express
fig_weekly = px.pie(
    pie_data_weekly,
    names="Category",
    values="Hours",
    title="Total Effort Spent This Week",
    color_discrete_sequence=px.colors.qualitative.Pastel
)

# Display the pie chart
st.plotly_chart(fig_weekly, use_container_width=True)

# ----------------------------
# New Feature: Daily Project Distribution Pie Charts
# ----------------------------
st.header("📊 Daily Project Distribution")

# Iterate over each date and create a pie chart for project distribution
for date_str in date_strings:
    # Filter data for the current date
    data_date = edited_data[edited_data["Date"] == date_str]
    
    if not data_date.empty:
        # Group by 'Project Name' and sum 'Effort Spent (hrs)'
        project_effort = data_date.groupby("Project Name")["Effort Spent (hrs)"].sum().reset_index()
        
        # Handle cases where 'Project Name' might be empty
        project_effort = project_effort[project_effort["Project Name"].str.strip() != ""]
        
        if not project_effort.empty:
            # Create pie chart for the current date
            fig_daily = px.pie(
                project_effort,
                names="Project Name",
                values="Effort Spent (hrs)",
                title=f"Project Distribution for {date_str}",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            # Display the pie chart
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.write(f"**{date_str}**: No project entries.")
    else:
        st.write(f"**{date_str}**: No data available.")

# ----------------------------
# Existing Work Time Data Display
# ----------------------------
st.header("📄 Existing Work Time Data")
if not existing_data.empty:
    st.dataframe(existing_data)
else:
    st.write("No data available yet.")
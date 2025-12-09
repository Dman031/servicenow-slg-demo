"""Streamlit dashboard for State & Local Government service request management."""

import json
import os
from datetime import datetime
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.ai_router import classify_request
from backend.models import ServiceRequest
from backend.workflow import WORKFLOW_STATES, advance_workflow

# Page configuration
st.set_page_config(page_title="Service Request Management", layout="wide")

# Initialize session state
if 'requests' not in st.session_state:
    st.session_state.requests = []
    # Load sample requests on first run
    sample_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'sample_requests.json')
    if os.path.exists(sample_file):
        with open(sample_file, 'r') as f:
            sample_data = json.load(f)
        
        # Apply AI classification to each request
        for req_data in sample_data:
            classification = classify_request(
                req_data['summary'],
                req_data['description'],
                req_data['channel']
            )
            
            # Create ServiceRequest with AI classification
            request = ServiceRequest(
                id=req_data['id'],
                channel=req_data['channel'],
                requester_type=req_data['requester_type'],
                department=classification['department'],
                summary=req_data['summary'],
                description=req_data['description'],
                status=req_data['status'],
                priority=classification['priority'],
                category=classification['category'],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            st.session_state.requests.append(request)

# HEADER
st.title("City of Sacramento - Service Request Management")
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"Current Date and Time: {current_time}")

# SIDEBAR - COMPLIANCE & METRICS
with st.sidebar:
    st.header("Compliance & Metrics")
    
    # Department filter
    departments = ['All'] + sorted(list(set(
        [req.department for req in st.session_state.requests if req.department]
    )))
    selected_department = st.selectbox("Department Filter", departments)
    
    # Status filter
    statuses = ['All'] + WORKFLOW_STATES
    selected_status = st.selectbox("Status Filter", statuses)
    
    # Request counts by status
    st.subheader("Request Counts by Status")
    status_counts = {}
    for status in WORKFLOW_STATES:
        count = sum(1 for req in st.session_state.requests if req.status == status)
        status_counts[status] = count
        st.metric(status, count)
    
    # Request counts by priority
    st.subheader("Request Counts by Priority")
    priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for req in st.session_state.requests:
        if req.priority:
            priority_counts[req.priority] = priority_counts.get(req.priority, 0) + 1
    for priority, count in priority_counts.items():
        st.metric(priority, count)

# Filter requests
filtered_requests = st.session_state.requests.copy()
if selected_department != 'All':
    filtered_requests = [req for req in filtered_requests if req.department == selected_department]
if selected_status != 'All':
    filtered_requests = [req for req in filtered_requests if req.status == selected_status]

# MAIN AREA - Two columns
col1, col2 = st.columns(2)

# LEFT COLUMN - ACTIVE REQUESTS
with col1:
    st.header("Active Requests")
    
    if not filtered_requests:
        st.info("No requests match the current filters.")
    else:
        for request in filtered_requests:
            # Priority color coding
            priority_color = {
                'High': '🔴',
                'Medium': '🟡',
                'Low': '🟢'
            }
            priority_badge = priority_color.get(request.priority, '⚪')
            
            # Status badge
            status_colors = {
                'NEW': 'blue',
                'TRIAGE': 'orange',
                'ASSIGNED': 'purple',
                'IN_PROGRESS': 'yellow',
                'RESOLVED': 'green',
                'CLOSED': 'gray'
            }
            status_color = status_colors.get(request.status, 'gray')
            
            with st.expander(
                f"{priority_badge} **#{request.id}** - {request.summary} | "
                f"Dept: {request.department or 'N/A'} | "
                f"Priority: {request.priority or 'N/A'} | "
                f"Status: {request.status}"
            ):
                st.write(f"**ID:** {request.id}")
                st.write(f"**Summary:** {request.summary}")
                st.write(f"**Department:** {request.department or 'N/A'}")
                st.write(f"**Category:** {request.category or 'N/A'}")
                st.write(f"**Priority:** {request.priority or 'N/A'}")
                st.write(f"**Status:** {request.status}")
                st.write(f"**Channel:** {request.channel}")
                st.write(f"**Requester Type:** {request.requester_type}")
                st.write(f"**Description:** {request.description}")
                if request.created_at:
                    st.write(f"**Created:** {request.created_at}")
                if request.updated_at:
                    st.write(f"**Updated:** {request.updated_at}")
                
                # Advance Workflow button
                if st.button(f"Advance Workflow", key=f"advance_{request.id}"):
                    new_status = advance_workflow(request.status)
                    request.status = new_status
                    request.updated_at = datetime.now().isoformat()
                    st.rerun()

# RIGHT COLUMN - CREATE NEW REQUEST
with col2:
    st.header("Create New Request")
    
    with st.form("new_request_form"):
        channel = st.selectbox("Channel", ["Resident Portal", "Phone", "Walk-in"])
        requester_type = st.selectbox("Requester Type", ["Resident", "Employee"])
        summary = st.text_input("Summary")
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            if summary and description:
                # Auto-assign ID
                max_id = max([req.id for req in st.session_state.requests], default=0)
                new_id = max_id + 1
                
                # Call AI classification
                classification = classify_request(summary, description, channel)
                
                # Create new request with timestamps
                new_request = ServiceRequest(
                    id=new_id,
                    channel=channel,
                    requester_type=requester_type,
                    department=classification['department'],
                    summary=summary,
                    description=description,
                    status='NEW',
                    priority=classification['priority'],
                    category=classification['category'],
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                st.session_state.requests.append(new_request)
                st.success(f"Request #{new_id} created successfully!")
                st.rerun()
            else:
                st.error("Please fill in both summary and description.")

# BOTTOM - ANALYTICS
st.divider()
st.header("Analytics")

if st.session_state.requests:
    # Prepare data for charts
    df = pd.DataFrame([req.dict() for req in st.session_state.requests])
    
    # Pie chart: Requests by Department
    if 'department' in df.columns:
        dept_counts = df['department'].value_counts()
        if not dept_counts.empty:
            fig_dept = px.pie(
                values=dept_counts.values,
                names=dept_counts.index,
                title="Requests by Department"
            )
            st.plotly_chart(fig_dept, use_container_width=True)
    
    # Bar charts side by side
    col3, col4 = st.columns(2)
    
    with col3:
        # Bar chart: Requests by Status
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            if not status_counts.empty:
                fig_status = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title="Requests by Status",
                    labels={'x': 'Status', 'y': 'Count'}
                )
                st.plotly_chart(fig_status, use_container_width=True)
    
    with col4:
        # Bar chart: Requests by Priority
        if 'priority' in df.columns:
            priority_counts = df['priority'].value_counts()
            if not priority_counts.empty:
                fig_priority = px.bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    title="Requests by Priority",
                    labels={'x': 'Priority', 'y': 'Count'},
                    color=priority_counts.index,
                    color_discrete_map={'High': 'red', 'Medium': 'yellow', 'Low': 'green'}
                )
                st.plotly_chart(fig_priority, use_container_width=True)
else:
    st.info("No requests available for analytics.")


"""Streamlit dashboard for State & Local Government service request management."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================================
# WORKFLOW MANAGEMENT
# ============================================================================

WORKFLOW_STATES = ['NEW', 'TRIAGE', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']


def advance_workflow(current_status: str) -> str:
    """
    Advance a service request to the next workflow state.
    
    Args:
        current_status: The current status of the service request
        
    Returns:
        The next status in the workflow. Returns 'CLOSED' if already closed,
        or 'NEW' if the status is unknown.
    """
    # If already closed, stay closed
    if current_status == 'CLOSED':
        return 'CLOSED'
    
    # Find current status index and return next state
    try:
        current_index = WORKFLOW_STATES.index(current_status)
        # Check if there's a next state
        if current_index < len(WORKFLOW_STATES) - 1:
            return WORKFLOW_STATES[current_index + 1]
        else:
            # Already at the last state (CLOSED)
            return 'CLOSED'
    except ValueError:
        # Unknown status, default to 'NEW'
        return 'NEW'


# ============================================================================
# AI REQUEST CLASSIFICATION
# ============================================================================

def classify_request(summary: str, description: str, channel: str) -> Dict:
    """
    Simulates ServiceNow's "Now Assist" AI routing.
    
    Classifies service requests based on keywords in summary and description
    to determine priority, category, and department.
    
    Args:
        summary: Brief summary of the service request
        description: Detailed description of the service request
        channel: Channel through which the request was submitted
        
    Returns:
        Dictionary with 'priority', 'category', 'department', 'confidence', 
        'keywords_detected', 'department_reason', and 'priority_reason' keys
    """
    # Combine summary and description for keyword matching (case-insensitive)
    text = f"{summary} {description}".lower()
    
    # Track detected keywords
    keywords_detected = []
    department_reason = ""
    priority_reason = ""
    
    # Determine priority based on keywords
    priority = 'Low'  # default
    priority_keywords = {
        'High': ['urgent', 'emergency', 'hazard', 'safety', 'dangerous'],
        'Medium': ['broken', 'not working', 'issue', 'problem', 'fault']
    }
    
    for prio_level, keywords in priority_keywords.items():
        found_keywords = [kw for kw in keywords if kw in text]
        if found_keywords:
            priority = prio_level
            keywords_detected.extend(found_keywords)
            priority_reason = f"Detected {prio_level.lower()} priority keywords: {', '.join(found_keywords[:3])}"
            break
    
    if not priority_reason:
        priority_reason = "No high-priority indicators found. Classified as Low priority."
    
    # Determine department based on keywords
    department = 'General Services'  # default
    category = 'General'  # default
    
    department_keywords = {
        'Public Works': {
            'keywords': ['pothole', 'streetlight', 'sidewalk', 'trash', 'infrastructure', 'road', 'street'],
            'reason': 'Infrastructure and public works keywords detected'
        },
        'Licensing': {
            'keywords': ['permit', 'license', 'zoning', 'business permit', 'application'],
            'reason': 'Permit and licensing keywords detected'
        },
        'IT': {
            'keywords': ['email', 'vpn', 'laptop', 'password', 'computer', 'network', 'software'],
            'reason': 'Technology and IT support keywords detected'
        },
        'HR': {
            'keywords': ['payroll', 'benefits', 'vacation', 'insurance', 'employee', 'hr'],
            'reason': 'Human resources and employee services keywords detected'
        }
    }
    
    for dept, dept_info in department_keywords.items():
        found_keywords = [kw for kw in dept_info['keywords'] if kw in text]
        if found_keywords:
            department = dept
            keywords_detected.extend(found_keywords)
            department_reason = dept_info['reason']
            break
    
    if department == 'Public Works':
        category = 'Infrastructure'
    elif department == 'Licensing':
        category = 'Permits & Licenses'
    elif department == 'IT':
        category = 'Technology'
    elif department == 'HR':
        category = 'Human Resources'
    else:
        category = 'General Services'
        department_reason = "No specific department keywords found. Routed to General Services."
    
    # Calculate confidence based on keyword matches
    total_keywords = len(keywords_detected)
    if total_keywords >= 3:
        confidence = min(95, 85 + (total_keywords - 3) * 2)
    elif total_keywords >= 2:
        confidence = 75 + (total_keywords - 2) * 5
    elif total_keywords >= 1:
        confidence = 65 + (total_keywords - 1) * 5
    else:
        confidence = 60
    
    # Ensure unique keywords
    keywords_detected = list(set(keywords_detected))
    
    return {
        'priority': priority,
        'category': category,
        'department': department,
        'confidence': confidence,
        'keywords_detected': keywords_detected,
        'department_reason': department_reason,
        'priority_reason': priority_reason
    }


# ============================================================================
# SERVICE REQUEST MODEL
# ============================================================================

class ServiceRequest:
    """Service Request model for State & Local Government."""
    
    def __init__(self, id: int, channel: str, requester_type: str, summary: str, 
                 description: str, status: str = 'NEW', department: Optional[str] = None,
                 priority: Optional[str] = None, category: Optional[str] = None,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None):
        self.id = id
        self.channel = channel
        self.requester_type = requester_type
        self.department = department
        self.summary = summary
        self.description = description
        self.status = status
        self.priority = priority
        self.category = category
        self.created_at = created_at
        self.updated_at = updated_at
    
    def dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'channel': self.channel,
            'requester_type': self.requester_type,
            'department': self.department,
            'summary': self.summary,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


# ============================================================================
# SAMPLE DATA
# ============================================================================

SAMPLE_REQUESTS = [
    {
        "id": 1,
        "channel": "Resident Portal",
        "requester_type": "Resident",
        "summary": "Large pothole on Main Street",
        "description": "There is a large pothole on Main Street near the intersection with Oak Avenue. It's causing damage to vehicles and is a safety hazard, especially during rainy weather.",
        "status": "NEW"
    },
    {
        "id": 2,
        "channel": "Phone",
        "requester_type": "Resident",
        "summary": "Streetlight not working on Elm Street",
        "description": "The streetlight at 123 Elm Street has been out for over a week. It's very dark at night and creates a safety concern for pedestrians and drivers.",
        "status": "NEW"
    },
    {
        "id": 3,
        "channel": "Walk-in",
        "requester_type": "Resident",
        "summary": "Missed trash pickup on Maple Drive",
        "description": "Our trash was not picked up on the scheduled day (Tuesday) at 456 Maple Drive. The bins were out by 6 AM as required. This is the second time this month.",
        "status": "NEW"
    },
    {
        "id": 4,
        "channel": "Resident Portal",
        "requester_type": "Resident",
        "summary": "Business permit application status",
        "description": "I submitted a business permit application for a new restaurant three weeks ago and haven't received any updates. Can you provide the current status and expected timeline?",
        "status": "NEW"
    },
    {
        "id": 5,
        "channel": "Resident Portal",
        "requester_type": "Employee",
        "summary": "Laptop screen is broken",
        "description": "My work laptop screen cracked when I accidentally dropped it. The screen is completely black now and I cannot use the device. I need a replacement or repair as soon as possible.",
        "status": "NEW"
    },
    {
        "id": 6,
        "channel": "Phone",
        "requester_type": "Employee",
        "summary": "Cannot reset password",
        "description": "I'm locked out of my account and the password reset link in my email is not working. I've tried multiple times but keep getting an error message. Need help accessing my account.",
        "status": "NEW"
    },
    {
        "id": 7,
        "channel": "Resident Portal",
        "requester_type": "Employee",
        "summary": "Payroll direct deposit not received",
        "description": "I did not receive my direct deposit for this pay period. I checked my bank account and confirmed the deposit was not made. My employee ID is 12345.",
        "status": "NEW"
    },
    {
        "id": 8,
        "channel": "Phone",
        "requester_type": "Employee",
        "summary": "Health insurance benefits question",
        "description": "I need to add my new spouse to my health insurance plan. What documents do I need to submit and what is the deadline for open enrollment changes?",
        "status": "NEW"
    }
]

# Page configuration
st.set_page_config(page_title="Service Request Management", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for ServiceNow styling
st.markdown("""
<style>
    /* ServiceNow Color Scheme */
    :root {
        --snow-navy: #1a1f36;
        --snow-green: #62d84e;
        --snow-gray: #f4f4f4;
        --snow-text: #2d2d2d;
        --snow-white: #ffffff;
        --snow-border: #e0e0e0;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ServiceNow Header */
    .snow-header {
        background-color: var(--snow-navy);
        color: white;
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: -1rem -1rem 1rem -1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .snow-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 600;
        font-size: 16px;
    }
    
    .snow-search {
        flex: 1;
        max-width: 400px;
        margin: 0 24px;
    }
    
    .snow-user {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Navigation Sidebar */
    .snow-nav-item {
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        color: var(--snow-text);
        text-decoration: none;
    }
    
    .snow-nav-item:hover {
        background-color: var(--snow-gray);
    }
    
    .snow-nav-item.active {
        background-color: var(--snow-green);
        color: white;
    }
    
    /* Request Cards */
    .snow-card {
        background: white;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 16px;
        border-left: 4px solid;
        padding: 16px;
    }
    
    .snow-card.high { border-left-color: #e74c3c; }
    .snow-card.medium { border-left-color: #f39c12; }
    .snow-card.low { border-left-color: var(--snow-green); }
    
    .snow-req-number {
        font-size: 18px;
        font-weight: 600;
        color: var(--snow-navy);
        margin-bottom: 8px;
    }
    
    .snow-req-title {
        font-size: 16px;
        color: var(--snow-text);
        margin-bottom: 12px;
    }
    
    .snow-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
    }
    
    .snow-badge.new { background: #3498db; color: white; }
    .snow-badge.triage { background: #e67e22; color: white; }
    .snow-badge.assigned { background: #9b59b6; color: white; }
    .snow-badge.in_progress { background: #f1c40f; color: #2d2d2d; }
    .snow-badge.resolved { background: var(--snow-green); color: white; }
    .snow-badge.closed { background: #95a5a6; color: white; }
    
    .snow-ai-tag {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        display: inline-block;
        margin-left: 8px;
    }
    
    .snow-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--snow-border);
    }
    
    .snow-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--snow-gray);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: var(--snow-text);
    }
    
    /* KPI Cards */
    .snow-kpi {
        background: white;
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .snow-kpi-value {
        font-size: 32px;
        font-weight: 600;
        color: var(--snow-navy);
        margin: 8px 0;
    }
    
    .snow-kpi-label {
        font-size: 14px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Form Styling */
    .snow-form-label {
        font-weight: 500;
        color: var(--snow-text);
        margin-bottom: 8px;
        display: block;
    }
    
    .stButton>button {
        background-color: var(--snow-green);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 24px;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #52c83e;
    }
    
    /* Footer */
    .snow-footer {
        text-align: center;
        padding: 24px;
        color: #7f8c8d;
        margin-top: 48px;
        border-top: 1px solid var(--snow-border);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--snow-gray);
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'requests' not in st.session_state:
    st.session_state.requests = []
    st.session_state.ai_insights = {}
    st.session_state.ai_routed_today = 0
    st.session_state.current_page = 'Dashboard'
    # Load sample requests on first run
    sample_data = SAMPLE_REQUESTS
    
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
        st.session_state.ai_insights[request.id] = classification
        st.session_state.ai_routed_today += 1

# Initialize AI insights if not present
if 'ai_insights' not in st.session_state:
    st.session_state.ai_insights = {}
if 'ai_routed_today' not in st.session_state:
    st.session_state.ai_routed_today = len(st.session_state.requests)
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Dashboard'

# Helper function to calculate time ago
def time_ago(timestamp_str):
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=None)
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown"

# SERVICE NOW HEADER
st.markdown("""
<div class="snow-header">
    <div class="snow-logo">
        <span>🔷</span>
        <span>Now Platform | Service Request Management</span>
    </div>
    <div class="snow-search">
        <input type="text" placeholder="Search requests..." style="width: 100%; padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 4px; background: rgba(255,255,255,0.1); color: white;"/>
    </div>
    <div class="snow-user">
        <div class="snow-avatar">JD</div>
        <span>John Doe</span>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("### Navigation")
    
    # Home button
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        st.session_state.current_page = 'Dashboard'
        st.rerun()
    
    # Navigation pages
    pages = ['Dashboard', 'Requests', 'Analytics', 'AI Insights', 'Settings']
    icons = {'Dashboard': '📊', 'Requests': '📋', 'Analytics': '📈', 'AI Insights': '✨', 'Settings': '⚙️'}
    
    for page in pages:
        icon = icons[page]
        is_active = st.session_state.current_page == page
        
        # Use different button styling for active page
        if is_active:
            if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True, type="primary"):
                st.session_state.current_page = page
                st.rerun()
        else:
            if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
    
    st.divider()
    
    # Filters
    st.markdown("### Filters")
    all_departments = ['All', 'Public Works', 'Licensing', 'IT', 'HR', 'General Services']
    selected_department = st.selectbox("Department", all_departments, key="dept_filter")
    
    statuses = ['All'] + WORKFLOW_STATES
    selected_status = st.selectbox("Status", statuses, key="status_filter")
    
    st.divider()
    
    # AI Insights
    st.markdown("### 🤖 Now Assist AI")
    st.metric("AI Routed Today", f"{st.session_state.ai_routed_today}")
    st.metric("Avg Time", "0.3s")
    st.metric("Accuracy", "97%")

# Filter requests
filtered_requests = st.session_state.requests.copy()
if selected_department != 'All':
    filtered_requests = [req for req in filtered_requests if req.department == selected_department]
if selected_status != 'All':
    filtered_requests = [req for req in filtered_requests if req.status == selected_status]

# Calculate metrics
open_requests = sum(1 for req in st.session_state.requests if req.status != 'CLOSED')
avg_resolution = "2.4 days"  # Placeholder
ai_accuracy = "97%"
sla_compliance = "94%"

# Main content based on selected page
if st.session_state.current_page == 'Dashboard':
    # KPI Cards
    st.markdown("### Key Performance Indicators")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">Open Requests</div>
            <div class="snow-kpi-value">{open_requests}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">Avg Resolution Time</div>
            <div class="snow-kpi-value">{avg_resolution}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">AI Accuracy</div>
            <div class="snow-kpi-value">{ai_accuracy}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">SLA Compliance</div>
            <div class="snow-kpi-value">{sla_compliance}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create New Request button
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("➕ Create New Request", use_container_width=True, type="primary"):
            st.session_state.current_page = 'Requests'
            st.rerun()
    
    st.markdown("### Recent Activity")
    
    # Show recent requests (last 5)
    recent_requests = sorted(st.session_state.requests, 
                             key=lambda x: x.created_at if x.created_at else "", 
                             reverse=True)[:5]
    
    if recent_requests:
        for request in recent_requests:
            ai_info = st.session_state.ai_insights.get(request.id, {})
            confidence = ai_info.get('confidence', 85)
            priority_class = request.priority.lower() if request.priority else 'low'
            status_class = request.status.lower().replace('_', '_')
            time_created = time_ago(request.created_at) if request.created_at else "Unknown"
            has_ai = request.id in st.session_state.ai_insights
            
            card_html = f"""
            <div class="snow-card {priority_class}">
                <div class="snow-req-number">
                    REQ{str(request.id).zfill(7)}
                    {'<span class="snow-ai-tag">✨ AI Suggested</span>' if has_ai else ''}
                </div>
                <div class="snow-req-title">{request.summary}</div>
                <div style="margin-bottom: 12px;">
                    <span class="snow-badge {status_class}">{request.status}</span>
                    <span style="color: #7f8c8d; font-size: 14px;">{request.department or 'N/A'}</span>
                    {'<span style="color: #7f8c8d; font-size: 12px; margin-left: 8px;">✨ AI Confidence: ' + str(confidence) + '%</span>' if has_ai else ''}
                </div>
                <div class="snow-card-footer">
                    <span style="color: #7f8c8d; font-size: 12px;">{time_created}</span>
                    <div class="snow-avatar">{request.requester_type[0] if request.requester_type else 'U'}</div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("No recent requests.")

elif st.session_state.current_page == 'Requests':
    # KPI Cards
    st.markdown("### Key Performance Indicators")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">Open Requests</div>
            <div class="snow-kpi-value">{open_requests}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">Avg Resolution Time</div>
            <div class="snow-kpi-value">4.2 hours</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">AI Accuracy</div>
            <div class="snow-kpi-value">97%</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(f"""
        <div class="snow-kpi">
            <div class="snow-kpi-label">SLA Compliance</div>
            <div class="snow-kpi-value">94%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Service Requests")
        
        if not filtered_requests:
            st.info("No requests match the current filters.")
        else:
            for request in filtered_requests:
                ai_info = st.session_state.ai_insights.get(request.id, {})
                confidence = ai_info.get('confidence', 85)
                priority_class = request.priority.lower() if request.priority else 'low'
                status_class = request.status.lower().replace('_', '_')
                time_created = time_ago(request.created_at) if request.created_at else "Unknown"
                has_ai = request.id in st.session_state.ai_insights
                
                # Department badge
                dept_badge = f'<span class="snow-badge" style="background: #3498db; color: white; margin-right: 8px;">{request.department or "N/A"}</span>'
                
                # Request card HTML
                card_html = f"""
                <div class="snow-card {priority_class}">
                    <div class="snow-req-number">
                        REQ{str(request.id).zfill(7)}
                        {'<span class="snow-ai-tag">✨ AI Suggested</span>' if has_ai else ''}
                    </div>
                    <div class="snow-req-title">{request.summary}</div>
                    <div style="margin-bottom: 12px;">
                        <span class="snow-badge {status_class}">{request.status}</span>
                        {dept_badge}
                        {'<span style="color: #7f8c8d; font-size: 12px; margin-left: 8px;">Confidence: ' + str(confidence) + '%</span>' if has_ai else ''}
                    </div>
                    <div class="snow-card-footer">
                        <span style="color: #7f8c8d; font-size: 12px;">{time_created}</span>
                        <div class="snow-avatar">{request.requester_type[0] if request.requester_type else 'U'}</div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Details in expander
                with st.expander(f"View Details - REQ{str(request.id).zfill(7)}"):
                    st.write(f"**Summary:** {request.summary}")
                    st.write(f"**Description:** {request.description}")
                    st.write(f"**Department:** {request.department or 'N/A'}")
                    st.write(f"**Category:** {request.category or 'N/A'}")
                    st.write(f"**Priority:** {request.priority or 'N/A'}")
                    st.write(f"**Status:** {request.status}")
                    st.write(f"**Channel:** {request.channel}")
                    st.write(f"**Requester Type:** {request.requester_type}")
                    if request.created_at:
                        st.write(f"**Created:** {request.created_at}")
                    
                    # AI Classification Details
                    if ai_info:
                        with st.expander("✨ Now Assist AI - Why this classification?"):
                            st.write(f"**AI Confidence:** {confidence}%")
                            if ai_info.get('keywords_detected'):
                                st.write(f"**Keywords Detected:** {', '.join(ai_info['keywords_detected'][:10])}")
                            if ai_info.get('department_reason'):
                                st.write(f"**Department Routing:** {ai_info['department_reason']}")
                            if ai_info.get('priority_reason'):
                                st.write(f"**Priority Reasoning:** {ai_info['priority_reason']}")
                    
                    # Advance Workflow button
                    if st.button(f"Advance Workflow", key=f"advance_{request.id}"):
                        new_status = advance_workflow(request.status)
                        request.status = new_status
                        request.updated_at = datetime.now().isoformat()
                        st.rerun()
    
    with col2:
        st.markdown("### Create New Request")
        
        with st.form("new_request_form"):
            st.markdown('<label class="snow-form-label">Channel</label>', unsafe_allow_html=True)
            channel = st.selectbox("", ["Resident Portal", "Phone", "Walk-in"], label_visibility="collapsed")
            
            st.markdown('<label class="snow-form-label">Requester Type</label>', unsafe_allow_html=True)
            requester_type = st.selectbox("", ["Resident", "Employee"], label_visibility="collapsed", key="req_type")
            
            st.markdown('<label class="snow-form-label">Summary</label>', unsafe_allow_html=True)
            summary = st.text_input("", placeholder="Enter request summary", label_visibility="collapsed")
            
            st.markdown('<label class="snow-form-label">Description</label>', unsafe_allow_html=True)
            description = st.text_area("", placeholder="Enter detailed description", label_visibility="collapsed", height=100)
            
            submitted = st.form_submit_button("Submit Request", use_container_width=True)
            
            if submitted:
                if summary and description:
                    max_id = max([req.id for req in st.session_state.requests], default=0)
                    new_id = max_id + 1
                    
                    with st.spinner("🔄 Now Assist AI analyzing request..."):
                        classification = classify_request(summary, description, channel)
                    
                    st.success("✅ AI Classification Complete")
                    
                    confidence = classification.get('confidence', 85)
                    st.info(
                        f"**Detected:** {classification['department']} | "
                        f"Priority: {classification['priority']} | "
                        f"Confidence: {confidence}%"
                    )
                    
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
                    st.session_state.ai_insights[new_id] = classification
                    st.session_state.ai_routed_today += 1
                    
                    st.success(f"Request REQ{str(new_id).zfill(7)} created successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in both summary and description.")

elif st.session_state.current_page == 'Analytics':
    st.markdown("### Analytics Dashboard")
    
    if st.session_state.requests:
        df = pd.DataFrame([req.dict() for req in st.session_state.requests])
        
        # Pie chart: Requests by Department
        if 'department' in df.columns:
            dept_counts = df['department'].value_counts()
            if not dept_counts.empty:
                fig_dept = px.pie(
                    values=dept_counts.values,
                    names=dept_counts.index,
                    title="Requests by Department",
                    color_discrete_sequence=['#62d84e', '#3498db', '#e67e22', '#9b59b6', '#95a5a6']
                )
                st.plotly_chart(fig_dept, use_container_width=True)
        
        # Bar charts side by side
        col3, col4 = st.columns(2)
        
        with col3:
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                if not status_counts.empty:
                    fig_status = px.bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        title="Requests by Status",
                        labels={'x': 'Status', 'y': 'Count'},
                        color_discrete_sequence=['#62d84e']
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
        
        with col4:
            if 'priority' in df.columns:
                priority_counts = df['priority'].value_counts()
                if not priority_counts.empty:
                    fig_priority = px.bar(
                        x=priority_counts.index,
                        y=priority_counts.values,
                        title="Requests by Priority",
                        labels={'x': 'Priority', 'y': 'Count'},
                        color=priority_counts.index,
                        color_discrete_map={'High': '#e74c3c', 'Medium': '#f39c12', 'Low': '#62d84e'}
                    )
                    st.plotly_chart(fig_priority, use_container_width=True)
    else:
        st.info("No requests available for analytics.")

elif st.session_state.current_page == 'AI Insights':
    st.markdown("### ✨ Now Assist AI Insights")
    
    total_ai = len([r for r in st.session_state.requests if r.id in st.session_state.ai_insights])
    avg_confidence = sum([st.session_state.ai_insights[r.id].get('confidence', 0) 
                          for r in st.session_state.requests if r.id in st.session_state.ai_insights]) / total_ai if total_ai > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total AI Classifications", total_ai)
    with col2:
        st.metric("Average Confidence", f"{avg_confidence:.1f}%")
    with col3:
        st.metric("Classification Speed", "0.3s avg")
    
    st.markdown("---")
    st.markdown("### AI Classification Details")
    
    for request in st.session_state.requests:
        if request.id in st.session_state.ai_insights:
            ai_info = st.session_state.ai_insights[request.id]
            with st.expander(f"REQ{str(request.id).zfill(7)} - {request.summary}"):
                st.write(f"**Confidence:** {ai_info.get('confidence', 0)}%")
                if ai_info.get('keywords_detected'):
                    st.write(f"**Keywords:** {', '.join(ai_info['keywords_detected'])}")
                if ai_info.get('department_reason'):
                    st.write(f"**Department:** {ai_info['department_reason']}")
                if ai_info.get('priority_reason'):
                    st.write(f"**Priority:** {ai_info['priority_reason']}")

elif st.session_state.current_page == 'Settings':
    st.markdown("### Settings")
    st.info("Settings configuration coming soon.")

# Footer
st.markdown("""
<div class="snow-footer">
    <p>✨ Powered by Now Assist AI</p>
</div>
""", unsafe_allow_html=True)

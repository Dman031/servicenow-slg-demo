# ServiceNow State & Local Government Demo

**AI-Powered Service Request Management**

---

## The Problem

Cities and counties receive thousands of service requests daily through multiple channels—phone calls, emails, walk-ins, and resident portals. Without a unified system, requests get lost in inboxes, manually routed by staff, and often take days to reach the right department. Residents have no visibility into request status, leading to frustration and duplicate submissions. Department silos prevent cross-functional collaboration, and leadership lacks real-time visibility into service delivery performance.

---

## The Solution

An AI-powered service request management platform that automatically classifies, prioritizes, and routes requests to the appropriate department in real-time. Built on ServiceNow principles, this solution transforms manual, reactive processes into automated, data-driven operations that improve response times, reduce administrative burden, and enhance resident satisfaction.

---

## Demo Features

- **AI Classification** - ServiceNow's "Now Assist" AI analyzes request content to automatically determine priority, category, and department routing
- **Workflow Engine** - Track requests through complete lifecycle: NEW → TRIAGE → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
- **Department Dashboards** - Real-time views for Public Works, Licensing, IT, HR, and General Services with filtering and metrics
- **Executive Analytics** - Interactive charts showing request distribution by department, status, and priority for data-driven decision making
- **Audit Trail** - Every action automatically timestamped and logged for compliance reporting and performance measurement

---

## Departments Supported

- **Public Works** - Infrastructure requests (potholes, streetlights, trash pickup, sidewalks)
- **Licensing** - Business permits, licenses, and zoning inquiries
- **IT** - Employee technology support (laptops, passwords, VPN, email)
- **HR** - Human resources inquiries (payroll, benefits, vacation)
- **General Services** - Miscellaneous resident and employee requests

---

## Quick Demo

```bash
git clone https://github.com/Dman031/servicenow-slg-demo.git
cd servicenow-slg-demo
pip install -r requirements.txt
streamlit run dashboard/app.py
```

The dashboard will open in your browser with 8 pre-loaded sample requests demonstrating AI classification across all departments.

---

## Included Documents

- **Problem Statement** (`docs/problem-statement-slg.md`) - Comprehensive analysis of current state challenges facing State & Local Government agencies
- **Discovery Questions** (`docs/discovery-workshop-slg.md`) - Structured workshop framework with 24 questions across 6 key areas
- **Demo Script** (`docs/demo-script-slg.md`) - 10-minute presentation guide for IT directors and executives
- **JD Alignment** (`docs/jd-alignment.md`) - Maps project deliverables to ServiceNow Solution Consultant job responsibilities

---

## Business Value

**For Residents:**
- Faster response times through automated routing
- Real-time status visibility reduces follow-up calls
- Consistent service delivery across all channels

**For Staff:**
- Reduced administrative time (no manual classification)
- Clear prioritization and workload visibility
- Cross-departmental collaboration capabilities

**For Leadership:**
- Real-time dashboards for data-driven decisions
- Automated compliance reporting and audit trails
- Performance metrics to measure against SLAs

---

## Screenshot

*[Dashboard screenshot here]*

---

**Built for ServiceNow Solution Consultants** - This demo showcases AI integration, workflow automation, and public sector domain expertise required for State & Local Government solution sales.

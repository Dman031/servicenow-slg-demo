"""AI-powered request classification and routing for ServiceNow State & Local Government."""

from typing import Dict, List


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


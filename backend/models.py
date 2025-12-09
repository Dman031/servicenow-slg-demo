from typing import Optional
from pydantic import BaseModel


class ServiceRequest(BaseModel):
    """Service Request model for State & Local Government."""
    
    id: int
    channel: str  # e.g., 'Resident Portal', 'Phone', 'Walk-in'
    requester_type: str  # 'Resident' or 'Employee'
    department: Optional[str] = None
    summary: str
    description: str
    status: str = 'NEW'
    priority: Optional[str] = None  # 'High', 'Medium', 'Low'
    category: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "channel": "Resident Portal",
                "requester_type": "Resident",
                "department": "Public Works",
                "summary": "Pothole on Main Street",
                "description": "Large pothole on Main Street near intersection with Oak Avenue",
                "status": "NEW",
                "priority": "High",
                "category": "Infrastructure",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


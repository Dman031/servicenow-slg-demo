"""Workflow management for ServiceNow State & Local Government service requests."""

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


from fastapi import APIRouter, Query, HTTPException # Added HTTPException
from typing import List, Dict, Any, Optional # Added for type hinting
from pydantic import BaseModel # For potential response models

# Assuming audit_logger is correctly imported from your core logic
# This path might need adjustment based on your actual core.audit structure
from core.audit import audit_logger, AuditLogEntry # AuditLogEntry for response model typing

router = APIRouter(prefix="/audit", tags=["audit"])

# Define a Pydantic model for the response of /log if AuditLogEntry.to_dict() isn't directly usable
# or if you want to strictly type the response structure.
# For now, assuming AuditLogEntry.to_dict() returns a structure compatible with client needs.
# If a specific structure is needed for the API response, define it here.
class AuditEntryResponse(BaseModel):
    entry_id: str
    entry_hash: str
    timestamp: float
    event_type: str
    layer: int
    details: Dict[str, Any]
    persona: Optional[str]
    confidence: Optional[float]
    forked_from: Optional[str]
    certificate: Optional[Dict[str, Any]]

class AuditBundleResponse(BaseModel):
    bundle_id: str
    generated_at: float
    count: int
    entries: List[AuditEntryResponse]

@router.get("/log", response_model=List[AuditEntryResponse])
def get_audit_log(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    layer: Optional[int] = Query(None, description="Filter by layer number"),
    persona: Optional[str] = Query(None, description="Filter by persona"),
    after_ts: Optional[float] = Query(0.0, description="Get logs after this UNIX timestamp"),
    limit: Optional[int] = Query(100, description="Maximum number of log entries to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    # audit_logger.query is from Subtask 6 blueprint
    # It returns List[Dict] where each dict is entry.to_dict()
    log_dicts = audit_logger.query(
        event_type=event_type,
        layer=layer,
        persona=persona,
        after_ts=after_ts,
        limit=limit,
        offset=offset
    )
    return [AuditEntryResponse(**entry_dict) for entry_dict in log_dicts]

@router.get("/bundle", response_model=AuditBundleResponse)
def get_audit_bundle(
    after_ts: Optional[float] = Query(0.0, description="Get logs for bundle after this UNIX timestamp")
):
    # audit_logger.snapshot_bundle is from Subtask 6 blueprint
    # It returns a dict with bundle_id, generated_at, count, entries (List[Dict])
    bundle_dict = audit_logger.snapshot_bundle(since_ts=after_ts)
    # Convert entries from List[Dict] to List[AuditEntryResponse]
    bundle_dict["entries"] = [AuditEntryResponse(**entry_dict) for entry_dict in bundle_dict["entries"]]
    return AuditBundleResponse(**bundle_dict)

@router.get("/entry/{entry_id}", response_model=Optional[AuditEntryResponse])
def get_log_entry(entry_id: str):
    # audit_logger.get_by_id is from Subtask 6 blueprint
    # It returns entry.to_dict() or None
    entry_dict = audit_logger.get_by_id(entry_id)
    if entry_dict:
        return AuditEntryResponse(**entry_dict)
    return None # Will result in 404 if not found, or 200 with null if Optional is handled by FastAPI like that.
                # Consider raising HTTPException(404) explicitly if preferred.

@router.post("/clear", response_model=Dict[str, bool]) # Changed to POST as it's a modifying action
def clear_audit(): # Subtask 6 API example uses POST for clear.
    audit_logger.clear()
    return {"ok": True, "message": "Audit log cleared"}

# Note: The Subtask 6 blueprint shows `audit_logger.clear()` and `audit_logger.snapshot_bundle(since_ts)`.
# It also shows `audit_logger.query(...)` and `audit_logger.get_by_id(entry_id)`.
# Pydantic models are added here for explicit response typing. 
from fastapi import APIRouter, Query, HTTPException # Added HTTPException
from typing import Dict, List, Any # Added List, Any for type hinting
from models.trace import TraceLogEntry
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trace", tags=["trace"])

# Shared in-memory for traces per run/session (as per Subtask 7 blueprint)
# Key: run_id (str), Value: List of TraceLogEntry dicts
trace_log_db: Dict[str, List[Dict[str, Any]]] = {}

@router.get("/get/{run_id}")
def get_trace(run_id: str):
    """Get trace entries for a run/session ID"""
    logger.info(f"Fetching traces for run_id: {run_id}")
    logger.info(f"Available trace keys: {list(trace_log_db.keys())}")
    
    trace_entries_dicts = trace_log_db.get(run_id)
    if trace_entries_dicts is None:
        logger.warning(f"No traces found for run_id: {run_id}")
        # Initialize empty trace for new session
        trace_log_db[run_id] = []
        return []
    
    try:
        # Convert list of dicts to list of TraceLogEntry models for response validation
        logger.info(f"Returning {len(trace_entries_dicts)} trace entries for {run_id}")
        return [TraceLogEntry(**entry) for entry in trace_entries_dicts]
    except Exception as e:
        logger.error(f"Error validating trace entries for {run_id}: {e}")
        # Return the raw entries if validation fails (for debugging)
        return trace_entries_dicts

@router.get("/all_runs", response_model=Dict[str, List[TraceLogEntry]]) # Adjusted response model
def list_all_traces():
    # Convert dict values (lists of dicts) to lists of TraceLogEntry models
    response_data = {}
    for run_id, entries_dicts in trace_log_db.items():
        response_data[run_id] = [TraceLogEntry(**entry) for entry in entries_dicts]
    return response_data

@router.post("/add/{run_id}", response_model=Dict[str, bool]) # Explicit response model
def add_trace(run_id: str, trace: TraceLogEntry):
    # Ensure the run_id key exists, initialize with empty list if not
    if run_id not in trace_log_db:
        trace_log_db[run_id] = []
    trace_log_db[run_id].append(trace.dict())
    return {"ok": True}

# Consider adding an endpoint to clear traces for a run_id or all traces for testing/management
@router.delete("/clear/{run_id}", response_model=Dict[str, bool])
def clear_trace_for_run(run_id: str):
    if run_id in trace_log_db:
        del trace_log_db[run_id]
        return {"ok": True, "message": f"Trace for run_id {run_id} cleared."}
    raise HTTPException(status_code=404, detail=f"Trace for run_id {run_id} not found.")

@router.delete("/clear_all", response_model=Dict[str, bool])
def clear_all_traces():
    trace_log_db.clear()
    return {"ok": True, "message": "All traces cleared."}

@router.get("/debug/all_keys")
def debug_all_keys():
    """Debug endpoint to see all trace keys and counts"""
    return {
        "total_sessions": len(trace_log_db),
        "sessions": {
            key: len(value) if isinstance(value, list) else "invalid"
            for key, value in trace_log_db.items()
        }
    } 
from fastapi import APIRouter, Query, HTTPException # Added HTTPException
from typing import Dict, List, Any # Added List, Any for type hinting
from models.trace import TraceLogEntry

router = APIRouter(prefix="/trace", tags=["trace"])

# Shared in-memory for traces per run/session (as per Subtask 7 blueprint)
# Key: run_id (str), Value: List of TraceLogEntry dicts
trace_log_db: Dict[str, List[Dict[str, Any]]] = {}

@router.get("/get/{run_id}", response_model=List[TraceLogEntry])
def get_trace(run_id: str):
    trace_entries_dicts = trace_log_db.get(run_id)
    if trace_entries_dicts is None:
        # Return empty list if run_id not found, as per typical API behavior for lists
        # Or raise HTTPException(status_code=404, detail="Trace for run_id not found") if preferred
        return [] 
    # Convert list of dicts to list of TraceLogEntry models for response validation
    return [TraceLogEntry(**entry) for entry in trace_entries_dicts]

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
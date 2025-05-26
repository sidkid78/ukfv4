from fastapi import APIRouter, HTTPException, Body # Added Body for List[float] in GET query
from typing import List, Any, Dict, Optional # Added Optional for response model
from models.memory import MemoryPatch, MemoryCell # Import your Pydantic models
from core.memory import global_memory_graph # Import your actual memory instance

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/cell", response_model=Optional[MemoryCell]) # Response can be None if cell not found
def get_memory_cell(coordinate: str):
    # Query param `coordinate` will be a comma-separated string like "0.1,0.2,...". Needs parsing.
    try:
        coord_list = [float(c.strip()) for c in coordinate.split(',')]
        if len(coord_list) != 13: # Assuming 13 dimensions
            raise ValueError("Coordinate must have 13 dimensions.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid coordinate format: {e}. Expected comma-separated floats.")
    
    # The global_memory_graph.get method needs to be adapted 
    # if it expects List[float] and returns a MemoryCell-like dict or object.
    # Assuming global_memory_graph.get returns a dict that can be unpacked into MemoryCell
    cell_data = global_memory_graph.get(coord_list)
    if cell_data:
        # If global_memory_graph.get already returns a MemoryCell object, this is simpler.
        # For now, assuming it returns a dict compatible with MemoryCell model.
        return MemoryCell(**cell_data) 
    return None # FastAPI will return 200 with null body if None is returned with Optional response_model

@router.get("/dump", response_model=List[MemoryCell])
def dump_all_memory():
    # Assuming global_memory_graph.dump_cells returns a list of dicts or MemoryCell objects
    all_cells_data = global_memory_graph.dump_cells()
    # Ensure it's a list of MemoryCell models for response validation
    return [MemoryCell(**cell_data) if isinstance(cell_data, dict) else cell_data for cell_data in all_cells_data]

@router.post("/patch", response_model=Dict[str, bool]) # Or MemoryCell if you return the patched cell
def patch_memory(patch: MemoryPatch):
    # The global_memory_graph.patch method needs to be consistent with MemoryPatch model
    # Assuming it takes coordinate, value, and some metadata derived from patch.source and patch.notes.
    # Operation type (add, update, delete) from patch.operation needs to be handled.
    
    if patch.operation == "delete":
        # global_memory_graph.delete should exist if this operation is supported
        # global_memory_graph.delete(patch.coordinate)
        # For now, let's assume patch covers add/update. Delete might be a separate endpoint or method.
        # Placeholder: raise error if delete is attempted but not implemented in global_memory_graph.patch
        raise HTTPException(status_code=501, detail="Delete operation not fully implemented in this endpoint version.")
    else: # add or update
        # The blueprint for InMemoryKnowledgeGraph in Subtask 3 has a patch method:
        # patch(self, coord: List[float], value: Any, meta: Dict = None)
        # We need to map MemoryPatch fields to this.
        meta_info = {"source": patch.source, "notes": patch.notes, "operation": patch.operation}
        if patch.notes is None:
            del meta_info["notes"] # Avoid passing None if the underlying method expects absence
        
        global_memory_graph.patch(
            coord=patch.coordinate,
            value=patch.value,
            meta=meta_info
        )
    return {"ok": True}

# Consider adding endpoints for:
# - Deleting a memory cell explicitly
# - Getting memory stats (n_cells, etc.)
# - Clearing memory (for testing) 
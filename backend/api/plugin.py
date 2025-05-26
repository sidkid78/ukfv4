from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional # Added List for response model and Optional
from pydantic import BaseModel # Added BaseModel

# Assuming ka_registry is correctly imported from your core logic
# This path might need adjustment based on your actual core.plugin_loader structure
from core.plugin_loader import ka_registry 

router = APIRouter(prefix="/plugin", tags=["plugin"]) # As per blueprint: /plugin/ka

# The Subtask 7 blueprint shows /plugin/ka/list, /plugin/ka/reload, /plugin/ka/run/{ka_name}
# So the router prefix should ideally be /plugin/ka or routes should include /ka/
# For now, using /plugin and adding /ka in routes for clarity and adherence to blueprint example paths.

class KaMetaResponse(BaseModel):
    name: str
    meta: Dict[str, Any]

class KaListResponse(BaseModel):
    plugins: List[KaMetaResponse]

class KaRunPayload(BaseModel):
    slice_input: Dict[str, Any]
    context: Dict[str, Any]

class KaRunResponse(BaseModel):
    output: Optional[Any]
    confidence: Optional[float]
    entropy: Optional[float]
    trace: Optional[Any]

@router.get("/ka/list", response_model=List[Dict[str, Any]]) # Using List[Dict] for flexibility from blueprint
def list_kas():
    # ka_registry.get_ka_names() and ka_registry.get_ka_meta(name) are from Subtask 5 blueprint
    return [
        {"name": name, "meta": ka_registry.get_ka_meta(name)}
        for name in ka_registry.get_ka_names()
    ]

@router.post("/ka/reload", response_model=Dict[str, Any]) # Using Dict for flexibility
def reload_kas():
    # ka_registry.reload_plugins() is from Subtask 5 blueprint
    ka_registry.reload_plugins()
    return {"status": "reloaded", "available_plugins": ka_registry.get_ka_names()}

@router.post("/ka/run/{ka_name}", response_model=KaRunResponse) # More specific response model
def run_ka(ka_name: str, payload: KaRunPayload):
    # ka_registry.get_ka_names() and ka_registry.call_ka(...) are from Subtask 5 blueprint
    if ka_name not in ka_registry.get_ka_names():
        raise HTTPException(status_code=404, detail=f"Knowledge Algorithm '{ka_name}' not found")
    
    # The call_ka method from Subtask 5 blueprint:
    # call_ka(self, name: str, slice_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]
    # It returns a dict with output, confidence, entropy, trace, handling errors internally.
    result = ka_registry.call_ka(name=ka_name, slice_input=payload.slice_input, context=payload.context)
    return KaRunResponse(**result)

# Note: The blueprint for `core.plugin_loader.KARegistry` (Subtask 5) defines:
# - `get_ka_names(self)` -> `List[str]`
# - `get_ka_meta(self, name: str)` -> `ka["meta"] if ka else {}` (returns a dict)
# - `reload_plugins(self)` (was `load_plugins` and `reload_plugins` calling `load_plugins`)
# - `call_ka(self, name: str, slice_input: Dict, context: Dict)` -> `Dict` (with output, conf, entropy, trace)
# The Pydantic models KaMetaResponse, KaListResponse, KaRunPayload, KaRunResponse are added for better API clarity and validation.
# If these are not desired, the response_models can be changed to Dict[str, Any] or List[Dict[str, Any]]. 
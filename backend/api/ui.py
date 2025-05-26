from fastapi import APIRouter
from typing import List, Dict, Any # Added for type hinting
from pydantic import BaseModel # Added BaseModel

# Assuming LAYER_CLASSES is correctly imported from your core logic
# This path might need adjustment based on your actual core.layers structure
from core.layers import LAYER_CLASSES 

router = APIRouter(prefix="/ui", tags=["ui"])

class LayerInfo(BaseModel):
    number: int
    name: str

class UiStateResponse(BaseModel):
    axes_labels: List[str]
    layers_available: List[LayerInfo]

@router.get("/state", response_model=UiStateResponse) # Using specific response model
def get_ui_state():
    # LAYER_CLASSES from Subtask 2 blueprint (core/layers/__init__.py)
    # It's a list of layer class constructors (e.g., [Layer1SimulationEntry, ...])
    # We need instances to get layer_number and layer_name if they are instance attributes,
    # or access them as class attributes if they are defined that way.
    # Assuming layer_number and layer_name are class attributes as per Subtask 2 BaseLayer example.
    
    available_layers = []
    if LAYER_CLASSES: # Check if LAYER_CLASSES is populated
        for layer_class in LAYER_CLASSES:
            try:
                # Attempt to access as class attributes
                num = layer_class.layer_number
                name = layer_class.layer_name
                available_layers.append(LayerInfo(number=num, name=name))
            except AttributeError:
                # Fallback: try instantiating if attributes are on instance (less ideal for this kind of info)
                # This might fail if __init__ requires args.
                try:
                    instance = layer_class()
                    available_layers.append(LayerInfo(number=instance.layer_number, name=instance.layer_name))
                except Exception as e:
                    # Log this issue, as it indicates a problem with layer class definition or this endpoint's logic
                    print(f"Error processing layer {layer_class.__name__} for UI state: {e}")
                    available_layers.append(LayerInfo(number=-1, name=f"Error: {layer_class.__name__}"))

    return UiStateResponse(
        axes_labels=[f"Axis_{i + 1}" for i in range(13)], # As per blueprint
        layers_available=available_layers
    )

# The blueprint also mentions /layer_status. 
# This could return dynamic status if layers can be active/inactive.
# For now, /state provides the available layers.
@router.get("/layer_status", response_model=List[LayerInfo]) # Example, mirrors layers_available for now
def get_layer_status():
    # This is similar to layers_available in /state. 
    # If dynamic status (active/inactive) is a feature, this endpoint would be more distinct.
    layers_status = []
    if LAYER_CLASSES:
        for layer_class in LAYER_CLASSES:
            try:
                layers_status.append(LayerInfo(number=layer_class.layer_number, name=layer_class.layer_name))
            except AttributeError:
                 layers_status.append(LayerInfo(number=-1, name=f"Error: {layer_class.__name__}"))

    return layers_status 
from fastapi import APIRouter, HTTPException, Body
from typing import List 
from models.axis import AxisMetadata, AxisCoordinate, CoordParseRequest, NameToCoordRequest, NameToCoordResponse, AXES, AXIS_KEY_MAP, AXIS_KEYS 

router = APIRouter(prefix="/axis", tags=["Axis Metadata"])

@router.get("/", response_model=List[AxisMetadata])
async def get_all_axes_metadata():
    return AXES 

@router.get("/{axis_key}", response_model=AxisMetadata)
async def get_single_axis_metadata(axis_key: str):
    axis_info = AXIS_KEY_MAP.get(axis_key)
    if not axis_info:
        raise HTTPException(status_code=404, detail=f"Axis key '{axis_key}' not found")
    return axis_info

@router.post("/parse", response_model=AxisCoordinate, tags=["Coordinate Operations"])
async def parse_nuremberg_coordinate_string(request: CoordParseRequest = Body(...)):
    """
    Parses and validates a 13-part pipe-delimited Nuremberg coordinate string 
    into an AxisCoordinate object.
    """
    parts = request.coordinate.split("|")
    if len(parts) != 13:
        raise HTTPException(
            status_code=400, 
            detail=f"Coordinate string must have exactly 13 parts separated by '|'. Received {len(parts)} parts."
        )
    
    coord_data_raw = {}
    for i, key in enumerate(AXIS_KEYS):
        part_value = parts[i]
        if key == "honeycomb":
            coord_data_raw[key] = [s.strip() for s in part_value.split(",")] if part_value else None
        elif key not in ["pillar", "sector"]:
             coord_data_raw[key] = part_value if part_value else None
        else: # pillar and sector
            coord_data_raw[key] = part_value
            if key == "sector": # Try to convert sector to int if it's numeric, else keep as string
                try:
                    coord_data_raw[key] = int(part_value)
                except ValueError:
                    pass # Keep as string if not a simple integer

    try:
        axis_coord_obj = AxisCoordinate(**coord_data_raw)
        return axis_coord_obj
    except ValueError as e: 
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/translate", response_model=NameToCoordResponse, tags=["Coordinate Operations"])
async def translate_names_to_coordinate(data: NameToCoordRequest = Body(...)):
    """
    Translates human-readable names/tags for various axes into a structured 
    13D AxisCoordinate. Uses example lookup maps for demonstration.
    """
    log = []
    
    # --- Pillar ---
    # Pillar is mandatory. If name provided, translate; otherwise, use a default or raise error.
    # For this example, if pillar_name is not given, we'll default to "PL01"
    # but in a real system, this might be an error or require more context.
    if data.pillar_name:
        pillar_code = EXAMPLE_PILLAR_NAMES.get(data.pillar_name)
        if pillar_code:
            log.append(f"Pillar name '{data.pillar_name}' translated to code '{pillar_code}'.")
        else:
            # Assuming if not in map, the name itself is the code (e.g. "PLxx.x")
            # Or, you could raise an error if strict mapping is required.
            pillar_code = data.pillar_name 
            log.append(f"Pillar name '{data.pillar_name}' used as code (not found in example map). Validating format.")
    else:
        pillar_code = "PL01" # Default pillar if not provided
        log.append(f"No pillar_name provided, defaulted to '{pillar_code}'.")

    # --- Sector ---
    # Sector is mandatory. Similar logic to pillar.
    if data.sector_name:
        sector_code = EXAMPLE_SECTOR_CODES.get(data.sector_name)
        if sector_code:
            log.append(f"Sector name '{data.sector_name}' translated to code '{sector_code}'.")
        else:
            sector_code = data.sector_name # Assume name is code if not in map
            log.append(f"Sector name '{data.sector_name}' used as code (not found in example map).")
    else:
        sector_code = "0000" # Default sector if not provided (adjust as needed)
        log.append(f"No sector_name provided, defaulted to '{sector_code}'.")

    # --- Derived fields based on Pillar and Sector ---
    honeycomb_links = [f"{pillar_code}↔{str(sector_code)}"] if pillar_code and sector_code else None
    log.append(f"Derived honeycomb: {honeycomb_links}")
    
    # Branch: Try to derive from pillar_name if available in example map
    branch_code = EXAMPLE_BRANCHES.get(data.pillar_name) if data.pillar_name else None
    if branch_code:
        log.append(f"Derived branch for pillar '{data.pillar_name}': '{branch_code}'.")
    else:
        log.append(f"No example branch mapping found for pillar '{data.pillar_name}'. Branch set to None.")

    node_code = f"N-{pillar_code}-{str(sector_code)}" if pillar_code and sector_code else None
    log.append(f"Derived node: {node_code}")

    # --- Regulatory & Compliance ---
    regulatory_code = None
    if data.regulatory_name:
        regulatory_code = EXAMPLE_REGULATORY.get(data.regulatory_name)
        if regulatory_code:
            log.append(f"Regulatory name '{data.regulatory_name}' translated to code '{regulatory_code}'.")
        else:
            regulatory_code = data.regulatory_name # Assume name is code
            log.append(f"Regulatory name '{data.regulatory_name}' used as code.")
    
    compliance_code = None
    if data.compliance_name:
        compliance_code = EXAMPLE_COMPLIANCE.get(data.compliance_name)
        if compliance_code:
            log.append(f"Compliance name '{data.compliance_name}' translated to code '{compliance_code}'.")
        else:
            compliance_code = data.compliance_name # Assume name is code
            log.append(f"Compliance name '{data.compliance_name}' used as code.")

    # --- Construct AxisCoordinate ---
    # Ensure sector_code is of the correct type for Pydantic model (Union[str, int])
    # If sector_code from EXAMPLE_SECTOR_CODES is numeric string, convert to int if possible
    final_sector_code = sector_code
    try:
        final_sector_code = int(sector_code)
    except (ValueError, TypeError):
        pass # Keep as string if not a simple integer or if it's None

    try:
        axis_coord_obj = AxisCoordinate(
            pillar=pillar_code,
            sector=final_sector_code, # Use the potentially converted sector_code
            honeycomb=honeycomb_links,
            branch=branch_code,
            node=node_code,
            regulatory=regulatory_code,
            compliance=compliance_code,
            role_knowledge=data.role_knowledge,
            role_sector=data.role_sector,
            role_regulatory=data.role_regulatory,
            role_compliance=data.role_compliance,
            location=data.location,
            temporal=data.temporal
        )
    except ValueError as e: # Catch Pydantic validation errors
        raise HTTPException(status_code=422, detail=f"Validation error creating AxisCoordinate: {str(e)}")

    return NameToCoordResponse(
        axis_coordinate=axis_coord_obj,
        nuremberg_13d=axis_coord_obj.as_nuremberg(),
        unified_system_id=axis_coord_obj.generate_unified_system_id(),
        translation_log=log
    )

# ========== SAMPLE LOOKUP DATA (for /axis/translate demo) ==========
EXAMPLE_PILLAR_NAMES = {
    "Physics": "PL12.2.1",
    "AI Safety": "PL09.3.2",
    "Bioinformatics": "PL25.6.1"
}
EXAMPLE_SECTOR_CODES = { # Name to Code
    "Healthcare": "6215", # Using string for consistency with Pydantic model
    "Manufacturing": "3345",
    "Software": "5415"
}
EXAMPLE_BRANCHES = { # Pillar Name to Branch Code
    "Physics": "5417.100/physics", # Example, actual mapping would be more complex
    "AI Safety": "5417.800/ai-safety",
    "Bioinformatics": "5417.150/bioinformatics"
}
EXAMPLE_REGULATORY = { # Name to Code
    "GDPR": "GDPR-ART5",
    "HIPAA": "HIPAA-164",
    "CFR": "CFR40.122"
}
EXAMPLE_COMPLIANCE = { # Name to Code
    "ISO 9001": "ISO9001",
    "SOC2": "SOC2"
}





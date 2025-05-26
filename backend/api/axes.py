from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator 
import datetime
import re
from hashlib import sha256

# ========== AXIS DEFINITIONS (from previous step) ==========
class AxisMetadata(BaseModel):
    index: int
    key: str
    name: str
    description: str
    formula: str
    coordinate_rule: str

AXES: List[AxisMetadata] = [
    AxisMetadata(index=1, key="pillar", name="Pillar Level System",
      description="Universal knowledge architecture: Pillar Levels (PLxx), sublevels",
      formula="PLxx.x.x (e.g. PL12.3.1); P(x1) = Σ(wᵢ * pᵢ)",
      coordinate_rule="Hierarchical: major.sub1.sub2"),
    AxisMetadata(index=2, key="sector", name="Sector of Industry",
      description="Industry/economic sector (NAICS, SIC, etc.)",
      formula="Integer domain code", coordinate_rule="Industry code"),
    AxisMetadata(index=3, key="honeycomb", name="Honeycomb System",
      description="Crosswalking grid/mesh between axes",
      formula="H(PL) = ⋃ᵢ=2¹³ Aᵢ ∩ PLₓ.y.z", coordinate_rule="Set of axis crosslinks"),
    AxisMetadata(index=4, key="branch", name="Branch System",
      description="Taxonomy/economic/disciplinary lineage (e.g., parent/child codes)",
      formula="Parent/child code chains", coordinate_rule="Branch path code"),
    AxisMetadata(index=5, key="node", name="Node System",
      description="Cross-sector nodes; convergence overlays",
      formula="Node ids; node ↔ PL/sector mapping", coordinate_rule="Node id(s)"),
    AxisMetadata(index=6, key="regulatory", name="Regulatory/Octopus Node",
      description="Legal/regulatory frameworks (CFR, GDPR, etc.)",
      formula="Regulatory code or jurisdiction id", coordinate_rule="E.g. CFR Title"),
    AxisMetadata(index=7, key="compliance", name="Compliance/Spiderweb Node",
      description="Standards/compliance framework mapping (ISO, NIST, ...)",
      formula="Compliance code/type", coordinate_rule="E.g. ISO 9001, FedRAMP"),
    AxisMetadata(index=8, key="role_knowledge", name="Knowledge Role/Persona",
      description="Persona by job, education, skill", formula="Role, job code, PL mapping",
      coordinate_rule="Freeform"),
    AxisMetadata(index=9, key="role_sector", name="Sector Expert Role/Persona",
      description="Domain (industry) expert persona", formula="Role, sector/industry mapping",
      coordinate_rule="Freeform"),
    AxisMetadata(index=10, key="role_regulatory", name="Regulatory Expert Role/Persona",
      description="Regulatory (government/compliance) role",
      formula="Role, regulatory code, provision branch", coordinate_rule="Freeform"),
    AxisMetadata(index=11, key="role_compliance", name="Compliance Expert Role/Unified",
      description="Compliance expert or Unified System ID (USI)",
      formula="SHA256(SAM_ID+NASA_ID+PL_ID)", coordinate_rule="Hash/Composite ID"),
    AxisMetadata(index=12, key="location", name="Location",
      description="Geospatial/region anchor (country, state, etc.)",
      formula="ISO 3166 geo code", coordinate_rule="E.g. US-CA, IN-MH"),
    AxisMetadata(index=13, key="temporal", name="Temporal",
      description="Time dimension: version, historical, window",
      formula="ISO 8601 date, datetime, or event id", coordinate_rule="Datetime or event id"),
]

AXIS_KEY_MAP: Dict[str, AxisMetadata] = {a.key: a for a in AXES}
AXIS_KEYS: List[str] = [a.key for a in AXES] 

# ========== 13D COORDINATE MODEL (from previous step) ==========
class AxisCoordinate(BaseModel):
    pillar: str = Field(..., example="PL15.1.3")
    sector: Union[str, int] = Field(..., example="5415") 
    honeycomb: Optional[List[str]] = Field(default=None, example=["PL15.1.3↔5415"])
    branch: Optional[str] = Field(default=None)
    node: Optional[str] = Field(default=None)
    regulatory: Optional[str] = Field(default=None)
    compliance: Optional[str] = Field(default=None)
    role_knowledge: Optional[str] = Field(default=None)
    role_sector: Optional[str] = Field(default=None)
    role_regulatory: Optional[str] = Field(default=None)
    role_compliance: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    temporal: Optional[str] = Field(default=None)

    @validator("pillar")
    def validate_pillar_format(cls, v):
        if not v: 
            raise ValueError("Pillar cannot be empty")
        if not re.match(r'^PL\d{1,2}(\.\d+){0,2}$', v):
            raise ValueError("Pillar must be in PLxx, PLxx.x, or PLxx.x.x format (e.g., PL12.3.1 or PL01)")
        return v

    @validator("sector")
    def validate_sector_format(cls, v):
        if not v: 
            raise ValueError("Sector cannot be empty")
        if isinstance(v, str) and not v.strip():
            raise ValueError("Sector string cannot be empty or just whitespace")
        return v

    @validator("temporal")
    def validate_temporal_format(cls, v):
        if v is None or v == "": 
            return None
        try:
            datetime.datetime.fromisoformat(v.replace("Z", "+00:00")) 
            return v
        except ValueError:
            try:
                datetime.date.fromisoformat(v)
                return v 
            except ValueError:
                if not re.match(r'^[A-Za-z0-9\-\s_:]+$', v): 
                    raise ValueError("Temporal must be a valid ISO 8601 datetime, date, or an event ID string.")
                return v
        return v

    def as_list(self) -> list:
        return [getattr(self, key, None) or "" for key in AXIS_KEYS]

    def as_dict(self) -> dict:
        return {key: getattr(self, key, None) for key in AXIS_KEYS}

    def as_nuremberg(self) -> str:
        parts = []
        for key in AXIS_KEYS:
            value = getattr(self, key, None)
            if isinstance(value, list): 
                parts.append(",".join(map(str, value)) if value else "")
            else:
                parts.append(str(value) if value is not None else "")
        return "|".join(parts)

    def generate_unified_system_id(self) -> str:
        pillar_val = self.pillar or ""
        sector_val = str(self.sector) if self.sector is not None else ""
        location_val = self.location or ""
        id_str = f"{pillar_val}|{sector_val}|{location_val}"
        return sha256(id_str.encode("utf-8")).hexdigest()

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

# ========== FASTAPI APP (from previous step) ==========
app = FastAPI(
    title="UKG/USKD 13-Axis System API",
    description="API for the multidimensional knowledge graph Axis System (metadata, coordinate logic, name-to-coord, crosswalks, roles & math queries)",
    version="1.1.0",
    contact={"name": "Universal Knowledge Graph", "email": "ukg@ai-safety.org"}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= API ENDPOINTS ============

@app.get("/axis/", response_model=List[AxisMetadata], tags=["Axis Metadata"])
async def get_all_axes_metadata():
    """Get metadata and rules for all 13 axes."""
    return AXES

@app.get("/axis/{axis_key}", response_model=AxisMetadata, tags=["Axis Metadata"])
async def get_single_axis_metadata(axis_key: str):
    """Get metadata for a specific axis by its key (e.g., 'pillar')."""
    axis_info = AXIS_KEY_MAP.get(axis_key)
    if not axis_info:
        raise HTTPException(status_code=404, detail=f"Axis key '{axis_key}' not found")
    return axis_info

class CoordParseRequest(BaseModel):
    coordinate: str = Field(..., example="PL12.4.1|5417|PL12.4.1↔5417|5417.100/physics|N10243|CFR_40.122|ISO9001|Data Scientist|Science Expert|Regulatory-Agent-Env|Compliance-Auditor|US-CA|2024-06-01T12:00:00Z")

@app.post("/axis/parse", response_model=AxisCoordinate, tags=["Coordinate Operations"])
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

# --- NEW ENDPOINT for translating names/tags to coordinates ---
class NameToCoordRequest(BaseModel):
    pillar_name: Optional[str] = Field(default=None, example="AI Safety")
    sector_name: Optional[str] = Field(default=None, example="Software")
    regulatory_name: Optional[str] = Field(default=None, example="GDPR")
    compliance_name: Optional[str] = Field(default=None, example="SOC2")
    role_knowledge: Optional[str] = Field(default=None, example="AI Ethicist")
    role_sector: Optional[str] = Field(default=None, example="Tech Policy Analyst")
    role_regulatory: Optional[str] = Field(default=None, example="Data Protection Officer")
    role_compliance: Optional[str] = Field(default=None, example="Security Auditor")
    location: Optional[str] = Field(default=None, example="EU")
    temporal: Optional[str] = Field(default=None, example="2024-05-25T10:00:00Z")
    # Fields for honeycomb, branch, node are typically derived or more complex,
    # so not taking direct name inputs for them in this simple example.
    # They will be populated based on pillar/sector.

class NameToCoordResponse(BaseModel):
    axis_coordinate: AxisCoordinate
    nuremberg_13d: str
    unified_system_id: str
    translation_log: List[str] = Field(description="Log of how names were translated or defaulted.")

@app.post("/axis/translate", response_model=NameToCoordResponse, tags=["Coordinate Operations"])
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

# ========== HEALTH / DOCS (from previous step) ==========
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok", "time": datetime.datetime.now().isoformat(), "axes_defined": len(AXES)}

@app.get("/", include_in_schema=False)
async def root_path():
    return {"message": "UKG/USKD Axis API is running. See /docs for OpenAPI documentation."}

# To run this:
# 1. Save as a Python file (e.g., main.py)
# 2. Install FastAPI and Uvicorn: pip install fastapi uvicorn[standard]
# 3. Run with Uvicorn: uvicorn main:app --reload
# Then you can access the API at http://localhost:8000/docs
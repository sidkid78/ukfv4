from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, Union 
import datetime 
import re 
from hashlib import sha256 

# ========== AXIS DEFINITIONS ==========
class AxisMetadata(BaseModel):
    index: int 
    key: str 
    name: str 
    description: str 
    formula: str 
    coordinate_rule: str 

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

    @field_validator("pillar")
    def validate_pillar_format(cls, v):
        if not v: 
            raise ValueError("Pillar cannot be empty")
        if not re.match(r'^PL\d{1,2}(\.\d+){0,2}$', v):
            raise ValueError("Pillar must be in PLxx, PLxx.x, or PLxx.x.x format (e.g., PL12.3.1 or PL01)")
        return v

    @field_validator("sector")
    def validate_sector_format(cls, v):
        if not v: 
            raise ValueError("Sector cannot be empty")
        if isinstance(v, str) and not v.strip():
            raise ValueError("Sector string cannot be empty or just whitespace")
        return v

    @field_validator("temporal")
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
    
# ========== AXIS METADATA DEFINITIONS ==========

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

class CoordParseRequest(BaseModel):
    coordinate: str = Field(..., example="PL12.4.1|5417|PL12.4.1↔5417|5417.100/physics|N10243|CFR_40.122|ISO9001|Data Scientist|Science Expert|Regulatory-Agent-Env|Compliance-Auditor|US-CA|2024-06-01T12:00:00Z")

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
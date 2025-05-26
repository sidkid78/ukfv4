from pydantic import BaseModel
from typing import Dict, Optional, Any, List


class SimulationQuery(BaseModel):
    query: str
    session_id: str 
    context: dict | None = None
    axes: list[int] | None = None   # 13-dimensional coordinate for now can be incomplete 

    # Example method for serialization
    def to_dict(self):
        return self.model_dump() 
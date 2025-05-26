from threading import RLock
from typing import Any, Dict, Tuple, List, Optional, Set
import hashlib
import time
import copy

# Defines a 13D coordinate for simulation
Coordinate = Tuple[float, ...]

# Helper for coordinate hashing for memory indexing
def coordinate_hash(coord: List[float]) -> str:
    # Lossless but gives string key for dict
    # (You might want to round or quantize floats for stability!)
    data = ":".join(f"{x:.6f}" for x in coord)
    return hashlib.sha256(data.encode()).hexdigest()

class MemoryCell:
    def __init__(
        self,
        coordinate: Coordinate,
        value: Any,
        meta: Dict[str, Any] = None,
        parent_cell_id: Optional[str] = None
    ):
        self.coordinate: Coordinate = tuple(coordinate)
        self.value = value              # Main answer, knowledge data, etc.
        self.meta = meta or {}          # e.g. {'by': 'AgentA', 'persona': '', 'confidence': 0.97, ...}
        self.lineage: List[str] = []    # Patch/fork history (cell_ids)
        self.parent_cell_id = parent_cell_id
        self.memory_cell_id = self._generate_id()
        self.forks: Set[str] = set()    # For lineage (forked from here)
        self.created_at = time.time()
        self.last_modified = self.created_at
        self.entropy_log: List[Dict] = []
        self.patch_history: List[Dict] = []

    def _generate_id(self):
        # Unique per coordinate + creation
        return hashlib.sha256(
            f"{self.coordinate}-{self.created_at}".encode()
        ).hexdigest()

    def log_patch(self, patch: Dict[str, Any]):
        self.patch_history.append(
            {
                "timestamp": time.time(),
                **patch
            }
        )
        self.last_modified = time.time()

    def log_entropy(self, entry: Dict[str, Any]):
        self.entropy_log.append(
            {
                "timestamp": time.time(),
                **entry
            }
        )

    def fork(self, new_value: Any, meta: Dict[str, Any], reason: str = "fork"):
        # Make a lineage copy (returns a new MemoryCell)
        fork_cell = MemoryCell(
            coordinate=self.coordinate,
            value=new_value,
            meta=meta,
            parent_cell_id=self.memory_cell_id,
        )
        fork_cell.lineage = self.lineage + [self.memory_cell_id]
        self.forks.add(fork_cell.memory_cell_id)
        fork_cell.meta["fork_reason"] = reason
        return fork_cell

    def decay(self, entropy_delta: float):
        self.meta["entropy"] = self.meta.get("entropy", 0.0) + entropy_delta
        self.log_entropy({"type": "decay", "delta": entropy_delta})

    def patch(self, new_value: Any, meta: Dict[str, Any], patch_type="edit"):
        old_value = copy.deepcopy(self.value)
        self.value = new_value
        self.meta.update(meta)
        self.log_patch({
            "type": patch_type,
            "old_value": old_value,
            "new_value": new_value,
            "meta": meta,
        })
        return self

    def to_dict(self, recursive=False):
        # Serialize for logging/UI; follow forks if needed
        dct = {
            "coordinate": list(self.coordinate),
            "value": self.value,
            "meta": self.meta,
            "cell_id": self.memory_cell_id,
            "parent_cell_id": self.parent_cell_id,
            "lineage": self.lineage,
            "forks": list(self.forks),
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "entropy_log": self.entropy_log if recursive else None,
            "patch_history": self.patch_history if recursive else None,
        }
        return dct

class InMemoryKnowledgeGraph:
    """
    In-memory, concurrency-safe, 13-axis knowledge graph for UKG/USKD.
    Permits coordinate, persona/role, recursive/forking access, 
    patching and entropy/fork lineage logging.

    All knowledge is RAM-only. Testable and restartable.
    """
    def __init__(self):
        self.lock = RLock()
        self.cells: Dict[str, MemoryCell] = {}
        # Persona<>CellID and fork lineage maps for trace/drift
        self.persona_index: Dict[str, Set[str]] = {}
        self.cell_forks: Dict[str, Set[str]] = {} # child->parent(s)
        self.patch_log: List[Dict] = [] # global patch history

    ### --- Core Memory Retrieval/Mutation --- ###

    def get(self, coordinate: List[float], persona: Optional[str] = None) -> Optional[Dict]:
        key = coordinate_hash(coordinate)
        with self.lock:
            cell = self.cells.get(key)
            if cell:
                if persona:
                    # Optionally restrict to persona match
                    if cell.meta.get("persona") == persona:
                        return cell.to_dict()
                    else:
                        return None
                else:
                    return cell.to_dict()
            else:
                return None

    def set(self, coordinate: List[float], value: Any, meta: Dict[str, Any], persona: Optional[str] = None) -> Dict:
        key = coordinate_hash(coordinate)
        with self.lock:
            # Overwrite or create
            cell = self.cells.get(key)
            if cell:
                cell.patch(value, meta)
            else:
                cell = MemoryCell(coordinate=coordinate, value=value, meta=meta)
                self.cells[key] = cell

            # Map persona for lookup/search
            persona_id = persona or meta.get("persona")
            if persona_id:
                if persona_id not in self.persona_index:
                    self.persona_index[persona_id] = set()
                self.persona_index[persona_id].add(cell.memory_cell_id)
            return cell.to_dict()

    def patch(self, coordinate: List[float], value: Any, meta: Dict[str, Any], persona: Optional[str] = None) -> Dict:
        # Wrapper for mutation; logs to patch log
        patched = self.set(coordinate, value, meta, persona)
        self.patch_log.append({
            "coordinate": list(coordinate),
            "value": value,
            "meta": meta,
            "persona": persona or meta.get("persona"),
            "timestamp": time.time()
        })
        return patched

    def fork(self, coordinate: List[float], new_value: Any, meta: Dict[str, Any], reason="fork") -> Optional[Dict]:
        # Forks an existing cell (for unstable reasoning, forks, etc.)
        key = coordinate_hash(coordinate)
        with self.lock:
            cell = self.cells.get(key)
            if not cell:
                return None
            fork_cell = cell.fork(new_value, meta, reason=reason)
            # Store new fork as primary at same coordinate (optional)
            # If you want to keep both the original and the fork at the same coordinate,
            # you'll need a more complex structure, e.g., a list of cells per coordinate hash
            # or adjust the keying strategy for forks.
            # For now, this replaces the cell at the coordinate with the new fork.
            self.cells[coordinate_hash(coordinate)] = fork_cell 
            
            # Track fork lineage for audit/drift/fork detection
            self.cell_forks.setdefault(cell.memory_cell_id, set()).add(fork_cell.memory_cell_id)
            self.patch_log.append({
                "type": "fork", # Added type for clarity
                "fork_of": cell.memory_cell_id,
                "fork_new_id": fork_cell.memory_cell_id,
                "coordinate": list(coordinate), # Added coordinate for easier lookup
                "meta": meta,
                "timestamp": time.time(),
                "reason": reason,
            })
            return fork_cell.to_dict()

    def decay_cell(self, coordinate: List[float], entropy_delta=0.1):
        # Increase entropy value, logs change for analysis
        key = coordinate_hash(coordinate)
        with self.lock:
            cell = self.cells.get(key)
            if cell:
                cell.decay(entropy_delta)
                self.patch_log.append({
                    "coordinate": list(coordinate),
                    "type": "decay",
                    "delta": entropy_delta,
                    "timestamp": time.time(),
                })

    def find_by_persona(self, persona: str) -> List[Dict]:
        # Returns list of all cells mapped to a persona/role
        with self.lock:
            cell_ids = self.persona_index.get(persona, set())
            return [cell.to_dict() for cell in self.cells.values() if cell.memory_cell_id in cell_ids]

    def get_patch_log(self, since_ts: float = 0.0) -> List[Dict]:
        # Audit/all patches after time
        with self.lock:
            return [p for p in self.patch_log if p["timestamp"] >= since_ts]

    def dump_cells(self): # Renamed from all_cells for clarity with API
        # For dump/inspection
        with self.lock:
            return [cell.to_dict(recursive=True) for cell in self.cells.values()] # Added recursive=True for full dump

    def stats(self) -> Dict:
        # For monitoring/memory UI
        with self.lock:
            return {
                "n_cells": len(self.cells),
                "n_personas": len(self.persona_index),
                "n_forks": sum(len(forks) for forks in self.cell_forks.values()),
                "patches": len(self.patch_log)
            }

# Instantiate a global singleton memory engine
global_memory_graph = InMemoryKnowledgeGraph()

# For API/engine use:
def get_memory(): # This function was in the blueprint, but seems redundant if global_memory_graph is directly imported.
    return global_memory_graph 
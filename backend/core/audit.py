import json
import threading
import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Literal # Added Literal

class AuditLogEntry:
    """
    Represents a single audit entry: patch, fork, agent decision, escalation, containment, etc.
    """
    def __init__(
        self,
        event_type: Literal[
            "simulation_pass", "memory_patch", "fork", "agent_decision",
            "escalation", "containment_trigger", "compliance_violation", "cert", "simulation_start", "simulation_end" # Added sim start/end
        ],
        layer: Optional[int], # Layer can be None for non-layer-specific events like sim_start/end
        details: Dict[str, Any],
        simulation_id: Optional[str] = None, # Added simulation_id to associate logs with a specific run
        persona: Optional[str] = None,
        confidence: Optional[float] = None,
        forked_from: Optional[str] = None, # This could be a cell_id or another audit_entry_id
        certificate: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = time.time()
        self.event_type = event_type
        self.layer = layer
        self.details = details
        self.simulation_id = simulation_id
        self.persona = persona
        self.confidence = confidence
        self.forked_from = forked_from
        self.certificate = certificate
        self.entry_id = str(uuid.uuid4())
        self.entry_hash = self._generate_hash()

    def _generate_hash(self):
        # Ensuring all parts of the content string are actually strings to avoid issues with repr()
        details_repr = repr(self.details) # repr() is generally safe but can be long.
                                          # Consider json.dumps(self.details, sort_keys=True) for canonical representation if details are complex.
        content_parts = [
            str(self.timestamp),
            str(self.event_type),
            str(self.layer),
            str(self.simulation_id),
            str(self.persona),
            details_repr,
            str(self.forked_from)
        ]
        content = "-".join(filter(None, content_parts)) # Filter out None before joining
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            "entry_id": self.entry_id,
            "entry_hash": self.entry_hash,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "layer": self.layer,
            "details": self.details,
            "simulation_id": self.simulation_id,
            "persona": self.persona,
            "confidence": self.confidence,
            "forked_from": self.forked_from,
            "certificate": self.certificate,
        }

class AuditLogger:
    """
    Central, concurrency-safe audit trail for simulation runs.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.entries: List[AuditLogEntry] = []
        self.entry_lookup: Dict[str, AuditLogEntry] = {}
        # Potentially add indexing by simulation_id if frequent lookups per simulation are needed
        # self.simulation_log_index: Dict[str, List[str]] = defaultdict(list)

    def log(
        self,
        event_type: Literal[
            "simulation_pass", "memory_patch", "fork", "agent_decision",
            "escalation", "containment_trigger", "compliance_violation", "cert", "simulation_start", "simulation_end"
        ],
        details: Dict[str, Any],
        layer: Optional[int] = None, # Made layer optional here as well
        simulation_id: Optional[str] = None,
        persona: Optional[str] = None,
        confidence: Optional[float] = None,
        forked_from: Optional[str] = None,
        certificate: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        with self._lock:
            entry = AuditLogEntry(
                event_type=event_type,
                layer=layer,
                details=details,
                simulation_id=simulation_id,
                persona=persona,
                confidence=confidence,
                forked_from=forked_from,
                certificate=certificate
            )
            self.entries.append(entry)
            self.entry_lookup[entry.entry_id] = entry
            # if simulation_id:
            #     self.simulation_log_index[simulation_id].append(entry.entry_id)
            print(f"[AUDIT] Event: {event_type}, SimID: {simulation_id}, Layer: {layer}, EntryID: {entry.entry_id}") # Basic log
            return entry

    def query(
        self,
        event_type: Optional[str] = None,
        layer: Optional[int] = None,
        simulation_id: Optional[str] = None, # Added simulation_id query parameter
        persona: Optional[str] = None,
        after_ts: float = 0.0,
        before_ts: Optional[float] = None, # Added before_ts for time range queries
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        with self._lock:
            # Efficient query if by simulation_id and index exists:
            # if simulation_id and self.simulation_log_index.get(simulation_id):
            #     target_entry_ids = self.simulation_log_index[simulation_id]
            #     candidate_entries = [self.entry_lookup[eid] for eid in target_entry_ids if eid in self.entry_lookup]
            # else:
            #     candidate_entries = self.entries
            candidate_entries = self.entries # Iterate all for now if no specific index optimization

            filtered = []
            for e in candidate_entries:
                if event_type is not None and e.event_type != event_type: continue
                if layer is not None and e.layer != layer: continue
                if simulation_id is not None and e.simulation_id != simulation_id: continue
                if persona is not None and e.persona != persona: continue
                if e.timestamp < after_ts: continue
                if before_ts is not None and e.timestamp >= before_ts: continue
                filtered.append(e)
            
            # Sort by timestamp (typically desired for logs)
            filtered.sort(key=lambda x: x.timestamp)

            return [e.to_dict() for e in filtered[offset:offset + limit]]

    def get_by_id(self, entry_id: str) -> Optional[Dict]:
        with self._lock:
            entry = self.entry_lookup.get(entry_id)
            return entry.to_dict() if entry else None

    def clear_all_logs(self): # Renamed from clear for clarity
        with self._lock:
            self.entries.clear()
            self.entry_lookup.clear()
            # self.simulation_log_index.clear()
            print("[AUDIT] All audit logs cleared.")

    def clear_simulation_logs(self, simulation_id: str):
        with self._lock:
            new_entries = []
            removed_count = 0
            for entry in self.entries:
                if entry.simulation_id == simulation_id:
                    if entry.entry_id in self.entry_lookup:
                        del self.entry_lookup[entry.entry_id]
                    removed_count += 1
                else:
                    new_entries.append(entry)
            self.entries = new_entries
            # if simulation_id in self.simulation_log_index:
            #     del self.simulation_log_index[simulation_id]
            print(f"[AUDIT] Cleared {removed_count} log entries for simulation ID: {simulation_id}")

    def snapshot_bundle(self, simulation_id: Optional[str] = None, since_ts: float = 0.0) -> Dict:
        """
        Return the full audit trace, optionally filtered by simulation_id and since_ts.
        """
        with self._lock:
            entries_to_bundle = self.query(
                simulation_id=simulation_id, 
                after_ts=since_ts, 
                limit=len(self.entries) # Get all matching entries for the bundle
            )
            bundle_id = str(uuid.uuid4())
            return {
                "bundle_id": bundle_id,
                "generated_at": time.time(),
                "simulation_id_filter": simulation_id,
                "since_ts_filter": since_ts,
                "count": len(entries_to_bundle),
                "entries": entries_to_bundle # Already list of dicts from query()
            }

# Singleton export for simulation engine usage
audit_logger = AuditLogger()


def make_patch_certificate(
    event: Literal["memory_patch", "fork", "escalation", "containment_trigger", "agent_decision", "compliance_violation"], # Added more specific events
    origin_layer: Optional[int], # Can be None if not layer-specific
    data: Dict[str, Any],
    simulation_id: Optional[str] = None,
    persona: Optional[str] = None
) -> Dict:
    """
    Create a cert for a patch/fork/dec/move. Can be attached to audit entries or UI bundles.
    """
    t = time.time()
    cert_id = str(uuid.uuid4())
    cert_payload = {
        "cert_id": cert_id,
        "event": event,
        "origin_layer": origin_layer,
        "simulation_id": simulation_id,
        "data_snapshot": data, # This could be large, ensure it's what you want to certify
        "persona": persona,
        "timestamp": t
    }
    # Using json.dumps for canonical representation to ensure hash consistency
    # Sort keys to handle dicts where order might vary but content is the same.
    try:
        canonical_payload_str = json.dumps(cert_payload, sort_keys=True, ensure_ascii=False)
    except TypeError: # Fallback if data_snapshot is not JSON serializable (e.g. contains custom objects)
        canonical_payload_str = repr(cert_payload)
        
    cert_hash = hashlib.sha256(canonical_payload_str.encode('utf-8')).hexdigest()
    
    # Return the full certificate including its hash
    # The blueprint returned cert_payload which didn't include the hash in itself.
    # It's more common for the certificate object to contain its own hash.
    final_cert = cert_payload.copy() # cert_payload was used for hashing
    final_cert["cert_hash"] = cert_hash
    return final_cert

# Example Usage (Illustrative - not part of the file content itself normally)
if __name__ == '__main__':
    # Log some events
    sim_id = "sim_123"
    audit_logger.log("simulation_start", simulation_id=sim_id, details={"config": "test_config"})
    audit_logger.log("memory_patch", simulation_id=sim_id, layer=2, details={"coord": [0,0], "value": "test"}, persona="System")
    audit_logger.log("simulation_end", simulation_id=sim_id, details={"status": "completed"})

    # Query logs
    print("\nAll logs for sim_123:")
    for entry_dict in audit_logger.query(simulation_id=sim_id):
        print(entry_dict)

    # Get a bundle
    bundle = audit_logger.snapshot_bundle(simulation_id=sim_id)
    print(f"\nBundle ID: {bundle['bundle_id']}, Count: {bundle['count']}")

    # Make a certificate
    cert_data = {"action": "escalated", "reason": "low_confidence"}
    my_cert = make_patch_certificate("escalation", origin_layer=3, data=cert_data, simulation_id=sim_id, persona="AgentX")
    print(f"\nGenerated Certificate: {my_cert}")
    audit_logger.log("cert", simulation_id=sim_id, layer=3, details=my_cert, persona="AgentX")

    # Clear logs for the simulation
    # audit_logger.clear_simulation_logs(sim_id)
    # print(f"\nLogs for {sim_id} after clearing: {audit_logger.query(simulation_id=sim_id)}")

    # audit_logger.clear_all_logs()
    # print(f"\nTotal logs after clearing all: {len(audit_logger.query())}")

    # Test hash generation for consistency
    # For complex `details`, ensure `repr(details)` or `json.dumps(details, sort_keys=True)` is consistent.
    entry1_details = {'a': 1, 'b': 2}
    entry2_details = {'b': 2, 'a': 1} # Same content, different order
    
    # Using repr (order matters for dicts before Python 3.7)
    # hash1_repr = hashlib.sha256(repr(entry1_details).encode('utf-8')).hexdigest()
    # hash2_repr = hashlib.sha256(repr(entry2_details).encode('utf-8')).hexdigest()
    # print(f"Hash with repr (order sensitive for dicts <3.7): {hash1_repr}, {hash2_repr}")

    # Using json.dumps with sort_keys=True (canonical)
    import json
    hash1_json = hashlib.sha256(json.dumps(entry1_details, sort_keys=True).encode('utf-8')).hexdigest()
    hash2_json = hashlib.sha256(json.dumps(entry2_details, sort_keys=True).encode('utf-8')).hexdigest()
    print(f"Hash with sorted json (canonical): {hash1_json}, {hash2_json}")
    assert hash1_json == hash2_json, "JSON hashes should match for dicts with same content regardless of order" 
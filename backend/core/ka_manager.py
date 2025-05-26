from typing import Dict, Any, List
from .plugin_loader import ka_registry # Assuming ka_registry is the instance of KARegistry
from .audit import audit_logger # For logging KA calls and errors

class KnowledgeAlgorithmManager:
    """
    Manages and executes Knowledge Algorithms (KAs) using the KARegistry.
    Handles input/output, context passing, and error logging for KAs.
    """

    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        # self.ka_registry = ka_registry # Directly use the global singleton for now

    def list_available_kas(self) -> List[str]:
        """Returns a list of names of all registered KAs."""
        return ka_registry.get_ka_names()

    def get_ka_metadata(self, ka_name: str) -> Dict[str, Any]:
        """Returns metadata for a specific KA."""
        meta = ka_registry.get_ka_meta(ka_name)
        if not meta:
            # Log this event? Or expect caller to handle empty dict?
            # For now, just returning empty as per ka_registry's behavior
            pass
        return meta

    def run_ka(
        self,
        ka_name: str,
        slice_input: Dict[str, Any],
        current_context: Dict[str, Any],
        layer_number: int # For audit logging
    ) -> Dict[str, Any]:
        """
        Runs a specified KA with the given input slice and current simulation context.

        Args:
            ka_name: The name of the Knowledge Algorithm to run.
            slice_input: The specific input data slice for the KA.
            current_context: The broader simulation context.
            layer_number: The layer number invoking this KA, for auditing.

        Returns:
            A dictionary containing the KA's output, confidence, entropy, and trace.
            If the KA is not found or crashes, it returns a dict with None output,
            0.0 confidence, 1.0 entropy, and an error message in the trace.
        """
        audit_logger.log(
            event_type="ka_execution_start", # A more specific event type for KA execution
            details={"ka_name": ka_name, "input_slice": slice_input}, # Add input to audit
            layer=layer_number,
            simulation_id=self.simulation_id
        )

        # The ka_registry.call_ka is designed to be safe and return a dict even on error
        result = ka_registry.call_ka(
            name=ka_name,
            slice_input=slice_input,
            context=current_context
        )

        # Log the outcome (success or failure, as indicated by the result from call_ka)
        if result.get("confidence", 0.0) == 0.0 and "crashed" in result.get("trace", ""):
            event = "ka_execution_failure"
        else:
            event = "ka_execution_success"
        
        audit_logger.log(
            event_type=event,
            details={"ka_name": ka_name, "result": result}, # Log the full result
            layer=layer_number,
            simulation_id=self.simulation_id,
            confidence=result.get("confidence")
        )
        
        return result

# Example (not part of the actual class, for illustration)
if __name__ == '__main__':
    # This example assumes a dummy KA plugin is registered. 
    # You'd need to create a plugins/ directory and a dummy_ka.py file with register_ka().
    
    # Create a dummy plugin file: backend/plugins/dummy_ka.py
    # Ensure backend/plugins/__init__.py exists if plugins is to be a package.
    
    # --- Content for backend/plugins/dummy_ka.py ---
    # def dummy_ka_meta():
    #     return {
    #         "name": "DummyKA",
    #         "description": "A KA that does very little.",
    #         "version": "0.1"
    #     }
    # 
    # def dummy_ka_runner(slice_input: dict, context: dict) -> dict:
    #     query = slice_input.get("data", "no_data")
    #     return {
    #         "output": {"processed_query": query[::-1]}, # Reverse the data
    #         "confidence": 0.9,
    #         "entropy": 0.1,
    #         "trace": "DummyKA processed the input."
    #     }
    # 
    # def register_ka():
    #     return {
    #         "name": dummy_ka_meta()["name"],
    #         "meta": dummy_ka_meta(),
    #         "runner": dummy_ka_runner
    #     }
    # --- End of content for backend/plugins/dummy_ka.py ---

    # Ensure the KARegistry loads plugins (it does so on init)
    # from .plugin_loader import ka_registry # ka_registry is already imported
    # ka_registry.reload_plugins() # If you added/changed plugins after initial load

    print("Available KAs:", ka_registry.get_ka_names())

    if "DummyKA" in ka_registry.get_ka_names():
        print("Metadata for DummyKA:", ka_registry.get_ka_meta("DummyKA"))
        
        kam = KnowledgeAlgorithmManager(simulation_id="sim_test_kam")
        
        test_slice = {"data": "hello world"}
        test_context = {"user_id": "test_user"}
        
        print(f"\nRunning DummyKA with input: {test_slice}")
        ka_output = kam.run_ka(
            ka_name="DummyKA",
            slice_input=test_slice,
            current_context=test_context,
            layer_number=0 # Example layer
        )
        print(f"DummyKA Output: {ka_output}")

        print(f"\nRunning a non-existent KA:")
        error_output = kam.run_ka(
            ka_name="NonExistentKA",
            slice_input=test_slice,
            current_context=test_context,
            layer_number=0
        )
        print(f"NonExistentKA Output: {error_output}")
    else:
        print("\nDummyKA not found. Please ensure plugins/dummy_ka.py exists and is registered.")
        print(f"PLUGIN_DIR is: {ka_registry.PLUGIN_DIR}")
        print("To create it, make a file backend/plugins/dummy_ka.py with the content shown in the comments of ka_manager.py")

    print("\nAudit logs from this test run:")
    for log_entry in audit_logger.query(simulation_id="sim_test_kam"):
        print(log_entry) 
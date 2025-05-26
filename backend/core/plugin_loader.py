import importlib
import importlib.util
import sys
import os
import threading
from typing import Dict, Callable, Any, List

# Corrected PLUGIN_DIR to be relative to this file's location, then up and into plugins/
# This assumes core/ is a direct subdirectory of backend/, and plugins/ is a sibling to core/
PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
PLUGIN_PACKAGE = "plugins" # This should match the directory name if it's treated as a package

class KARegistry:
    """
    Discovers, loads, hot-reloads KA modules from plugins/ dir.
    Registry format:
      { "ka_name": { "meta": ..., "runner": callable, "module": ref } }
    """

    def __init__(self):
        self.algos: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock() # Changed to RLock if re-entrant calls to load_plugins are possible, otherwise Lock is fine.
        # self.plugin_files: List[str] = [] # This was in blueprint, but not used. Removing for now.
        self.load_plugins()

    def load_plugins(self):
        """
        Loads/discovers KA modules from plugins/, calling their 'register' function.
        """
        with self.lock:
            self.algos.clear()
            # self.plugin_files = [] # Also unused here
            if not os.path.exists(PLUGIN_DIR):
                # Try to create if it doesn't exist, as per blueprint expectation
                try:
                    os.makedirs(PLUGIN_DIR)
                    print(f"[INFO] Created plugin directory: {PLUGIN_DIR}")
                except OSError as e:
                    print(f"[ERROR] Could not create plugin directory {PLUGIN_DIR}: {e}")
                    return # Cannot proceed without plugin directory
            
            # Ensure plugins directory is in sys.path to allow direct import by name for the package
            # This is important if plugins/ itself is not a package (no __init__.py) but modules within it are treated as part of 'plugins' package.
            # A more robust way is to ensure plugins/ is a proper package.
            # For now, let's adjust sys.path as a common workaround if plugins/ might not be a package.
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if backend_dir not in sys.path:
                 sys.path.insert(0, backend_dir)

            for fname in os.listdir(PLUGIN_DIR):
                if fname.endswith('.py') and not fname.startswith("__"):
                    module_name_in_package = f"{PLUGIN_PACKAGE}.{fname[:-3]}" # e.g., plugins.sample_algo
                    file_path = os.path.join(PLUGIN_DIR, fname)
                    try:
                        # Force reload: Unload module if already loaded
                        if module_name_in_package in sys.modules:
                            del sys.modules[module_name_in_package]
                        
                        # Load the module
                        # The blueprint used spec_from_file_location which is good for arbitrary paths.
                        # If plugins is a package, importlib.import_module can be simpler.
                        spec = importlib.util.spec_from_file_location(module_name_in_package, file_path)
                        if spec is None:
                            print(f"[ERROR] Could not create spec for plugin {fname}. Skipping.")
                            continue
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name_in_package] = module # Register module before execution
                        spec.loader.exec_module(module)
                        
                        # Register the KA if a register function exists
                        # The blueprint had module.register(self.algos) which mutates a dict passed in.
                        # Let's refine this to have register return the KA details.
                        if hasattr(module, "register_ka") and callable(module.register_ka):
                            ka_details = module.register_ka() # Expects dict like {"name": ..., "meta": ..., "runner": ...}
                            if isinstance(ka_details, dict) and 'name' in ka_details and 'runner' in ka_details:
                                ka_name = ka_details['name']
                                self.algos[ka_name] = {
                                    "meta": ka_details.get("meta", {}),
                                    "runner": ka_details["runner"],
                                    "module_path": file_path # Store path for debugging
                                }
                                print(f"[INFO] Registered KA: {ka_name} from {fname}")
                            else:
                                print(f"[WARN] KA plugin {fname} register_ka() did not return valid details. Skipped.")
                        else:
                            print(f"[WARN] KA plugin {fname} has no callable register_ka(). Skipped.")
                    except Exception as e:
                        print(f"[ERROR] Loading plugin {fname}: {e}")
                        # If module was partially loaded and failed, remove from sys.modules to allow retry
                        if module_name_in_package in sys.modules:
                            del sys.modules[module_name_in_package]

    def reload_plugins(self):
        """Force reload of all plugins (API/CLI action)."""
        print("[INFO] Reloading KA plugins...")
        self.load_plugins()

    def get_ka_names(self) -> List[str]:
        """List names (keys) of available KAs."""
        with self.lock:
            return list(self.algos.keys())

    def get_ka_meta(self, name: str) -> Dict[str, Any]:
        """Get KA metadata."""
        with self.lock:
            ka = self.algos.get(name)
            return ka["meta"] if ka else {}

    # get_runner was in blueprint but call_ka directly uses the runner.
    # def get_runner(self, name: str) -> Callable:
    #     """Get callable KA runner."""
    #     with self.lock:
    #         ka = self.algos.get(name)
    #         if ka is None:
    #             raise KeyError(f"KA '{name}' not found")
    #         return ka["runner"]

    def call_ka(
        self, 
        name: str, 
        slice_input: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the plugin safely, trap any errors, return minimal diagnosis if fail.
        """
        with self.lock: # Lock ensures that self.algos is not modified during iteration/access
            ka_info = self.algos.get(name)
        
        if not ka_info or not callable(ka_info.get("runner")):
            print(f"[ERROR] KA '{name}' not found or runner is not callable.")
            return {
                "output": None,
                "confidence": 0.0,
                "entropy": 1.0,
                "trace": f"KA '{name}' not found or invalid."
            }
        
        runner = ka_info["runner"]
        try:
            result = runner(slice_input, context)
            # Ensure required keys as per blueprint's expectation for KA output
            for k_required in ("output", "confidence", "entropy", "trace"):
                if k_required not in result:
                    # Provide defaults if missing, can also raise error
                    result[k_required] = None 
                    if k_required == "confidence": result[k_required] = 0.0
                    if k_required == "entropy": result[k_required] = 1.0
            return result
        except Exception as exc:
            print(f"[ERROR] Running KA '{name}': {exc}")
            return {
                "output": None,
                "confidence": 0.0,
                "entropy": 1.0,
                "trace": f"KA '{name}' crashed: {exc}"
            }

# Single instance for app
ka_registry = KARegistry()

# Example of how a plugin in plugins/sample_algo.py might look now:
"""
# In plugins/sample_algo.py

def sample_ka_meta():
    return {
        "name": "SampleEchoKA",
        "description": "A demo echo knowledge algorithm.",
        "version": "1.0.1",
        "author": "UKG Sim Team"
    }

def sample_ka_runner(slice_input: dict, context: dict) -> dict:
    q = slice_input.get("query", "")
    return {
        "output": {"echo_response": q, "processed_by": sample_ka_meta()["name"]},
        "confidence": 0.75, # Example value
        "entropy": 0.05,    # Example value
        "trace": {"input_received": q, "notes": "SampleEchoKA ran successfully"}
    }

def register_ka(): # Changed from `register` to `register_ka` and changed signature
    return {
        "name": sample_ka_meta()["name"], # The KA's self-declared name
        "meta": sample_ka_meta(),
        "runner": sample_ka_runner
    }
""" 
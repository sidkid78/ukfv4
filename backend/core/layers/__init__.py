"""
Layers Module - Contains implementations for simulation layers 1-10

Exports:
- BaseLayer: Abstract base class for all layers
- Layer1 to Layer10: Concrete layer implementations
"""
from .base import BaseLayer
from .layer1 import Layer1SimulationEntry
from .layer2 import Layer2MemoryDatabase 
from .layer3 import Layer3ResearchAgents
from .layer4 import Layer4POVEngine
from .layer5 import Layer5Gatekeeper
from .layer6 import Layer6AdvancedReasoning
from .layer7 import Layer7QuantumReasoning
from .layer8 import Layer8SocietalEthics
from .layer9 import Layer9MetaAnalysisVerification
from .layer10 import Layer10EmergenceContainment

LAYER_CLASSES = [
    Layer1SimulationEntry,
    Layer2MemoryDatabase,
    Layer3ResearchAgents,
    Layer4POVEngine,
    Layer5Gatekeeper,
    Layer6AdvancedReasoning,
    Layer7QuantumReasoning,
    Layer8SocietalEthics,
    Layer9MetaAnalysisVerification,
    Layer10EmergenceContainment
]

def get_layer_instance(layer_id: int):
    """
    Factory function to get appropriate layer instance based on
    configuration.
    """
    if layer_id == 3:
        return Layer3ResearchAgents()
    else:
        return LAYER_CLASSES[layer_id]()

__all__ = [
    'BaseLayer',
    'Layer1SimulationEntry', 'Layer2MemoryDatabase', 'Layer3ResearchAgents', 'Layer4POVEngine', 'Layer5Gatekeeper',
    'Layer6AdvancedReasoning', 'Layer7QuantumReasoning', 'Layer8SocietalEthics', 'Layer9MetaAnalysisVerification', 'Layer10EmergenceContainment'
]
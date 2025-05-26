"""
Layer 2: Memory/Database Layer
Handles knowledge retrieval, memory patching, and context enrichment
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph


@register_layer(2)
class Layer2MemoryDatabase(BaseLayer):
    """
    Memory and knowledge retrieval layer. Handles knowledge graph access,
    memory patching, and context enrichment from stored knowledge.
    """
    
    def __init__(self):
        super().__init__()
        self.layer_number = 2
        self.layer_name = "Memory/Database Layer"
        self.confidence_threshold = 0.98
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process memory retrieval and knowledge augmentation"""
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        axes = input_data.get("axes", [0.0] * 13)
        persona = input_data.get("persona", "general_assistant")
        
        # Search for relevant knowledge
        memory_search_results = self._search_memory(memory, query, axes, persona)
        
        # Retrieve or create memory cell
        primary_cell = memory.get(axes, persona=persona)
        
        # Determine if we need to patch memory
        patches_needed = self._determine_memory_patches(
            query, memory_search_results, primary_cell
        )
        
        patches = []
        for patch_info in patches_needed:
            patch = self.patch_memory(
                memory=memory,
                coordinate=patch_info["coordinate"],
                value=patch_info["value"],
                operation=patch_info["operation"],
                reason=patch_info["reason"],
                persona=persona
            )
            patches.append(patch)
        
        # Calculate confidence based on knowledge availability
        confidence = self._calculate_memory_confidence(
            memory_search_results, primary_cell, patches
        )
        
        # Determine escalation need
        escalate = self.should_escalate(confidence) or len(memory_search_results) == 0
        
        # Create enriched output
        output = {
            **input_data,  # Pass through previous data
            "memory_results": memory_search_results,
            "primary_cell": primary_cell,
            "knowledge_available": len(memory_search_results) > 0,
            "patches_applied": len(patches),
            "memory_enriched": True
        }
        
        # Add best answer if available
        if memory_search_results:
            best_result = max(memory_search_results, key=lambda x: x.get("relevance", 0))
            output["memory_answer"] = best_result.get("value")
            output["memory_confidence"] = best_result.get("confidence", 0.5)
        
        trace = {
            "memory_searches": len(memory_search_results),
            "primary_cell_found": primary_cell is not None,
            "patches_applied": len(patches),
            "knowledge_gaps": self._identify_knowledge_gaps(query, memory_search_results)
        }
        
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            patches=patches,
            metadata={"memory_layer": True}
        )
    
    def _search_memory(
        self, 
        memory: InMemoryKnowledgeGraph, 
        query: str, 
        axes: List[float], 
        persona: str
    ) -> List[Dict[str, Any]]:
        """Search memory for relevant knowledge"""
        
        results = []
        
        # Search by persona
        persona_cells = memory.find_by_persona(persona)
        for cell in persona_cells:
            relevance = self._calculate_relevance(query, cell)
            if relevance > 0.3:
                results.append({
                    **cell,
                    "relevance": relevance,
                    "source": "persona_match"
                })
        
        # Search nearby coordinates (simplified - would use proper similarity search)
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:
                    continue
                
                search_axes = axes.copy()
                search_axes[0] = max(0, min(1, axes[0] + i * 0.1))
                search_axes[1] = max(0, min(1, axes[1] + j * 0.1))
                
                cell = memory.get(search_axes)
                if cell:
                    relevance = self._calculate_relevance(query, cell)
                    if relevance > 0.4:
                        results.append({
                            **cell,
                            "relevance": relevance,
                            "source": "coordinate_proximity"
                        })
        
        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return results[:10]  # Top 10 results
    
    def _calculate_relevance(self, query: str, cell: Dict[str, Any]) -> float:
        """Calculate relevance score between query and memory cell"""
        
        if not cell or not cell.get("value"):
            return 0.0
        
        cell_value = str(cell["value"]).lower()
        query_lower = query.lower()
        
        # Simple keyword matching (would use embeddings in production)
        query_words = set(query_lower.split())
        cell_words = set(cell_value.split())
        
        if not query_words or not cell_words:
            return 0.0
        
        intersection = query_words.intersection(cell_words)
        union = query_words.union(cell_words)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0.0
        
        # Boost for exact phrase matches
        if query_lower in cell_value:
            jaccard_similarity += 0.3
        
        return min(1.0, jaccard_similarity)
    
    def _determine_memory_patches(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]], 
        primary_cell: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Determine what memory patches are needed"""
        
        patches = []
        
        # If no relevant knowledge found, create a stub
        if not search_results and not primary_cell:
            coordinate = [0.5] * 13  # Default coordinate
            patches.append({
                "coordinate": coordinate,
                "value": {
                    "query_stub": query,
                    "created_at": datetime.now().isoformat(),
                    "needs_research": True,
                    "stub_type": "knowledge_gap"
                },
                "operation": "add",
                "reason": "Created knowledge gap stub for research"
            })
        
        # Update existing cells with new context if needed
        if primary_cell and search_results:
            # Merge relevant results into primary cell
            enriched_value = primary_cell.get("value", {})
            if isinstance(enriched_value, dict):
                enriched_value["related_knowledge"] = [
                    r["value"] for r in search_results[:3]  # Top 3 related
                ]
                enriched_value["last_accessed"] = datetime.now().isoformat()
                
                patches.append({
                    "coordinate": primary_cell["coordinate"],
                    "value": enriched_value,
                    "operation": "update",
                    "reason": "Enriched with related knowledge"
                })
        
        return patches
    
    def _calculate_memory_confidence(
        self, 
        search_results: List[Dict[str, Any]], 
        primary_cell: Optional[Dict[str, Any]], 
        patches: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence based on memory state"""
        
        base_confidence = 0.7
        
        # Increase confidence for good search results
        if search_results:
            avg_relevance = sum(r.get("relevance", 0) for r in search_results) / len(search_results)
            base_confidence += avg_relevance * 0.2
        
        # Increase confidence for existing primary cell
        if primary_cell and not primary_cell.get("value", {}).get("needs_research", False):
            base_confidence += 0.15
        
        # Slight boost for patches applied (shows active knowledge management)
        if patches:
            base_confidence += min(len(patches) * 0.05, 0.1)
        
        return min(1.0, max(0.1, base_confidence))
    
    def _identify_knowledge_gaps(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify gaps in available knowledge"""
        
        gaps = []
        
        if not search_results:
            gaps.append("No relevant knowledge found")
        
        if search_results and max(r.get("relevance", 0) for r in search_results) < 0.6:
            gaps.append("Low relevance of available knowledge")
        
        # Check for specific knowledge types
        has_factual = any("fact" in str(r.get("value", "")).lower() for r in search_results)
        has_analytical = any("analysis" in str(r.get("value", "")).lower() for r in search_results)
        
        if not has_factual:
            gaps.append("Lacks factual foundation")
        if not has_analytical:
            gaps.append("Lacks analytical perspective")
        
        return gaps


"""
Layer 2: Memory/Database Layer
Handles knowledge retrieval, memory patching, and context enrichment
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import uuid
import logging

from .base import BaseLayer, LayerResult, register_layer
from core.memory import InMemoryKnowledgeGraph
from core.gemini_service import gemini_service, GeminiRequest, GeminiModel
import asyncio

logger = logging.getLogger(__name__)


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
        self.confidence_threshold = 0.8  # More realistic threshold
        self.requires_memory = True
        
    def process(
        self, 
        input_data: Dict[str, Any], 
        state: Dict[str, Any], 
        memory: InMemoryKnowledgeGraph,
        agents: Optional[List[Any]] = None
    ) -> LayerResult:
        """Process memory retrieval and knowledge augmentation"""
        log_id = str(uuid.uuid4())[:8]
        logger.info(f"Layer 2 processing started | ID: {log_id} | Query: {input_data.get('query', '')[:50]}...")
        
        query = input_data.get("normalized_query", input_data.get("query", ""))
        axes = input_data.get("axes", [0.0] * 13)
        persona = input_data.get("persona", "general_assistant")
        
        # Search for relevant knowledge
        logger.debug(f"Searching memory | ID: {log_id}")
        memory_search_results = self._search_memory(memory, query, axes, persona)
        logger.info(f"Memory search completed | ID: {log_id} | Results: {len(memory_search_results)}")
        
        # Retrieve or create memory cell
        primary_cell = memory.get(axes, persona=persona)
        logger.debug(f"Primary cell status | ID: {log_id} | Found: {primary_cell is not None}")
        
        # Determine if we need to patch memory
        patches_needed = self._determine_memory_patches(
            query, memory_search_results, primary_cell
        )
        logger.info(f"Patches determined | ID: {log_id} | Count: {len(patches_needed)}")
        
        patches = []
        for patch_info in patches_needed:
            logger.debug(f"Applying patch | ID: {log_id} | Operation: {patch_info['operation']} | Reason: {patch_info['reason']}")
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
        logger.info(f"Confidence calculated | ID: {log_id} | Value: {confidence:.2f}")
        
        # Determine escalation need based on confidence and knowledge availability
        escalate = self.should_escalate(confidence) or (len(memory_search_results) == 0 and confidence < 0.8)
        if escalate:
            reason = "Empty results" if len(memory_search_results) == 0 else "Low confidence"
            logger.warning(f"Escalation triggered | ID: {log_id} | Reason: {reason}")
        
        # Create enriched output
        output = {
            **input_data,
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
            logger.debug(f"Best memory result | ID: {log_id} | Relevance: {best_result.get('relevance', 0):.2f}")
        
        trace = {
            "memory_searches": len(memory_search_results),
            "primary_cell_found": primary_cell is not None,
            "patches_applied": len(patches),
            "knowledge_gaps": self._identify_knowledge_gaps(query, memory_search_results)
        }
        
        logger.info(f"Layer 2 processing complete | ID: {log_id} | Confidence: {confidence:.2f} | Escalate: {escalate}")
        return LayerResult(
            output=output,
            confidence=confidence,
            escalate=escalate,
            trace=trace,
            patches=patches,
            metadata={
                "memory_layer": True,
                "log_id": log_id
            }
        )
    
    def _search_memory(
        self, 
        memory: InMemoryKnowledgeGraph, 
        query: str, 
        axes: List[float], 
        persona: str
    ) -> List[Dict[str, Any]]:
        """Search memory for relevant knowledge"""
        logger.debug(f"Starting memory search | Persona: {persona} | Axes: {axes[:2]}...")
        results = []
        
        # Search by persona
        persona_cells = memory.find_by_persona(persona)
        logger.debug(f"Found {len(persona_cells)} persona cells for {persona}")
        for cell in persona_cells:
            relevance = self._calculate_relevance(query, cell)
            if relevance > 0.3:
                results.append({
                    **cell,
                    "relevance": relevance,
                    "source": "persona_match"
                })
        
        # Search nearby coordinates
        logger.debug("Starting coordinate proximity search")
        proximity_matches = 0
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
                        proximity_matches += 1
                        results.append({
                            **cell,
                            "relevance": relevance,
                            "source": "coordinate_proximity"
                        })
        logger.debug(f"Found {proximity_matches} proximity matches")
        
        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        logger.debug(f"Top relevance scores: {[r['relevance'] for r in results[:3]]}")
        return results[:10]
    
    def _calculate_relevance(self, query: str, cell: Dict[str, Any]) -> float:
        """Calculate relevance score using AI-powered semantic similarity"""
        if not cell or not cell.get("value"):
            return 0.0
        
        cell_value = str(cell["value"])
        
        # For short content, use simple keyword matching as fallback
        if len(cell_value) < 20 or len(query) < 10:
            return self._keyword_relevance(query, cell_value)
        
        # Use AI for semantic relevance scoring
        try:
            ai_request = GeminiRequest(
                prompt=f"Rate the relevance between this query and content on a scale of 0.0 to 1.0:\n\nQUERY: {query}\n\nCONTENT: {cell_value[:500]}...",
                system_prompt="""You are a semantic relevance expert. Rate how relevant the content is to answering the query.
                
                Scoring guide:
                - 1.0: Content directly answers the query
                - 0.8-0.9: Content is highly relevant and helpful
                - 0.6-0.7: Content is somewhat relevant
                - 0.4-0.5: Content has some relevance
                - 0.1-0.3: Content is barely relevant
                - 0.0: Content is not relevant
                
                Respond with ONLY a number between 0.0 and 1.0, nothing else.""",
                model=GeminiModel.GEMINI_FLASH,
                temperature=0.1  # Low temperature for consistent scoring
            )
            
            response = asyncio.run(gemini_service.generate_async(ai_request, layer=2))
            
            # Try to parse the relevance score
            try:
                relevance = float(response.content.strip())
                relevance = max(0.0, min(1.0, relevance))  # Clamp to 0-1
                
                logger.debug(f"AI relevance score: {relevance:.2f} for query: {query[:30]}...")
                return relevance
                
            except ValueError:
                logger.warning(f"Invalid AI relevance score: {response.content}, using keyword fallback")
                return self._keyword_relevance(query, cell_value)
                
        except Exception as e:
            logger.warning(f"AI relevance calculation failed: {str(e)}, using keyword fallback")
            return self._keyword_relevance(query, cell_value)
    
    def _keyword_relevance(self, query: str, cell_value: str) -> float:
        """Fallback keyword-based relevance calculation"""
        cell_lower = cell_value.lower()
        query_lower = query.lower()
        
        # Simple keyword matching
        query_words = set(query_lower.split())
        cell_words = set(cell_lower.split())
        
        if not query_words or not cell_words:
            return 0.0
        
        intersection = query_words.intersection(cell_words)
        union = query_words.union(cell_words)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0.0
        
        # Boost for exact phrase matches
        if query_lower in cell_lower:
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
        
        # Create stub if no results
        if not search_results and not primary_cell:
            logger.info("Creating knowledge gap stub")
            coordinate = [0.5] * 13
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
        
        # Update existing cells
        if primary_cell and search_results:
            logger.info("Enriching existing memory cell")
            enriched_value = primary_cell.get("value", {})
            if isinstance(enriched_value, dict):
                enriched_value["related_knowledge"] = [
                    r["value"] for r in search_results[:3]
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
        
        if search_results:
            avg_relevance = sum(r.get("relevance", 0) for r in search_results) / len(search_results)
            base_confidence += avg_relevance * 0.2
            logger.debug(f"Confidence boost from search results: {avg_relevance * 0.2:.2f}")
        
        if primary_cell and not primary_cell.get("value", {}).get("needs_research", False):
            base_confidence += 0.15
            logger.debug("Confidence boost from valid primary cell")
        
        if patches:
            boost = min(len(patches) * 0.05, 0.1)
            base_confidence += boost
            logger.debug(f"Confidence boost from patches: {boost:.2f}")
        
        return min(1.0, max(0.1, base_confidence))
    
    def _identify_knowledge_gaps(self, query: str, search_results: List[Dict[str, Any]]) -> List[str]:
        """Identify gaps in available knowledge using AI analysis"""
        gaps = []
        
        # Basic checks first
        if not search_results:
            gaps.append("No relevant knowledge found")
            logger.warning("Critical knowledge gap detected")
        
        if search_results and max(r.get("relevance", 0) for r in search_results) < 0.6:
            gaps.append("Low relevance of available knowledge")
            logger.debug("Low relevance gap detected")
        
        # Use AI to identify more sophisticated knowledge gaps
        if search_results:
            try:
                # Prepare content summary for AI analysis
                available_content = "\n".join([
                    f"- {str(r.get('value', ''))[:100]}..." 
                    for r in search_results[:3]
                ])
                
                ai_request = GeminiRequest(
                    prompt=f"Analyze what knowledge gaps exist for answering this query:\n\nQUERY: {query}\n\nAVAILABLE KNOWLEDGE:\n{available_content}",
                    system_prompt="""You are a knowledge gap analyst. Identify what important information is missing to fully answer the query.
                    
                    Look for gaps in:
                    - Factual information
                    - Context and background
                    - Recent developments
                    - Different perspectives
                    - Supporting evidence
                    
                    List each gap on a separate line starting with '- '
                    If no significant gaps, respond with 'No major gaps identified'.""",
                    model=GeminiModel.GEMINI_FLASH,
                    temperature=0.3
                )
                
                response = asyncio.run(gemini_service.generate_async(ai_request, layer=2))
                content = response.content.strip()
                
                # Parse AI-identified gaps
                if content and "no major gaps" not in content.lower():
                    ai_gaps = [
                        line.strip().replace("- ", "") 
                        for line in content.split("\n") 
                        if line.strip().startswith("- ")
                    ]
                    gaps.extend(ai_gaps[:3])  # Limit to top 3 AI-identified gaps
                    
                logger.debug(f"AI identified {len(ai_gaps) if 'ai_gaps' in locals() else 0} additional knowledge gaps")
                    
            except Exception as e:
                logger.warning(f"AI knowledge gap analysis failed: {str(e)}")
        
        # Legacy knowledge type checks
        has_factual = any("fact" in str(r.get("value", "")).lower() for r in search_results)
        has_analytical = any("analysis" in str(r.get("value", "")).lower() for r in search_results)
        
        if not has_factual:
            gaps.append("Lacks factual foundation")
        if not has_analytical:
            gaps.append("Lacks analytical perspective")
        
        logger.debug(f"Identified {len(gaps)} knowledge gaps")
        return gaps

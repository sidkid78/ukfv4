// Gemini AI Types for frontend integration
// Extends the existing simulation types with AI-specific interfaces

import { SimulationLayer, EventType } from './simulation';

// Gemini AI Models
export type GeminiModel = 
  | "gemini-2.5-pro-preview-03-25"
  | "gemini-2.5-flash-preview-05-20"
  | "gemini-2.0-flash"
  | "gemini-2.5-flash-preview";

// AI Request/Response Types
export interface AIRequest {
  prompt: string;
  model?: GeminiModel;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  persona?: string;
  stream?: boolean;
}

export interface AIResponse {
  content: string;
  model: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  confidence: number;
  reasoning_trace?: Record<string, any>;
  timestamp: string;
  request_id: string;
  processing_time: number;
}

// AI Health Status
export interface AIHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  models_available: string[];
  response_time?: number;
  last_check: string;
}

// Layer-specific AI Analysis
export interface LayerAIAnalysis {
  layer: SimulationLayer;
  ai_analysis: {
    normalized_query: string;
    query_type: string;
    complexity_score: number;
    intent: string;
    domain: string;
    safety_level: 'safe' | 'caution' | 'high_risk';
    requires_escalation: boolean;
    escalation_reason?: string;
    key_concepts: string[];
    uncertainty_indicators: string[];
    insights: string[];
    suggested_persona: string;
    ai_confidence: number;
    fallback_used?: boolean;
  };
  confidence: number;
  processing_time: number;
}

// Agent AI Analysis
export interface AgentAIResult {
  agent_id: string;
  persona: string;
  answer: string;
  confidence: number;
  reasoning: string;
  evidence: string[];
  alternatives: string[];
  ai_response: string;
  processing_time: number;
  error?: boolean;
  error_message?: string;
}

// Research Synthesis
export interface AIResearchSynthesis {
  answer: string;
  confidence: number;
  evidence_quality: 'poor' | 'medium' | 'good' | 'excellent';
  alternatives: string[];
  synthesis_reasoning: string;
  requires_expert_review: boolean;
}

// Safety Analysis
export interface AISafetyAnalysis {
  content_length: number;
  safety_analysis: {
    safety_score: number;
    analysis: string;
    recommendations: string[];
    containment_needed: boolean;
  };
  safe: boolean;
  containment_needed: boolean;
}

// AI Usage Statistics
export interface AIUsageStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time: number;
  tokens_used: number;
  cost_estimate?: number;
  last_24h: {
    requests: number;
    tokens: number;
  };
}

// AI Configuration
export interface AIConfig {
  default_model: GeminiModel;
  temperature: number;
  max_tokens: number;
  timeout: number;
  max_retries: number;
  safety_threshold: number;
}

// Real-time AI Events (WebSocket)
export interface AIEvent {
  type: 'AI_STARTED' | 'AI_COMPLETED' | 'AI_ERROR' | 'AI_STREAM_CHUNK';
  data: {
    request_id: string;
    session_id: string;
    layer?: SimulationLayer;
    content?: string;
    error?: string;
    progress?: number;
  };
  timestamp: string;
}

// UI-specific AI State
export interface AIState {
  isGenerating: boolean;
  currentRequest?: {
    id: string;
    prompt: string;
    model: GeminiModel;
    started_at: string;
  };
  lastResponse?: AIResponse;
  health: AIHealthStatus;
  config: AIConfig;
  usage: AIUsageStats;
}

// AI Chat Interface (for direct interaction)
export interface AIChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  model?: GeminiModel;
  confidence?: number;
  processing_time?: number;
  metadata?: Record<string, any>;
}

export interface AIChatSession {
  id: string;
  title: string;
  messages: AIChatMessage[];
  created_at: string;
  updated_at: string;
  model: GeminiModel;
  system_prompt?: string;
}

// AI Enhancement for existing types
export interface AIEnhancedTraceStep {
  id: string;
  timestamp: string;
  layer: SimulationLayer;
  layer_name: string;
  message: string;
  event_type: EventType;
  confidence: number;
  ai_enhanced: boolean;
  ai_analysis?: LayerAIAnalysis;
  ai_agents?: AgentAIResult[];
  ai_synthesis?: AIResearchSynthesis;
  input_snapshot: Record<string, any>;
  output_snapshot: Record<string, any>;
}

// AI-powered query suggestions
export interface AIQuerySuggestion {
  id: string;
  query: string;
  category: string;
  complexity: number;
  estimated_layers: SimulationLayer[];
  description: string;
  tags: string[];
}

export default {
  AIRequest,
  AIResponse,
  AIHealthStatus,
  LayerAIAnalysis,
  AgentAIResult,
  AIResearchSynthesis,
  AISafetyAnalysis,
  AIUsageStats,
  AIConfig,
  AIEvent,
  AIState,
  AIChatMessage,
  AIChatSession,
  AIEnhancedTraceStep,
  AIQuerySuggestion,
};
`
}

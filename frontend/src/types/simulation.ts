// frontend/src/types/simulation.ts
// Shared API contracts for UKG/USKD Simulation System

export type SimulationLayer = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type SimulationStatus = 
  | 'READY' 
  | 'RUNNING' 
  | 'STEPPING' 
  | 'COMPLETED' 
  | 'ESCALATED' 
  | 'CONTAINED' 
  | 'FAILED';

export type LayerStatus = 
  | 'READY' 
  | 'RUNNING' 
  | 'COMPLETED' 
  | 'ESCALATED' 
  | 'CONTAINED';

export type EventType = 
  | 'SIMULATION_START'
  | 'LAYER_ENTRY' 
  | 'LAYER_EXIT'
  | 'AGENT_SPAWN'
  | 'AGENT_ACTION'
  | 'MEMORY_PATCH'
  | 'FORK_DETECTED'
  | 'ESCALATION'
  | 'CONTAINMENT'
  | 'COMPLIANCE_CHECK'
  | 'AUDIT_EVENT';

// Core Simulation Types

export interface SimulationRequest {
  prompt: string;
  model?: 'gemini-2.0-flash' | 'gemini-2.0-pro';
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  context?: Record<string, unknown>;
  persona?: string;
  stream?: boolean;
}

export interface SimulationQuery {
  user_query: string;
  session_id: string;
  context?: Record<string, unknown>;
  axes?: number[]; // 13-dimensional coordinate
}

export interface ConfidenceScore {
  layer: SimulationLayer;
  score: number;
  delta: number;
  entropy?: number;
}

export interface TraceStep {
  id: string;
  timestamp: string;
  layer: SimulationLayer;
  layer_name: string;
  message: string;
  event_type: EventType;
  confidence: ConfidenceScore;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown>;
  agent?: string;
  persona?: string;
  patch?: MemoryPatch;
  fork?: ForkEvent;
  audit_cert?: AuditCertEvent;
  notes?: string;
}

export interface LayerState {
  layer: SimulationLayer;
  name: string;
  status: LayerStatus;
  trace: TraceStep[];
  agents: string[];
  confidence: ConfidenceScore;
  forked: boolean;
  escalation: boolean;
  persona_reasonings: Record<string, string>;
  patches: MemoryPatch[];
}

export interface SimulationSession {
  id: string;
  run_id: string;
  created_at: string;
  user_id?: string;
  status: SimulationStatus;
  layers_active: SimulationLayer[];
  current_layer: SimulationLayer;
  input_query: SimulationQuery;
  layers: LayerState[];
  state: Record<string, unknown>;
  final_output?: unknown;
}

// Memory & Knowledge Graph Types
export interface MemoryCell {
  coordinate: number[]; // 13-dimensional
  value: unknown;
  version: number;  
  metadata?: Record<string, unknown>;
  created_at: string;
  last_modified: string;
}

export interface MemoryPatch {
  id: string;
  coordinate: number[];
  value: unknown;
  operation: 'add' | 'update' | 'delete' | 'fork';
  source: string;
  agent?: string;
  persona?: string;
  layer: SimulationLayer;
  timestamp: string;
  reason: string;
  before?: unknown;
  after?: unknown;
}

export interface ForkEvent {
  id: string;
  parent_layer: SimulationLayer;
  fork_layer: SimulationLayer;
  reason: string;
  agent: string;
  timestamp: string;
  branch_id: string;
  confidence_before: number;
  confidence_after: number;
}

// Agent & Persona Types
export interface Agent {
  id: string;
  name: string;
  role: string;
  persona: string;
  active: boolean;
  axes?: number[];
  context: Record<string, unknown>;
  memory_trace: unknown[];
  created_at: string;
}

export interface AgentCreateRequest {
  name: string;
  role: string;
  persona?: string;
  axes?: number[];
  init_prompt?: string;
}

// Plugin & KA Types
export interface KnowledgeAlgorithm {
  id: string;
  name: string;
  active: boolean;
  type: string;
  description?: string;
  version: string;
  author?: string;
  params: Record<string, unknown>;
  layers_mapped: SimulationLayer[];
}

export interface KAResult {
  name: string;
  output: unknown;
  confidence: number;
  entropy: number;
  trace: Record<string, unknown>;
}

// Audit & Compliance Types
export interface AuditCertEvent {
  id: string;
  entry_id: string;
  entry_hash: string;
  timestamp: string;
  event_type: EventType;
  layer: SimulationLayer;
  details: Record<string, unknown>;
  persona?: string;
  confidence?: number;
  forked_from?: string;
  certificate?: Record<string, unknown>;
}

export interface ComplianceViolation {
  id: string;
  type: 'CONFIDENCE_LOW' | 'ENTROPY_HIGH' | 'CONTAINMENT_BREACH' | 'DRIFT_DETECTED';
  layer: SimulationLayer;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  message: string;
  timestamp: string;
  auto_contained: boolean;
}

// API Response Types
export interface SimulationRunResponse {
  run_id: string;
  session: SimulationSession;
  trace: TraceStep[];
  final_output: unknown;
  state: Record<string, unknown>;
}

export interface LayerStepResponse {
  layer: SimulationLayer;
  status: LayerStatus;
  trace: TraceStep[];
  confidence: ConfidenceScore;
  escalation_triggered: boolean;
  patches_applied: MemoryPatch[];
  agents_spawned: string[];
}

export interface LayerStepRequest {
  layer: SimulationLayer;
  query: string;
  context?: Record<string, unknown>;
  persona?: string;
}

// UI State Types
export type ViewPanel = 
  | 'TRACE' 
  | 'AGENTS' 
  | 'PERSONAS' 
  | 'FORKS' 
  | 'CONFIDENCE' 
  | 'MEMORY' 
  | 'AUDIT';

export type SimulationMode = 
  | 'NORMAL' 
  | 'STEPPING' 
  | 'REPLAY' 
  | 'RED_TEAM' 
  | 'CHAOS';

export interface UIState {
  current_session?: SimulationSession;
  layer_cursor: number;
  view_panel: ViewPanel;
  simulation_mode: SimulationMode;
  replay_speed: number;
  show_admin_controls: boolean;
  selected_agents: string[];
  selected_plugins: string[];
}

// WebSocket Event Types for Real-time Updates
export interface WSEvent {
  type: 'LAYER_UPDATE' | 'AGENT_ACTION' | 'MEMORY_PATCH' | 'FORK_DETECTED' | 'CONTAINMENT';
  data: unknown;
  timestamp: string;
  session_id: string;
}

export interface SimulationSessionData {
  id: string;
  // ... other minimal fields if truly needed elsewhere for partial data
}

export interface StartSimulationResponse {
  content: string; // Expected from GeminiResponse
  model: string;
  request_id: string; 
  session: SimulationSession; // Changed from SimulationSessionData to full SimulationSession
}
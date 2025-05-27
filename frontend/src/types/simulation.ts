/**
 * TypeScript type definitions for UKG/USKD Simulation System
 * Comprehensive typing for all simulation entities and states
 */

// Core simulation types
export type SimulationLayer = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type SimulationStatus = 
  | 'INITIALIZING'
  | 'READY' 
  | 'RUNNING' 
  | 'COMPLETED' 
  | 'CONTAINED' 
  | 'FAILED'
  | 'PAUSED';

export type LayerStatus = 
  | 'READY'
  | 'RUNNING'
  | 'COMPLETED'
  | 'ESCALATED'
  | 'CONTAINED'
  | 'FAILED';

export type ViewPanel = 
  | 'TRACE'
  | 'AGENTS'
  | 'PLUGINS'
  | 'CONFIDENCE'
  | 'MEMORY'
  | 'FORKS'
  | 'AUDIT';

export type SimulationMode = 
  | 'NORMAL'
  | 'STEPPING'
  | 'REPLAY'
  | 'RED_TEAM'
  | 'CHAOS';

export type AgentRole = 
  | 'RESEARCHER'
  | 'ANALYST'
  | 'CRITIC'
  | 'SYNTHESIZER'
  | 'GATEKEEPER'
  | 'VALIDATOR';

export type AgentStatus = 
  | 'INACTIVE'
  | 'ACTIVE'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'TERMINATED';

// Confidence and entropy scoring
export interface ConfidenceScore {
  layer: SimulationLayer;
  score: number;        // 0.0 to 1.0
  delta: number;        // Change from previous layer
  entropy?: number;     // Uncertainty measure
  timestamp?: string;
}

// Trace and logging
export interface TraceStep {
  id: string;
  timestamp: string;
  layer: SimulationLayer;
  layer_name: string;           // Added for TraceLog component
  message: string;
  event_type: string;           // Renamed from 'type' to match component
  data?: unknown;
  agent?: string;
  confidence?: ConfidenceScore;
  metadata?: Record<string, unknown>;
}

// Event types for trace logging
export type TraceEventType = 
  | 'simulation_start'
  | 'layer_entry'
  | 'layer_complete'
  | 'ai_interaction'
  | 'memory_patch'
  | 'agent_spawn'
  | 'agent_action'
  | 'fork_detected'
  | 'escalation'
  | 'containment'
  | 'confidence_update'
  | 'error'
  | 'info'
  | 'warning';

// Memory and knowledge graph
export interface MemoryCell {
  coordinate: number[];  // 13D coordinate
  value: unknown;
  version: number;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MemoryPatch {
  id: string;
  cell: string;
  coordinate: number[];
  before: unknown;
  after: unknown;
  layer: SimulationLayer;
  agent: string;
  timestamp: string;
  reason: string;
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
}

// Fork and branching
export interface ForkEvent {
  id: string;
  parent_layer: SimulationLayer;
  fork_layer: SimulationLayer;
  reason: string;
  agent: string;
  timestamp: string;
  branch_id: string;
  metadata?: Record<string, unknown>;
}

// Agents and personas - Updated to match backend AgentStatus
export interface Agent {
  id: string;
  name: string;
  role: string; // Changed from AgentRole to string to match backend
  persona: string; // Required field in backend
  active: boolean; // Added to match backend
  context: Record<string, any>; // Changed from unknown to any
  memory_trace: any[]; // Added to match backend
  created_at: string;
  // Optional frontend-only fields
  layer?: SimulationLayer;
  axes?: number[];
  trace?: TraceStep[];
  last_active?: string;
}

// Knowledge Algorithms (KAs)
export interface KnowledgeAlgorithm {
  id: string;
  name: string;
  description: string;
  version: string;
  active: boolean;
  type: string;
  params?: Record<string, unknown>;
  layers: SimulationLayer[];
  metadata?: Record<string, unknown>;
}

// Layer state and management
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
  start_time?: string;
  end_time?: string;
  duration?: number;
}

// Audit and compliance
export interface AuditCertEvent {
  id: string;
  runId: string;
  type: string;
  content: string;
  issuedBy: string;
  issuedAt: string;
  hash?: string;
  verified?: boolean;
}

// Main simulation session
export interface SimulationSession {
  id: string;
  run_id: string;
  created_at: string;
  status: SimulationStatus;
  layers_active: SimulationLayer[];
  current_layer: SimulationLayer;
  input_query: {
    user_query: string;
    context?: Record<string, unknown>;
    session_id: string;
  };
  layers: LayerState[];
  state: {
    created_timestamp: number;
    total_patches: number;
    total_forks: number;
    agents_spawned: string[];
    [key: string]: unknown;
  };
  final_output?: unknown;
  metadata?: Record<string, unknown>;
}

// API request/response types
export interface StartSimulationRequest {
  prompt: string;
  context?: Record<string, unknown>;
  axes?: number[];
  config?: Record<string, unknown>;
}

export interface AgentCreateRequest {
  name: string;
  role: string;
  persona?: string;
  axes?: number[];
  init_prompt?: string;
}

export interface StartSimulationResponse {
  content: string;
  model: string;
  request_id: string;
  session: SimulationSession;
}

export interface StepSimulationResponse {
  layer: SimulationLayer;
  status: LayerStatus;
  trace: TraceStep[];
  agents_spawned: string[];
  patches_applied: MemoryPatch[];
  confidence: ConfidenceScore;
  escalation_triggered: boolean;
  metadata?: Record<string, unknown>;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  timestamp: string;
  session_id?: string;
  data?: unknown;
}

export interface StatusUpdateMessage extends WebSocketMessage {
  type: 'status_update';
  status: SimulationStatus;
  session: SimulationSession;
}

export interface LayerCompleteMessage extends WebSocketMessage {
  type: 'layer_complete';
  layer: LayerState;
}

export interface TraceUpdateMessage extends WebSocketMessage {
  type: 'trace_update';
  trace_step: TraceStep;
}

export interface AgentSpawnMessage extends WebSocketMessage {
  type: 'agent_spawn';
  agent: Agent;
}

export interface MemoryPatchMessage extends WebSocketMessage {
  type: 'memory_patch';
  patch: MemoryPatch;
}

export interface ForkDetectedMessage extends WebSocketMessage {
  type: 'fork_detected';
  fork: ForkEvent;
}

export interface ContainmentTriggerMessage extends WebSocketMessage {
  type: 'containment_trigger';
  reason: string;
  layer: SimulationLayer;
  details: Record<string, unknown>;
}

// UI State types
export interface UIState {
  viewPanel: ViewPanel;
  simulationMode: SimulationMode;
  layerCursor: number;
  replaySpeed: number;
  showAdminControls: boolean;
  selectedAgents: string[];
  selectedPlugins: string[];
}

// Utility types
export type Coordinate13D = [number, number, number, number, number, number, number, number, number, number, number, number, number];

export interface PersonaMapping {
  persona: string;
  axes: number[];
  traits: string[];
  capabilities: string[];
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'error';
  sessions_count: number;
  websocket_connections: number;
  plugins_loaded: number;
  memory_usage?: number;
  uptime?: number;
}

// Error types
export interface SimulationError {
  code: string;
  message: string;
  layer?: SimulationLayer;
  session_id?: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

// Configuration types
export interface SimulationConfig {
  max_layers: number;
  confidence_threshold: number;
  entropy_threshold: number;
  max_agents: number;
  auto_escalation: boolean;
  containment_enabled: boolean;
  trace_level: 'MINIMAL' | 'NORMAL' | 'VERBOSE' | 'DEBUG';
}

export interface EventType {
  id: string;
  name: string;
  description: string;
  type: string;
}

// Export all types for easy importing
export type {
  // Re-export key types at top level
  SimulationSession as Session,
  LayerState as Layer,
  Agent,
  KnowledgeAlgorithm as Plugin,
  TraceStep as Trace,
  MemoryPatch as Patch,
  ForkEvent as Fork,
  ConfidenceScore as Confidence,
};

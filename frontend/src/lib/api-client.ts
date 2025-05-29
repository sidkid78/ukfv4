/**
 * API Client for UKG/USKD Simulation System
 * Handles all backend communication with type safety
 */

import { useEffect, useState } from 'react';


import { 
  SimulationLayer,
  LayerStatus,
  SimulationSession,
  Agent,
  KnowledgeAlgorithm,
  AuditCertEvent,
  MemoryCell,
  MemoryPatch,
  TraceStep,
  UIState,
  LayerState,
} from '@/types/simulation';


const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`; // Note: endpoints now include /api prefix
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`, 0);
  }
}

// Simulation API
export const simulationAPI = {  
  async start(payload: { prompt: string; context?: Record<string, unknown> }) {
    return apiRequest('/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getSession(sessionId: string): Promise<SimulationSession> {
    return apiRequest<SimulationSession>(`/api/simulation/session/${sessionId}`);
  },

  async listSessions(): Promise<SimulationSession[]> {
    return apiRequest<SimulationSession[]>('/api/simulation/sessions');
  },

  async step(sessionId: string) {
    return apiRequest(`/api/simulation/step/${sessionId}`, {
      method: 'POST',
    });
  },
};

// Agent API - Fixed to match backend endpoints
export const agentAPI = {
  async list(): Promise<Agent[]> {
    return apiRequest<Agent[]>('/api/agent/list');
  },

  async spawn(request: { name: string; role: string; persona?: string }): Promise<Agent> {
    return apiRequest<Agent>('/api/agent/spawn', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async kill(agentId: string): Promise<{ status: string; agent_id: string }> {
    return apiRequest(`/api/agent/${agentId}`, {
      method: 'DELETE',
    });
  },

  async getStatus(agentId: string): Promise<Agent> {
    return apiRequest<Agent>(`/api/agent/status/${agentId}`);
  },

  async setContext(agentId: string, context: Record<string, unknown>): Promise<{ ok: boolean }> {
    return apiRequest(`/api/agent/set_context/${agentId}`, {
      method: 'POST',
      body: JSON.stringify(context),
    });
  },
};

// Plugin API
export const pluginAPI = {
  async listKAs(): Promise<KnowledgeAlgorithm[]> {
    try {
      const response = await apiRequest<KnowledgeAlgorithm[] | { plugins: KnowledgeAlgorithm[] }>('/api/plugin/ka/list');
      console.log('Raw plugin API response:', response);
      
      // Handle different response formats from the backend
      if (Array.isArray(response)) {
        return response;
      } else if (response && Array.isArray(response.plugins)) {
        return response.plugins;
      } else {
        console.warn('Unexpected plugin API response format:', response);
        return [];
      }
    } catch (error) {
      console.error('Failed to list KAs:', error);
      throw error;
    }
  },

  async reloadKAs(): Promise<{ status: string; available: string[] }> {
    try {
      const response = await apiRequest<{ status: string; available_plugins?: string[]; available?: string[] }>('/api/plugin/ka/reload', {
        method: 'POST',
      });
      
      // Normalize response format
      return {
        status: response.status || 'unknown',
        available: response.available_plugins || response.available || []
      };
    } catch (error) {
      console.error('Failed to reload KAs:', error);
      throw error;
    }
  },

  async runKA(kaName: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    try {
      const requestPayload = {
        slice_input: payload,
        context: { ui_test: true, timestamp: new Date().toISOString() }
      };
      
      console.log(`Running KA ${kaName} with payload:`, requestPayload);
      
      const response = await apiRequest(`/api/plugin/ka/run/${encodeURIComponent(kaName)}`, {
        method: 'POST',
        body: JSON.stringify(requestPayload),
      });
      
      return response as Record<string, unknown>;
    } catch (error) {
      console.error(`Failed to run KA ${kaName}:`, error);
      throw error;
    }
  },

  // Additional helper methods for plugin management
  async getPluginDetails(pluginName: string): Promise<KnowledgeAlgorithm> {
    try {
      const plugins = await this.listKAs();
      const plugin = plugins.find(p => p.name === pluginName);
      if (!plugin) {
        throw new Error(`Plugin ${pluginName} not found`);
      }
      return plugin;
    } catch (error) {
      console.error(`Failed to get plugin details for ${pluginName}:`, error);
      throw error;
    }
  },

  async validatePlugin(pluginName: string): Promise<boolean> {
    try {
      const testPayload = {
        query: "validation_test",
        test_mode: true
      };
      
      const result = await this.runKA(pluginName, testPayload);
      return result && typeof result.confidence === 'number';
    } catch (error) {
      console.error(`Plugin validation failed for ${pluginName}:`, error);
      return false;
    }
  }
};

// Memory API
export const memoryAPI = {
  async getCell(coordinate: number[]): Promise<MemoryCell> {
    return apiRequest<MemoryCell>('/api/memory/cell', {
      method: 'POST',
      body: JSON.stringify({ coordinate }),
    });
  },

  async patchCell(patch: MemoryPatch): Promise<MemoryPatch> {
    return apiRequest<MemoryPatch>('/api/memory/patch', {
      method: 'POST',
      body: JSON.stringify(patch),
    });
  },

  async dumpAll(): Promise<MemoryCell[]> {
    return apiRequest<MemoryCell[]>('/api/memory/dump');
  },
};

// Audit API
export const auditAPI = {
  async getLog(filters?: {
    event_type?: string;
    layer?: number;
    persona?: string;
    after?: number;
    limit?: number;
    offset?: number;
  }): Promise<AuditCertEvent[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }
    const query = params.toString();
    return apiRequest<AuditCertEvent[]>(`/api/audit/log${query ? `?${query}` : ''}`);
  },

  async getBundle(after?: number): Promise<AuditCertEvent[]> {
    const query = after ? `?after=${after}` : '';
    return apiRequest<AuditCertEvent[]>(`/api/audit/bundle${query}`);
  },

  async getEntry(entryId: string): Promise<AuditCertEvent> {
    return apiRequest<AuditCertEvent>(`/api/audit/entry/${entryId}`);
  },
};

// Trace API
export const traceAPI = {
  async getTrace(runId: string): Promise<TraceStep[]> {
    return apiRequest<TraceStep[]>(`/api/trace/get/${runId}`);
  },

  async addTrace(runId: string, trace: TraceStep): Promise<{ ok: boolean }> {
    return apiRequest(`/api/trace/add/${runId}`, {
      method: 'POST',
      body: JSON.stringify(trace),
    });
  },
};

// UI State API
export const uiAPI = {
  async getState(): Promise<UIState> {
    return apiRequest<UIState>('/api/ui/state');
  },

  async getLayerStatus(): Promise<LayerStatus> {
    return apiRequest<LayerStatus>('/api/ui/layer_status');
  },
};

// Health Check
export const healthAPI = {
  async check(): Promise<{ status: string; service: string; plugins_loaded: number }> {
    return apiRequest('/health');
  },

  async agentHealth(): Promise<{ status: string; total_agents: number; active_agents: number }> {
    return apiRequest('/api/agent/health');
  },
};

// Layer simulation API
export const layerAPI = {
  async getLayerStatus(sessionId: string): Promise<LayerState[]> {
    try {
      const response = await apiRequest<LayerState[]>(`/api/simulation/layers/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Failed to get layer status:', error);
      throw error;
    }
  },

  async stepToLayer(sessionId: string, targetLayer: SimulationLayer): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/step-to-layer/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ target_layer: targetLayer }),
      });
      return response;
    } catch (error) {
      console.error(`Failed to step to layer ${targetLayer}:`, error);
      throw error;
    }
  },

  async pauseSimulation(sessionId: string): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/pause/${sessionId}`, {
        method: 'POST',
      });
      return response;
    } catch (error) {
      console.error('Failed to pause simulation:', error);
      throw error;
    }
  },

  async resumeSimulation(sessionId: string): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/resume/${sessionId}`, {
        method: 'POST',
      });
      return response;
    } catch (error) {
      console.error('Failed to resume simulation:', error);
      throw error;
    }
  },

  async escalateLayer(sessionId: string, layer: SimulationLayer, reason?: string): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/escalate/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ 
          layer, 
          reason: reason || 'Manual escalation triggered' 
        }),
      });
      return response;
    } catch (error) {
      console.error(`Failed to escalate layer ${layer}:`, error);
      throw error;
    }
  },

  async triggerContainment(sessionId: string, reason: string): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/contain/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
      });
      return response;
    } catch (error) {
      console.error('Failed to trigger containment:', error);
      throw error;
    }
  },

  async getLayerTrace(sessionId: string, layer: SimulationLayer): Promise<unknown[]> {
    try {
      const response = await apiRequest<unknown[]>(`/api/simulation/layer-trace/${sessionId}/${layer}`);
      return response;
    } catch (error) {
      console.error(`Failed to get trace for layer ${layer}:`, error);
      throw error;
    }
  },

  async getLayerAgents(sessionId: string, layer: SimulationLayer): Promise<unknown[]> {
    try {
      const response = await apiRequest<unknown[]>(`/api/simulation/layer-agents/${sessionId}/${layer}`);
      return response;
    } catch (error) {
      console.error(`Failed to get agents for layer ${layer}:`, error);
      throw error;
    }
  },

  async getLayerPlugins(sessionId: string, layer: SimulationLayer): Promise<unknown[]> {
    try {
      const response = await apiRequest<unknown[]>(`/api/simulation/layer-plugins/${sessionId}/${layer}`);
      return response;
    } catch (error) {
      console.error(`Failed to get plugins for layer ${layer}:`, error);
      throw error;
    }
  },

  async setSimulationMode(sessionId: string, mode: 'AUTO' | 'STEPPING' | 'MANUAL'): Promise<unknown> {
    try {
      const response = await apiRequest(`/api/simulation/mode/${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ mode }),
      });
      return response;
    } catch (error) {
      console.error(`Failed to set simulation mode to ${mode}:`, error);
      throw error;
    }
  }
};

// Update the existing simulationAPI with layer-specific methods
export const enhancedSimulationAPI = {
  ...simulationAPI,
  
  async runWithLayerControl(
    query: string, 
    options: {
      maxLayer?: SimulationLayer;
      stepMode?: boolean;
      safetyMode?: boolean;
      plugins?: string[];
    } = {}
  ): Promise<unknown> {
    try {
      const response = await apiRequest('/api/simulation/run-controlled', {
        method: 'POST',
        body: JSON.stringify({
          prompt: query,
          max_layer: options.maxLayer || 10,
          step_mode: options.stepMode || false,
          safety_mode: options.safetyMode || true,
          enabled_plugins: options.plugins || []
        }),
      });
      return response;
    } catch (error) {
      console.error('Failed to run controlled simulation:', error);
      throw error;
    }
  },

  async getSimulationState(sessionId: string): Promise<unknown> { 
    try {
      const response = await apiRequest(`/api/simulation/state/${sessionId}`);
      return response;
    } catch (error) {
      console.error('Failed to get simulation state:', error);
      throw error;
    }
  }
};

// WebSocket integration for real-time layer updates (re-enabled with correct URL)
export class LayerWebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string = '';
  private listeners: Map<string, ((data: unknown) => void)[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private isConnecting = false;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
    // Re-enable WebSocket with correct URL
    this.connect();
  }

  private connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return; // Already connecting or connected
    }
    
    this.isConnecting = true;
    // Generate a unique client ID for this connection
    const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/${this.sessionId}/${clientId}`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('Layer WebSocket connected to:', wsUrl);
        this.isConnecting = false;
        this.reconnectAttempts = 0; // Reset on successful connection
        this.emit('connected', { sessionId: this.sessionId });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('Layer WebSocket disconnected');
        this.isConnecting = false;
        this.emit('disconnected', {});
        
        // Attempt to reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        } else {
          console.log('Max reconnection attempts reached');
        }
      };

      this.ws.onerror = (error) => {
        console.error('Layer WebSocket error:', error);
        this.isConnecting = false;
        this.emit('error', { error });
        
        // Don't attempt reconnect on WebSocket errors for now
        // This prevents infinite error loops
        this.reconnectAttempts = this.maxReconnectAttempts;
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
    }
  }

  private handleMessage(data: unknown) {
    const { type, payload } = data as { type: string; payload: unknown };
    
    switch (type) {
      case 'layer_started':
        this.emit('layerStarted', payload);
        break;
      case 'layer_completed':
        this.emit('layerCompleted', payload);
        break;
      case 'layer_escalated':
        this.emit('layerEscalated', payload);
        break;
      case 'layer_forked':
        this.emit('layerForked', payload);
        break;
      case 'confidence_updated':
        this.emit('confidenceUpdated', payload);
        break;
      case 'agents_spawned':
        this.emit('agentsSpawned', payload);
        break;
      case 'containment_triggered':
        this.emit('containmentTriggered', payload);
        break;
      default:
        this.emit('message', data);
    }
  }

  public on(event: string, callback: (data: unknown) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  public off(event: string, callback: (data: unknown) => void) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: unknown) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners.clear();
  }

  public sendCommand(command: string, data: unknown = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'command',
        command,
        data,
        sessionId: this.sessionId
      }));
    }
  }
}

// React hook for layer WebSocket integration
export function useLayerWebSocket(sessionId: string) {
  const [wsManager, setWsManager] = useState<LayerWebSocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [layerUpdates, setLayerUpdates] = useState<unknown[]>([]);

  useEffect(() => {
    if (!sessionId) return;

    // Cleanup existing connection first
    if (wsManager) {
      wsManager.disconnect();
    }

    // Re-enable WebSocket manager with correct URL
    const manager = new LayerWebSocketManager(sessionId);
    
    manager.on('connected', () => setIsConnected(true));
    manager.on('disconnected', () => setIsConnected(false));
    
    manager.on('layerStarted', (data: unknown) => {
      setLayerUpdates(prev => [...prev, { type: 'started', ...(data as Record<string, unknown>) }]);
    });
    
    manager.on('layerCompleted', (data: unknown) => {
      setLayerUpdates(prev => [...prev, { type: 'completed', ...(data as Record<string, unknown>) }]);
    });
    
    manager.on('layerEscalated', (data: unknown) => {
      setLayerUpdates(prev => [...prev, { type: 'escalated', ...(data as Record<string, unknown>) }]);
    });

    setWsManager(manager);

    return () => {
      manager.disconnect();
    };
  }, [sessionId]); // Remove wsManager from dependencies to prevent recreation loop

  return {
    isConnected,
    layerUpdates,
    sendCommand: wsManager?.sendCommand.bind(wsManager),
    wsManager
  };
}

// Export enhanced APIs
export default {
  simulation:simulationAPI,
  enhanced: enhancedSimulationAPI,
  layer: layerAPI,
  agent: agentAPI,
  plugin: pluginAPI,
  memory: memoryAPI,
  audit: auditAPI,
  trace: traceAPI,
  ui: uiAPI,
  health: healthAPI,
};


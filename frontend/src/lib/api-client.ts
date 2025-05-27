/**
 * API Client for UKG/USKD Simulation System
 * Handles all backend communication with type safety
 */

import { 
  SimulationSession,
  Agent,
  KnowledgeAlgorithm,
  AuditCertEvent,
  MemoryCell,
  MemoryPatch,
  TraceStep,
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
  async start(payload: { prompt: string; context?: Record<string, any> }) {
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

  async setContext(agentId: string, context: Record<string, any>): Promise<{ ok: boolean }> {
    return apiRequest(`/api/agent/set_context/${agentId}`, {
      method: 'POST',
      body: JSON.stringify(context),
    });
  },
};

// Plugin API
export const pluginAPI = {
  async listKAs(): Promise<KnowledgeAlgorithm[]> {
    return apiRequest<KnowledgeAlgorithm[]>('/api/plugin/ka/list');
  },

  async reloadKAs(): Promise<{ status: string; available: string[] }> {
    return apiRequest('/api/plugin/ka/reload', {
      method: 'POST',
    });
  },

  async runKA(kaName: string, payload: any): Promise<any> {
    return apiRequest(`/api/plugin/ka/run/${kaName}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
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

  async getBundle(after?: number): Promise<any> {
    const query = after ? `?after=${after}` : '';
    return apiRequest(`/api/audit/bundle${query}`);
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
  async getState(): Promise<any> {
    return apiRequest('/api/ui/state');
  },

  async getLayerStatus(): Promise<any> {
    return apiRequest('/api/ui/layer_status');
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

// Export all APIs
export default {
  simulation: simulationAPI,
  agent: agentAPI,
  plugin: pluginAPI,
  memory: memoryAPI,
  audit: auditAPI,
  trace: traceAPI,
  ui: uiAPI,
  health: healthAPI,
};

/**
 * API Client for UKG/USKD Simulation System
 * Handles all backend communication with type safety
 */

import { 
  SimulationQuery, 
  SimulationRunResponse,
  LayerStepRequest,
  LayerStepResponse,
  Agent,
  AgentCreateRequest,
  KnowledgeAlgorithm,
  AuditCertEvent,
  SimulationSession 
  
} from '@/types/simulation';


const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}/api${endpoint}`;
  
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
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
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
  async run(query: SimulationQuery): Promise<SimulationRunResponse> {
    return apiRequest<SimulationRunResponse>('/simulation/run', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  },

  async step(request: LayerStepRequest): Promise<LayerStepResponse> {
    return apiRequest<LayerStepResponse>('/simulation/step', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async getSession(sessionId: string): Promise<SimulationSession> {
    return apiRequest<SimulationSession>(`/simulation/session/${sessionId}`);
  },

  async listSessions(): Promise<SimulationSession[]> {
    return apiRequest<SimulationSession[]>('/simulation/sessions');
  },

  async replay(sessionId: string, step: number): Promise<any> {
    return apiRequest(`/simulation/replay`, {
      method: 'POST',
      body: JSON.stringify({ run_id: sessionId, step }),
    });
  },
};

// Agent API
export const agentAPI = {
  async list(sessionId?: string): Promise<Agent[]> {
    const endpoint = sessionId ? `/agent/list?session_id=${sessionId}` : '/agent/list';
    return apiRequest<Agent[]>(endpoint);
  },

  async spawn(request: AgentCreateRequest): Promise<Agent> {
    return apiRequest<Agent>('/agent/spawn', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async kill(agentId: string): Promise<{ success: boolean }> {
    return apiRequest(`/agent/${agentId}`, {
      method: 'DELETE',
    });
  },

  async getStatus(agentId: string): Promise<Agent> {
    return apiRequest<Agent>(`/agent/${agentId}`);
  },
};

// Plugin API
export const pluginAPI = {
  async listKAs(): Promise<KnowledgeAlgorithm[]> {
    return apiRequest<KnowledgeAlgorithm[]>('/plugin/ka/list');
  },

  async reloadKAs(): Promise<{ status: string; available: string[] }> {
    return apiRequest('/plugin/ka/reload', {
      method: 'POST',
    });
  },

  async runKA(kaName: string, payload: any): Promise<any> {
    return apiRequest(`/plugin/ka/run/${kaName}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

// Memory API
export const memoryAPI = {
  async getCell(coordinate: number[]): Promise<any> {
    return apiRequest('/memory/cell', {
      method: 'POST',
      body: JSON.stringify({ coordinate }),
    });
  },

  async patchCell(patch: any): Promise<{ success: boolean }> {
    return apiRequest('/memory/patch', {
      method: 'POST',
      body: JSON.stringify(patch),
    });
  },

  async dumpAll(): Promise<any[]> {
    return apiRequest('/memory/dump');
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
    return apiRequest<AuditCertEvent[]>(`/audit/log${query ? `?${query}` : ''}`);
  },

  async getBundle(after?: number): Promise<any> {
    const query = after ? `?after=${after}` : '';
    return apiRequest(`/audit/bundle${query}`);
  },

  async getEntry(entryId: string): Promise<AuditCertEvent> {
    return apiRequest<AuditCertEvent>(`/audit/entry/${entryId}`);
  },
};

// WebSocket API
export class SimulationWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private onMessage?: (data: any) => void;
  private onError?: (error: Event) => void;
  private onClose?: () => void;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  connect(callbacks: {
    onMessage?: (data: any) => void;
    onError?: (error: Event) => void;
    onClose?: () => void;
  }) {
    this.onMessage = callbacks.onMessage;
    this.onError = callbacks.onError;
    this.onClose = callbacks.onClose;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage?.(data);
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.onError?.(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
      this.onClose?.();
    };
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
/**
 * API Client for UKG/USKD Simulation System
 * Handles all backend communication with type safety
 */

import { 
    SimulationQuery, 
    SimulationRunResponse,
    LayerStepResponse,
    AuditCertEvent,
    SimulationSession,
    LayerStepRequest,
    WSEvent,
    SimulationRequest,
    StartSimulationResponse,
    SimulationStatus,
    SimulationMode
  } from '@/types/simulation';
  
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
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
  
  export async function apiRequest<T = unknown>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
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
    async start(request: SimulationRequest): Promise<StartSimulationResponse> {
      const response = await apiRequest<StartSimulationResponse>('/api/simulation/start', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      console.log(response);
      return response;
    },

    async run(query: SimulationQuery): Promise<SimulationRunResponse> {
      return apiRequest<SimulationRunResponse>('/api/simulation/run', {
        method: 'POST',
        body: JSON.stringify(query),
      });
    },
  
    async step(request: LayerStepRequest): Promise<LayerStepResponse> {
      return apiRequest<LayerStepResponse>('/api/simulation/step', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
  
    async getSession(sessionId: string): Promise<SimulationSession> {
      return apiRequest<SimulationSession>(`/api/simulation/session/${sessionId}`);
    },
  
    async listSessions(): Promise<SimulationSession[]> {
      return apiRequest<SimulationSession[]>('/api/simulation/sessions');
    },

    async updateStatus(sessionId: string, status: SimulationStatus): Promise<SimulationSession> {
      return apiRequest<SimulationSession>(`/api/simulation/session/${sessionId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
    },

    async updateMode(sessionId: string, mode: SimulationMode): Promise<SimulationSession> {
      return apiRequest<SimulationSession>(`/api/simulation/session/${sessionId}/mode`, {
        method: 'PATCH',
        body: JSON.stringify({ mode }),
      });
    },
  
    async replay(sessionId: string, step: number): Promise<SimulationSession> {
      return apiRequest<SimulationSession>(`/api/simulation/replay`, {
        method: 'POST',
        body: JSON.stringify({ run_id: sessionId, step }),
      });
    },

    async cancel(sessionId: string): Promise<{ success: boolean }> {
      return apiRequest<{ success: boolean }>(`/api/simulation/session/${sessionId}/cancel`, {
        method: 'POST',
      });
    },

    async reset(sessionId: string): Promise<SimulationSession> {
      return apiRequest<SimulationSession>(`/api/simulation/session/${sessionId}/reset`, {
        method: 'POST',
      });
    },
  
    async patchCell(patch: unknown): Promise<{ success: boolean }> {
      return apiRequest('/memory/patch', {
        method: 'POST',
        body: JSON.stringify(patch),
      });
    },
  
    async dumpAll(): Promise<unknown[]> {
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
  
    async getBundle(after?: number): Promise<AuditCertEvent[]> {
      const query = after ? `?after=${after}` : '';
      return apiRequest<AuditCertEvent[]>(`/audit/bundle${query}`);
    },
  
    async getEntry(entryId: string): Promise<AuditCertEvent> {
      return apiRequest<AuditCertEvent>(`/audit/entry/${entryId}`);
    },
  };
  
  // WebSocket API
  export class SimulationWebSocket {
    private ws: WebSocket | null = null;
    private sessionId: string;
    private onMessage?: (data: WSEvent) => void;
    private onError?: (error: Event) => void;
    private onClose?: () => void;
  
    constructor(sessionId: string) {
      this.sessionId = sessionId;
    }
  
    connect(callbacks: {
      onMessage?: (data: WSEvent) => void;
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
          this.onMessage?.(data as WSEvent);
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
  
    send(data: Record<string, unknown> | WSEvent) {
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

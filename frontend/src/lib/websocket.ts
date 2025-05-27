function generateClientId(): string {
  // Simple UUID v4 generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private clientId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: string[] = [];
  private listeners: Map<string, ((data: unknown) => void)[]> = new Map();

  constructor(sessionId: string, clientId?: string) {
    this.sessionId = sessionId;
    this.clientId = clientId || generateClientId();
    this.connect();
  }

  private connect() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/simulation/ws/${this.sessionId}`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  private handleOpen() {
    console.log(`WebSocket connected for session ${this.sessionId}`);
    this.reconnectAttempts = 0;
    
    // Send queued messages
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws?.send(message);
      }
    }
    
    // Start heartbeat
    this.startHeartbeat();
    
    // Notify listeners
    this.emit('connected', { sessionId: this.sessionId });
  }

  private handleMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      switch (data.type) {
        case 'status_update':
          this.emit('status_update', data);
          break;
        case 'layer_complete':
          this.emit('layer_complete', data);
          break;
        case 'trace_update':
          this.emit('trace_update', data);
          break;
        case 'agent_spawn':
          this.emit('agent_spawn', data);
          break;
        case 'memory_patch':
          this.emit('memory_patch', data);
          break;
        case 'fork_detected':
          this.emit('fork_detected', data);
          break;
        case 'containment_trigger':
          this.emit('containment_trigger', data);
          break;
        case 'heartbeat':
          // Respond to heartbeat
          this.send({ type: 'heartbeat_response', timestamp: Date.now() });
          break;
        default:
          this.emit('message', data);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent) {
    console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
    this.stopHeartbeat();
    
    if (event.code !== 1000) { // Not a normal closure
      this.scheduleReconnect();
    }
    
    this.emit('disconnected', { code: event.code, reason: event.reason });
  }

  private handleError(error: Event) {
    console.error('WebSocket error:', error);
    this.emit('error', error);
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() });
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public send(data: unknown) {
    const message = JSON.stringify(data);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      // Queue message for later
      this.messageQueue.push(message);
    }
  }

  public on(event: string, callback: (data: unknown) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)?.push(callback);
  }

  public off(event: string, callback: (data: unknown) => void) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(callback);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: unknown) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error);
        }
      });
    }
  }

  public disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  public getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }
}

// React hook for WebSocket integration
import { useEffect, useRef } from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import type { LayerState, TraceStep, Agent, MemoryPatch, ForkEvent } from '@/types/simulation';

// Define a type for expected WebSocket messages
interface WebSocketMessage {
  session?: unknown;
  status?: string;
  layer?: LayerState;
  trace_step?: TraceStep;
  agent?: Agent;
  patch?: MemoryPatch;
  fork?: ForkEvent;
  id?: string;
}

export function useWebSocket(sessionId: string) {
  const wsRef = useRef<WebSocketManager | null>(null);
  const {
    setWsConnected,
    addTraceStep,
    updateLayer,
    addAgent,
    addPatch,
    addFork,
    addAuditEvent,
  } = useSimulationStore();

  useEffect(() => {
    // Only connect if we have a valid session ID
    if (!sessionId || sessionId.trim() === '') {
      console.log('No session ID provided, skipping WebSocket connection');
      return;
    }

    console.log(`Connecting WebSocket for session: ${sessionId}`);
    
    // Create WebSocket manager
    wsRef.current = new WebSocketManager(sessionId);
    const ws = wsRef.current;

    // Set up event listeners
    ws.on('connected', () => {
      setWsConnected(true);
    });

    ws.on('disconnected', () => {
      setWsConnected(false);
    });

    ws.on('status_update', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.session) {
        // Update session in store
        console.log('Session status update:', msg.status);
      }
    });

    ws.on('layer_complete', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.layer) {
        updateLayer(msg.layer.layer, msg.layer);
      }
    });

    ws.on('trace_update', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.trace_step) {
        addTraceStep(msg.trace_step);
      }
    });

    ws.on('agent_spawn', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.agent) {
        addAgent(msg.agent);
      }
    });

    ws.on('memory_patch', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.patch) {
        addPatch(msg.patch);
      }
    });

    ws.on('fork_detected', (data: unknown) => {
      const msg = data as WebSocketMessage;
      if (msg.fork) {
        addFork(msg.fork);
      }
    });

    ws.on('containment_trigger', (data: unknown) => {
      const msg = data as WebSocketMessage;
      console.warn('CONTAINMENT TRIGGERED:', msg);
      addAuditEvent({
        id: msg.id || Date.now().toString(),
        runId: sessionId,
        type: 'CONTAINMENT',
        content: JSON.stringify(msg),
        issuedBy: 'system',
        issuedAt: new Date().toISOString(),
      });
    });

    // Cleanup on unmount
    return () => {
      ws.disconnect();
      setWsConnected(false);
    };
  }, [
    sessionId,
    setWsConnected,
    addTraceStep,
    updateLayer,
    addAgent,
    addPatch,
    addFork,
    addAuditEvent,
  ]);

  return {
    send: (data: unknown) => wsRef.current?.send(data),
    connectionState: wsRef.current?.getConnectionState() || 'DISCONNECTED',
  };
}

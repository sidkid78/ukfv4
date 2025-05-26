/**
 * Central state management for UKG/USKD Simulation System
 * Using Zustand for reactive state with TypeScript
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { 
  SimulationSession,
  LayerState,
  TraceStep,
  Agent,
  KnowledgeAlgorithm,
  MemoryPatch,
  ForkEvent,
  AuditCertEvent,
  ViewPanel,
  SimulationMode,
  ConfidenceScore
} from '@/types/simulation';

interface SimulationState {
  // Core Session Data
  currentSession: SimulationSession | null;
  sessions: SimulationSession[];
  
  // Layer Management
  layers: LayerState[];
  currentLayer: number;
  layerCursor: number;
  
  // Trace & Audit
  trace: TraceStep[];
  patches: MemoryPatch[];
  forks: ForkEvent[];
  auditEvents: AuditCertEvent[];
  
  // Agents & Plugins
  agents: Agent[];
  plugins: KnowledgeAlgorithm[];
  
  // UI State
  viewPanel: ViewPanel;
  simulationMode: SimulationMode;
  replaySpeed: number;
  showAdminControls: boolean;
  selectedAgents: string[];
  selectedPlugins: string[];
  
  // WebSocket Connection
  wsConnected: boolean;
  
  // Loading States
  isLoading: boolean;
  isRunningSimulation: boolean;
  isSteppingLayer: boolean;
}

interface SimulationActions {
  // Session Management
  setCurrentSession: (session: SimulationSession | null) => void;
  addSession: (session: SimulationSession) => void;
  updateSession: (sessionId: string, updates: Partial<SimulationSession>) => void;
  
  // Layer Management
  setLayers: (layers: LayerState[]) => void;
  updateLayer: (layerNumber: number, updates: Partial<LayerState>) => void;
  setLayerCursor: (cursor: number) => void;
  setCurrentLayer: (layer: number) => void;
  
  // Trace & Events
  setTrace: (trace: TraceStep[]) => void;
  addTraceStep: (step: TraceStep) => void;
  setPatches: (patches: MemoryPatch[]) => void;
  addPatch: (patch: MemoryPatch) => void;
  setForks: (forks: ForkEvent[]) => void;
  addFork: (fork: ForkEvent) => void;
  setAuditEvents: (events: AuditCertEvent[]) => void;
  addAuditEvent: (event: AuditCertEvent) => void;
  
  // Agents & Plugins
  setAgents: (agents: Agent[]) => void;
  addAgent: (agent: Agent) => void;
  removeAgent: (agentId: string) => void;
  updateAgent: (agentId: string, updates: Partial<Agent>) => void;
  setPlugins: (plugins: KnowledgeAlgorithm[]) => void;
  updatePlugin: (pluginId: string, updates: Partial<KnowledgeAlgorithm>) => void;
  
  // UI Actions
  setViewPanel: (panel: ViewPanel) => void;
  setSimulationMode: (mode: SimulationMode) => void;
  setReplaySpeed: (speed: number) => void;
  toggleAdminControls: () => void;
  setSelectedAgents: (agentIds: string[]) => void;
  setSelectedPlugins: (pluginIds: string[]) => void;
  
  // WebSocket
  setWsConnected: (connected: boolean) => void;
  
  // Loading States
  setLoading: (loading: boolean) => void;
  setRunningSimulation: (running: boolean) => void;
  setSteppingLayer: (stepping: boolean) => void;
  
  // Utility Actions
  reset: () => void;
  resetSession: () => void;
  getLayerByNumber: (layerNumber: number) => LayerState | undefined;
  getCurrentLayerState: () => LayerState | undefined;
  getConfidenceHistory: () => ConfidenceScore[];
}

type SimulationStore = SimulationState & SimulationActions;

const initialState: SimulationState = {
  // Core Session Data
  currentSession: null,
  sessions: [],
  
  // Layer Management
  layers: [],
  currentLayer: 1,
  layerCursor: 0,
  
  // Trace & Audit
  trace: [],
  patches: [],
  forks: [],
  auditEvents: [],
  
  // Agents & Plugins
  agents: [],
  plugins: [],
  
  // UI State
  viewPanel: 'TRACE',
  simulationMode: 'NORMAL',
  replaySpeed: 1,
  showAdminControls: false,
  selectedAgents: [],
  selectedPlugins: [],
  
  // WebSocket Connection
  wsConnected: false,
  
  // Loading States
  isLoading: false,
  isRunningSimulation: false,
  isSteppingLayer: false,
};

export const useSimulationStore = create<SimulationStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,
      
      // Session Management
      setCurrentSession: (session) => 
        set({ currentSession: session }, false, 'setCurrentSession'),
      
      addSession: (session) =>
        set((state) => ({ 
          sessions: [...state.sessions, session],
          currentSession: session 
        }), false, 'addSession'),
      
      updateSession: (sessionId, updates) =>
        set((state) => ({
          sessions: state.sessions.map(s => 
            s.id === sessionId ? { ...s, ...updates } : s
          ),
          currentSession: state.currentSession?.id === sessionId 
            ? { ...state.currentSession, ...updates }
            : state.currentSession
        }), false, 'updateSession'),
      
      // Layer Management
      setLayers: (layers) => 
        set({ layers }, false, 'setLayers'),
      
      updateLayer: (layerNumber, updates) =>
        set((state) => ({
          layers: state.layers.map(layer =>
            layer.layer === layerNumber ? { ...layer, ...updates } : layer
          )
        }), false, 'updateLayer'),
      
      setLayerCursor: (cursor) => 
        set({ layerCursor: Math.max(0, cursor) }, false, 'setLayerCursor'),
      
      setCurrentLayer: (layer) => 
        set({ currentLayer: layer }, false, 'setCurrentLayer'),
      
      // Trace & Events
      setTrace: (trace) => 
        set({ trace }, false, 'setTrace'),
      
      addTraceStep: (step) =>
        set((state) => ({ 
          trace: [...state.trace, step] 
        }), false, 'addTraceStep'),
      
      setPatches: (patches) => 
        set({ patches }, false, 'setPatches'),
      
      addPatch: (patch) =>
        set((state) => ({ 
          patches: [...state.patches, patch] 
        }), false, 'addPatch'),
      
      setForks: (forks) => 
        set({ forks }, false, 'setForks'),
      
      addFork: (fork) =>
        set((state) => ({ 
          forks: [...state.forks, fork] 
        }), false, 'addFork'),
      
      setAuditEvents: (events) => 
        set({ auditEvents: events }, false, 'setAuditEvents'),
      
      addAuditEvent: (event) =>
        set((state) => ({ 
          auditEvents: [...state.auditEvents, event] 
        }), false, 'addAuditEvent'),
      
      // Agents & Plugins
      setAgents: (agents) => 
        set({ agents }, false, 'setAgents'),
      
      addAgent: (agent) =>
        set((state) => ({ 
          agents: [...state.agents, agent] 
        }), false, 'addAgent'),
      
      removeAgent: (agentId) =>
        set((state) => ({
          agents: state.agents.filter(a => a.id !== agentId),
          selectedAgents: state.selectedAgents.filter(id => id !== agentId)
        }), false, 'removeAgent'),
      
      updateAgent: (agentId, updates) =>
        set((state) => ({
          agents: state.agents.map(agent =>
            agent.id === agentId ? { ...agent, ...updates } : agent
          )
        }), false, 'updateAgent'),
      
      setPlugins: (plugins) => 
        set({ plugins }, false, 'setPlugins'),
      
      updatePlugin: (pluginId, updates) =>
        set((state) => ({
          plugins: state.plugins.map(plugin =>
            plugin.id === pluginId ? { ...plugin, ...updates } : plugin
          )
        }), false, 'updatePlugin'),
      
      // UI Actions
      setViewPanel: (panel) => 
        set({ viewPanel: panel }, false, 'setViewPanel'),
      
      setSimulationMode: (mode) => 
        set({ simulationMode: mode }, false, 'setSimulationMode'),
      
      setReplaySpeed: (speed) => 
        set({ replaySpeed: Math.max(0.1, Math.min(5, speed)) }, false, 'setReplaySpeed'),
      
      toggleAdminControls: () =>
        set((state) => ({ 
          showAdminControls: !state.showAdminControls 
        }), false, 'toggleAdminControls'),
      
      setSelectedAgents: (agentIds) => 
        set({ selectedAgents: agentIds }, false, 'setSelectedAgents'),
      
      setSelectedPlugins: (pluginIds) => 
        set({ selectedPlugins: pluginIds }, false, 'setSelectedPlugins'),
      
      // WebSocket
      setWsConnected: (connected) => 
        set({ wsConnected: connected }, false, 'setWsConnected'),
      
      // Loading States
      setLoading: (loading) => 
        set({ isLoading: loading }, false, 'setLoading'),
      
      setRunningSimulation: (running) => 
        set({ isRunningSimulation: running }, false, 'setRunningSimulation'),
      
      setSteppingLayer: (stepping) => 
        set({ isSteppingLayer: stepping }, false, 'setSteppingLayer'),
      
      // Utility Actions
      reset: () => 
        set(initialState, false, 'reset'),
      
      resetSession: () =>
        set({
          currentSession: null,
          layers: [],
          currentLayer: 1,
          layerCursor: 0,
          trace: [],
          patches: [],
          forks: [],
          agents: [],
          viewPanel: 'TRACE',
          simulationMode: 'NORMAL',
          selectedAgents: [],
          selectedPlugins: [],
        }, false, 'resetSession'),
      
      getLayerByNumber: (layerNumber) => {
        const state = get();
        return state.layers.find(layer => layer.layer === layerNumber);
      },
      
      getCurrentLayerState: () => {
        const state = get();
        return state.layers[state.layerCursor];
      },
      
      getConfidenceHistory: () => {
        const state = get();
        return state.layers.map(layer => layer.confidence);
      },
    })),
    {
      name: 'simulation-store',
      partialize: (state: SimulationState) => ({
        // Persist only essential data
        sessions: state.sessions,
        viewPanel: state.viewPanel,
        simulationMode: state.simulationMode,
        replaySpeed: state.replaySpeed,
        showAdminControls: state.showAdminControls,
      }),
    }
  )
);

// Selectors for optimized component subscriptions
export const useCurrentSession = () => 
  useSimulationStore((state) => state.currentSession);

export const useCurrentLayer = () => 
  useSimulationStore((state) => state.getCurrentLayerState());

export const useLayers = () => 
  useSimulationStore((state) => state.layers);

export const useTrace = () => 
  useSimulationStore((state) => state.trace);

export const useAgents = () => 
  useSimulationStore((state) => state.agents);

export const usePlugins = () => 
  useSimulationStore((state) => state.plugins);

export const useUIState = () => 
  useSimulationStore((state) => ({
    viewPanel: state.viewPanel,
    simulationMode: state.simulationMode,
    replaySpeed: state.replaySpeed,
    showAdminControls: state.showAdminControls,
    layerCursor: state.layerCursor,
  }));

export const useLoadingStates = () =>
  useSimulationStore((state) => ({
    isLoading: state.isLoading,
    isRunningSimulation: state.isRunningSimulation,
    isSteppingLayer: state.isSteppingLayer,
  }));

// Hook for WebSocket integration
export const useWebSocketConnection = () => {
  const { wsConnected, setWsConnected } = useSimulationStore();
  return { wsConnected, setWsConnected };
};
'use client';

import React, { useEffect, useState } from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import { simulationAPI, SimulationWebSocket } from '@/lib/api-client';
import { LayerTimeline } from './layer-timeline';
import { LayerPanel } from './layer-panel';
import { TraceConsole } from './trace-console';
import { ConfidenceMeter } from './confidence-meter';
import { ReplayControls } from './replay-controls';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Settings, Play, Pause } from 'lucide-react';

interface SimulationSessionProps {
  sessionId: string;
}

export function SimulationSession({ sessionId }: SimulationSessionProps) {
  const {
    currentSession,
    setCurrentSession,
    layers,
    setLayers,
    simulationMode,
    setSimulationMode,
    isRunningSimulation,
    setRunningSimulation,
    wsConnected,
    setWsConnected,
  } = useSimulationStore();

  const [ws, setWs] = useState<SimulationWebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load session data on mount
  useEffect(() => {
    const loadSession = async () => {
      try {
        const session = await simulationAPI.getSession(sessionId);
        setCurrentSession(session);
        setLayers(session.layers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session');
      }
    };

    loadSession();
  }, [sessionId, setCurrentSession, setLayers]);

  // Setup WebSocket connection
  useEffect(() => {
    if (!sessionId) return;

    const websocket = new SimulationWebSocket(sessionId);
    websocket.connect({
      onMessage: (data) => {
        // Handle real-time updates
        console.log('WebSocket message:', data);
        // Update store based on message type
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      },
      onClose: () => {
        setWsConnected(false);
      },
    });

    setWs(websocket);
    setWsConnected(true);

    return () => {
      websocket.disconnect();
      setWs(null);
      setWsConnected(false);
    };
  }, [sessionId, setWsConnected]);

  const handleToggleSimulation = () => {
    if (isRunningSimulation) {
      setRunningSimulation(false);
      setSimulationMode('STEPPING');
    } else {
      setRunningSimulation(true);
      setSimulationMode('NORMAL');
      // Start simulation via API
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="max-w-md bg-white p-6 rounded-lg shadow-lg text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Session Load Error</h2>
          <p className="text-slate-600 mb-4">{error}</p>
          <Button onClick={() => window.location.href = '/simulation'}>
            Back to Simulation Center
          </Button>
        </div>
      </div>
    );
  }

  if (!currentSession) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Simulation Session
            </h1>
            <p className="text-slate-600 mt-1">
              {currentSession.input_query.user_query}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              {wsConnected ? 'Connected' : 'Disconnected'}
            </div>
            
            {/* Control Buttons */}
            <Button
              variant="outline"
              onClick={handleToggleSimulation}
              className="flex items-center gap-2"
            >
              {isRunningSimulation ? (
                <>
                  <Pause className="h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Resume
                </>
              )}
            </Button>
            
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 space-y-6">
        {/* Layer Timeline */}
        <LayerTimeline />
        
        {/* Control Panel */}
        <ReplayControls />
        
        {/* Main Panel and Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Layer Details Panel */}
          <div className="lg:col-span-3">
            <LayerPanel />
          </div>
          
          {/* Confidence Meter Sidebar */}
          <div className="space-y-4">
            <ConfidenceMeter />
            
            {/* Session Info */}
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="font-medium mb-2">Session Info</h3>
              <div className="space-y-1 text-sm text-slate-600">
                <div>Status: <span className="font-medium">{currentSession.status}</span></div>
                <div>Layer: <span className="font-medium">{currentSession.current_layer}/10</span></div>
                <div>Agents: <span className="font-medium">{layers.reduce((acc, l) => acc + l.agents.length, 0)}</span></div>
                <div>Started: <span className="font-medium">{new Date(currentSession.created_at).toLocaleString()}</span></div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Trace Console */}
        <TraceConsole />
      </div>
    </div>
  );
}

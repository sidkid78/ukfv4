'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
// import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSimulationStore } from '@/state/useSimulationStore';
import { LayerTimeline } from '@/components/LayerTimeline';
import { TraceLog } from '@/components/TraceLog';
import { ConfidenceMeter } from '@/components/ConfidenceMeter';
import { AgentPanel } from '@/components/AgentPanel';
import { PluginPanel } from '@/components/PluginPanel';
import { useWebSocket } from '@/lib/websocket';
import { TraceStep, ViewPanel } from '@/types/simulation';

export default function SimulationPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  
  const {
    currentSession,
    layers,
    // currentLayer,
    layerCursor,
    // trace,
    agents,
    plugins,
    viewPanel,
    isRunningSimulation,
    setCurrentSession,
    setLayers,
    setViewPanel,
    setRunningSimulation,
  } = useSimulationStore();

  const [query, setQuery] = useState('');
  const [sessionExists, setSessionExists] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Only connect WebSocket AFTER session is confirmed to exist
  const { connectionState } = useWebSocket(
    sessionExists ? sessionId : ''
  );

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId]);

  const loadSession = async (id: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log(`Loading session: ${id}`);
      const response = await fetch(`/api/simulation/session/${id}`);
      
      if (response.ok) {
        const session = await response.json();
        console.log('Session loaded:', session);
        
        setCurrentSession(session);
        setLayers(session.layers || []);
        setQuery(session.input_query?.user_query || '');
        setSessionExists(true); // This will trigger WebSocket connection
        
      } else if (response.status === 404) {
        setError(`Session ${id} not found. It may have expired or never existed.`);
        setSessionExists(false);
      } else {
        throw new Error(`Failed to load session: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
      setError(`Failed to load session: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setSessionExists(false);
    } finally {
      setIsLoading(false);
    }
  };

  const startSimulation = async () => {
    if (!query.trim()) return;
    
    setRunningSimulation(true);
    try {
      const response = await fetch('/api/simulation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: query,
          context: {}
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setCurrentSession(result.session);
        setLayers(result.session.layers || []);
        setSessionExists(true);
      } else {
        throw new Error(`Failed to start simulation: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to start simulation:', error);
      setError(`Failed to start simulation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setRunningSimulation(false);
    }
  };

  const stepToNextLayer = async () => {
    if (!currentSession) return;
    
    try {
      const response = await fetch(`/api/simulation/step/${currentSession.id}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Reload the session to get updated data
        await loadSession(currentSession.id);
      } else {
        throw new Error(`Failed to step simulation: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to step simulation:', error);
      setError(`Failed to step simulation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading simulation session...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-800">Session Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-700 mb-4">{error}</p>
              <div className="flex gap-2">
                <Button onClick={() => loadSession(sessionId)} variant="outline">
                  Retry Loading
                </Button>
                <Button onClick={() => window.location.href = '/simulation'}>
                  Back to Home
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              UKG/USKD Simulation Engine
            </h1>
            <p className="text-slate-600">
              Multi-layered AGI-safe reasoning system
            </p>
          </div>
          
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-green-50 text-green-700">
              {layers.length} Layers Active
            </Badge>
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {agents.length} Agents
            </Badge>
            <Badge variant="outline" className="bg-purple-50 text-purple-700">
              {plugins.length} Plugins
            </Badge>
            <Badge 
              variant="outline" 
              className={connectionState === 'CONNECTED' ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-700"}
            >
              WS: {connectionState}
            </Badge>
          </div>
        </div>

        {/* Query Input */}
        <Card>
          <CardHeader>
            <CardTitle>Simulation Query</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Input
                placeholder="Enter your query for the simulation engine..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isRunningSimulation) {
                    startSimulation();
                  }
                }}
              />
              <Button 
                onClick={startSimulation}
                disabled={isRunningSimulation || !query.trim()}
                className="min-w-[120px]"
              >
                {isRunningSimulation ? 'Running...' : 'Start Simulation'}
              </Button>
              <Button 
                variant="outline"
                onClick={stepToNextLayer}
                disabled={!currentSession || isRunningSimulation}
              >
                Step Layer
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Layer Timeline */}
        {layers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Layer Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <LayerTimeline layers={layers} currentLayer={layerCursor} />
            </CardContent>
          </Card>
        )}

        {/* Main Content Tabs */}
        <Tabs value={viewPanel} onValueChange={(value: string) => setViewPanel(value as ViewPanel)}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="TRACE">Trace Log</TabsTrigger>
            <TabsTrigger value="AGENTS">Agents</TabsTrigger>
            <TabsTrigger value="PLUGINS">Plugins</TabsTrigger>
            <TabsTrigger value="CONFIDENCE">Confidence</TabsTrigger>
            <TabsTrigger value="MEMORY">Memory</TabsTrigger>
          </TabsList>

          <TabsContent value="TRACE" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Simulation Trace</CardTitle>
              </CardHeader>
              <CardContent>
                <TraceLog 
                  trace={currentSession?.state?.global_trace as TraceStep[]} 
                  autoScroll={true}
                  showFilters={true}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="AGENTS" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Active Agents</CardTitle>
              </CardHeader>
              <CardContent>
                <AgentPanel agents={agents} sessionId={sessionId} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="PLUGINS" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Knowledge Algorithms</CardTitle>
              </CardHeader>
              <CardContent>
                <PluginPanel plugins={plugins} sessionId={sessionId} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="CONFIDENCE" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Confidence Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <ConfidenceMeter layers={layers} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="MEMORY" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Memory Graph</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-slate-500">
                  Memory visualization coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Session Info */}
        {currentSession && (
          <Card>
            <CardHeader>
              <CardTitle>Session Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">Session ID:</span>
                  <p className="text-slate-600 font-mono">{currentSession.id}</p>
                </div>
                <div>
                  <span className="font-medium">Status:</span>
                  <p className="text-slate-600">{currentSession.status}</p>
                </div>
                <div>
                  <span className="font-medium">Current Layer:</span>
                  <p className="text-slate-600">{currentSession.current_layer}</p>
                </div>
                <div>
                  <span className="font-medium">Created:</span>
                  <p className="text-slate-600">
                    {new Date(currentSession.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

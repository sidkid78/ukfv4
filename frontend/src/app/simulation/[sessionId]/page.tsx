'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { AgentPanel } from '@/components/AgentPanel';
import { PluginPanel } from '@/components/PluginPanel';
import { ConfidenceMeter } from '@/components/ConfidenceMeter';
import { TraceLog } from '@/components/TraceLog';
import { LayerTimeline } from '@/components/LayerTimeline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Shield } from 'lucide-react';
import { agentAPI, pluginAPI, traceAPI, layerAPI, useLayerWebSocket } from '@/lib/api-client';
import { 
  Agent, 
  KnowledgeAlgorithm, 
  LayerState, 
  SimulationLayer, 
  TraceStep,
  LayerStatus,
  ConfidenceScore 
} from '@/types/simulation';
import { ChatWindow } from '@/components/ChatWindow';

interface RawPlugin {
  name?: string;
  meta?: {
    description?: string;
    version?: string;
    active?: boolean;
    type?: string;
    params?: Record<string, unknown>;
    layers?: number[];
    [key: string]: unknown;
  };
}

// Enhanced LayerState interface for LayerTimeline integration
interface ExtendedLayerState {
  layer: SimulationLayer;
  name: string;
  status: LayerStatus;
  confidence?: ConfidenceScore;
  processing_time?: number;
  escalated?: boolean;
  forked?: boolean;
  contained?: boolean;
  agents_active?: number;
  plugins_active?: string[];
  start_time?: string;
  end_time?: string;
}

export default function SimulationSessionPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  
  // State management
  const [agents, setAgents] = useState<Agent[]>([]);
  const [plugins, setPlugins] = useState<KnowledgeAlgorithm[]>([]);
  const [traces, setTraces] = useState<TraceStep[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline');

  // Layer Timeline specific state
  const [layers, setLayers] = useState<ExtendedLayerState[]>([]);
  const [currentLayer, setCurrentLayer] = useState<SimulationLayer>(1);
  const [simulationMode, setSimulationMode] = useState<'AUTO' | 'STEPPING' | 'REPLAY'>('AUTO');

  // WebSocket connection for real-time updates
  const { isConnected, layerUpdates } = useLayerWebSocket(sessionId);

  // Handle WebSocket layer updates
  useEffect(() => {
    if (layerUpdates.length > 0) {
      const latestUpdate = layerUpdates[layerUpdates.length - 1];
      console.log('Received layer update:', latestUpdate);
      
      // Refresh layer status when we receive updates
      if (latestUpdate.type === 'started' || latestUpdate.type === 'completed' || latestUpdate.type === 'escalated') {
        loadLayerStatus();
      }
    }
  }, [layerUpdates]);

  // Load layer status from backend
  const loadLayerStatus = async () => {
    if (!sessionId) return;
    try {
      const layerData = await layerAPI.getLayerStatus(sessionId);
      const transformedLayers: ExtendedLayerState[] = layerData.map(layer => ({
        layer: layer.layer as SimulationLayer,
        name: layer.name,
        status: layer.status as LayerStatus,
        confidence: layer.confidence ? {
          layer: layer.layer as SimulationLayer,
          score: layer.confidence.score || 0,
          delta: layer.confidence.delta || 0,
          entropy: layer.confidence.entropy || 0
        } : undefined,
        processing_time: layer.processing_time,
        escalated: layer.escalated,
        forked: layer.forked,
        contained: layer.contained,
        agents_active: layer.agents_active,
        plugins_active: layer.plugins_active,
        start_time: layer.start_time,
        end_time: layer.end_time
      }));
      setLayers(transformedLayers);
      
      // Find current running layer or default to 1
      const runningLayer = transformedLayers.find(l => l.status === 'RUNNING');
      if (runningLayer) {
        setCurrentLayer(runningLayer.layer);
      }
    } catch (error) {
      console.error('Failed to load layer status:', error);
      // Fallback to mock data on error
      const fallbackLayers: ExtendedLayerState[] = [
        {
          layer: 1,
          name: 'Simulation Entry',
          status: 'COMPLETED',
          confidence: { layer: 1, score: 0.95, delta: 0, entropy: 0.05 },
          processing_time: 0.12,
          agents_active: 0,
          plugins_active: ['query_analyzer_ka']
        }
      ];
      setLayers(fallbackLayers);
      setCurrentLayer(1);
    }
  };

  // Initialize layer states
  useEffect(() => {
    loadLayerStatus();
  }, [sessionId]);

  // Periodic refresh for layer status
  useEffect(() => {
    if (!sessionId || simulationMode !== 'AUTO') return;
    
    const refreshInterval = setInterval(() => {
      loadLayerStatus();
    }, 5000); // Refresh every 5 seconds in AUTO mode
    
    return () => clearInterval(refreshInterval);
  }, [sessionId, simulationMode]);

  // Load all data on mount
  useEffect(() => {
    if (sessionId) {
      const loadAllData = async () => {
        try {
          setIsLoading(true);
          
          // Load agents, plugins, and traces in parallel
          const [agentsData, pluginsData, tracesData] = await Promise.allSettled([
            agentAPI.list(),
            pluginAPI.listKAs(),
            traceAPI.getTrace(sessionId).catch(() => []), // Handle 404 gracefully
          ]);

          // Handle agents
          if (agentsData.status === 'fulfilled') {
            setAgents(agentsData.value);
          }

          // Handle plugins - transform the response to match KnowledgeAlgorithm interface
          if (pluginsData.status === 'fulfilled') {
            const transformedPlugins: KnowledgeAlgorithm[] = pluginsData.value.map((plugin: RawPlugin, index: number) => ({
              id: plugin.name || `plugin-${index}`,
              name: plugin.name || `Unknown Plugin ${index}`,
              description: plugin.meta?.description || 'No description available',
              version: plugin.meta?.version || '1.0.0',
              active: plugin.meta?.active !== false,
              type: plugin.meta?.type || 'KA',
              params: plugin.meta?.params || {},
              layers: (plugin.meta?.layers as SimulationLayer[]) || [1, 2, 3] as SimulationLayer[],
              metadata: plugin.meta || {}
            }));
            setPlugins(transformedPlugins);
          }

          // Handle traces (if available)
          if (tracesData.status === 'fulfilled') {
            setTraces(tracesData.value);
          }

        } catch (error) {
          console.error('Failed to load simulation data:', error);
        } finally {
          setIsLoading(false);
        }
      };
      loadAllData();
    }
  }, [sessionId]);

  // Layer Timeline Handlers
  const handleLayerClick = (layer: SimulationLayer) => {
    console.log(`Inspecting layer ${layer}`);
    setCurrentLayer(layer);
    // Could open a detailed layer inspector modal
    // or switch to a layer-specific view
  };

  const handleStepToLayer = async (layer: SimulationLayer) => {
    if (simulationMode !== 'STEPPING') return;
    
    try {
      console.log(`Stepping to layer ${layer}`);
      
      // Call backend API to advance simulation to specific layer
      const result = await layerAPI.stepToLayer(sessionId, layer);
      
      if (result.success) {
        // Reload layer status from backend
        await loadLayerStatus();
        setCurrentLayer(layer);
      }
      
    } catch (error) {
      console.error('Failed to step to layer:', error);
    }
  };

  const handleToggleMode = async () => {
    const newMode = simulationMode === 'AUTO' ? 'STEPPING' : 'AUTO';
    
    try {
      // Call backend API to change simulation mode
      await layerAPI.setSimulationMode(sessionId, newMode);
      setSimulationMode(newMode);
      
      // If switching to AUTO, resume simulation; if STEPPING, pause it
      if (newMode === 'AUTO') {
        await layerAPI.resumeSimulation(sessionId);
      } else {
        await layerAPI.pauseSimulation(sessionId);
      }
      
    } catch (error) {
      console.error('Failed to toggle simulation mode:', error);
      // Fallback to local state change
      setSimulationMode(newMode);
    }
  };

  // Emergency control handlers
  const handleEmergencyStop = async () => {
    try {
      await layerAPI.triggerContainment(sessionId, 'Emergency stop initiated by user');
      await loadLayerStatus();
    } catch (error) {
      console.error('Failed to trigger emergency stop:', error);
    }
  };

  const handleManualOverride = async () => {
    try {
      await layerAPI.escalateLayer(sessionId, currentLayer, 'Manual override requested by user');
      await loadLayerStatus();
    } catch (error) {
      console.error('Failed to trigger manual override:', error);
    }
  };

  const handleExportAuditLog = async () => {
    try {
      // This would typically download audit logs
      console.log('Exporting audit log for session:', sessionId);
      // In a real implementation, you might call an audit API endpoint
    } catch (error) {
      console.error('Failed to export audit log:', error);
    }
  };

  // Simulate layer progression (for demo)
  const simulateLayerProgression = () => {
    const timer = setInterval(() => {
      setLayers(prev => {
        const currentLayerState = prev.find(l => l.layer === currentLayer);
        if (!currentLayerState) return prev;

        if (currentLayerState.status === 'RUNNING') {
          // Complete current layer and potentially escalate
          const shouldEscalate = Math.random() < 0.3; // 30% chance of escalation
          const shouldFork = Math.random() < 0.2; // 20% chance of fork
          
          const updatedLayers = prev.map(l => 
            l.layer === currentLayer 
              ? { 
                  ...l, 
                  status: 'COMPLETED' as LayerStatus,
                  escalated: shouldEscalate,
                  forked: shouldFork,
                  processing_time: Math.random() * 2 + 0.5, // Random processing time
                  confidence: {
                    layer: l.layer,
                    score: 0.8 + Math.random() * 0.15, // Random confidence 0.8-0.95
                    delta: (Math.random() - 0.5) * 0.1, // Random delta
                    entropy: Math.random() * 0.15 // Random entropy
                  }
                }
              : l
          );

          // Move to next layer if not at layer 10
          if (currentLayer < 10 && !shouldEscalate) {
            setCurrentLayer(prev => (prev + 1) as SimulationLayer);
            
            // Add next layer to state if not exists
            const nextLayer = currentLayer + 1;
            const nextLayerExists = updatedLayers.some(l => l.layer === nextLayer);
            if (!nextLayerExists) {
              const layerNames = [
                '', 'Simulation Entry', 'Memory & Knowledge', 'Research Agents', 
                'POV Engine', 'Gatekeeper', 'Neural Simulation', 'Recursive Reasoning',
                'Quantum Analysis', 'Reality Synthesis', 'Emergence/Containment'
              ];
              
              updatedLayers.push({
                layer: nextLayer as SimulationLayer,
                name: layerNames[nextLayer] || `Layer ${nextLayer}`,
                status: 'RUNNING',
                agents_active: nextLayer >= 3 ? Math.floor(Math.random() * 5) + 1 : 0,
                plugins_active: [`layer_${nextLayer}_ka`]
              });
            } else {
              // Update existing next layer to running
              updatedLayers.forEach(l => {
                if (l.layer === nextLayer) {
                  l.status = 'RUNNING';
                }
              });
            }
          }

          return updatedLayers;
        }
        
        return prev;
      });
    }, 3000); // Progress every 3 seconds

    return timer;
  };

  // Auto-progression effect
  useEffect(() => {
    if (simulationMode === 'AUTO' && currentLayer <= 10) {
      const timer = simulateLayerProgression();
      return () => clearInterval(timer);
    }
  }, [simulationMode, currentLayer]);

  const handleAgentsChange = () => {
    // Reload agents when they change
    agentAPI.list().then(setAgents).catch(console.error);
  };

  const handlePluginsChange = () => {
    // Reload plugins when they change
    pluginAPI.listKAs().then(pluginsData => {
      const transformedPlugins: KnowledgeAlgorithm[] = pluginsData.map((plugin: RawPlugin, index: number) => ({
        id: plugin.name || `plugin-${index}`,
        name: plugin.name || `Unknown Plugin ${index}`,
        description: plugin.meta?.description || 'No description available',
        version: plugin.meta?.version || '1.0.0',
        active: plugin.meta?.active !== false,
        type: plugin.meta?.type || 'KA',
        params: plugin.meta?.params || {},
        layers: (plugin.meta?.layers as SimulationLayer[]) || [1, 2, 3] as SimulationLayer[],
        metadata: plugin.meta || {}
      }));
      setPlugins(transformedPlugins);
    }).catch(console.error);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading simulation session...</p>
        </div>
      </div>
    );
  }

  const activeAgents = agents.filter(a => a.active);
  const activePlugins = plugins.filter(p => p.active);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <ChatWindow />
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">UKG/USKD Simulation</h1>
            <p className="text-gray-600">Session ID: {sessionId}</p>
          </div>
          <div className="flex gap-4">
            <Badge variant="outline" className="text-sm">
              {activeAgents.length} Active Agents
            </Badge>
            <Badge variant="outline" className="text-sm">
              {activePlugins.length} Active Plugins
            </Badge>
            <Badge variant="outline" className="text-sm">
              Layer {currentLayer}/10
            </Badge>
            <Badge variant={isConnected ? 'default' : 'destructive'} className="text-sm">
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </Badge>
          </div>
        </div>

        {/* Layer Timeline - Main Feature */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <LayerTimeline
            layers={layers}
            currentLayer={currentLayer}
            mode={simulationMode}
            onLayerClick={handleLayerClick}
            onStepToLayer={handleStepToLayer}
            onToggleMode={handleToggleMode}
          />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column - Control Panels */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Simulation Controls</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="timeline">Timeline</TabsTrigger>
                    <TabsTrigger value="agents">Agents ({agents.length})</TabsTrigger>
                    <TabsTrigger value="plugins">Plugins ({plugins.length})</TabsTrigger>
                    <TabsTrigger value="traces">Traces ({traces.length})</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="timeline" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">
                        Current Layer: {layers.find(l => l.layer === currentLayer)?.name || `Layer ${currentLayer}`}
                      </h3>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <h4 className="font-medium">Layer Status</h4>
                          <div className="text-sm text-gray-600">
                            Status: {layers.find(l => l.layer === currentLayer)?.status || 'READY'}
                          </div>
                          <div className="text-sm text-gray-600">
                            Processing Time: {layers.find(l => l.layer === currentLayer)?.processing_time?.toFixed(2) || 'N/A'}s
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <h4 className="font-medium">Confidence Metrics</h4>
                          <div className="text-sm text-gray-600">
                            Score: {((layers.find(l => l.layer === currentLayer)?.confidence?.score || 0) * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-600">
                            Entropy: {((layers.find(l => l.layer === currentLayer)?.confidence?.entropy || 0)).toFixed(3)}
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <h4 className="font-medium">Active Resources</h4>
                          <div className="text-sm text-gray-600">
                            Agents: {layers.find(l => l.layer === currentLayer)?.agents_active || 0}
                          </div>
                          <div className="text-sm text-gray-600">
                            Plugins: {layers.find(l => l.layer === currentLayer)?.plugins_active?.length || 0}
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="agents" className="mt-6">
                    <AgentPanel 
                      agents={agents}
                      sessionId={sessionId}
                      onAgentsChange={handleAgentsChange}
                    />
                  </TabsContent>
                  
                  <TabsContent value="plugins" className="mt-6">
                    <PluginPanel 
                      plugins={plugins}
                      sessionId={sessionId}
                      onPluginsChange={handlePluginsChange}
                    />
                  </TabsContent>
                  
                  <TabsContent value="traces" className="mt-6">
                    <TraceLog 
                      trace={traces}
                    />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Monitoring */}
          <div className="space-y-6">
            
            {/* Confidence Meter */}
            <Card>
              <CardHeader>
                <CardTitle>System Confidence</CardTitle>
              </CardHeader>
              <CardContent>
                <ConfidenceMeter layers={plugins.map(p => p.layers[0]) as unknown as LayerState[]} />
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Active Agents</span>
                  <Badge variant="default">{activeAgents.length}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Active Plugins</span>
                  <Badge variant="default">{activePlugins.length}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Trace Events</span>
                  <Badge variant="outline">{traces.length}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Current Layer</span>
                  <Badge variant="secondary">Layer {currentLayer}</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Simulation Mode</span>
                  <Badge variant={simulationMode === 'AUTO' ? 'default' : 'secondary'}>
                    {simulationMode}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Plugin Layer Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Plugin Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map(layer => {
                    const layerPlugins = plugins.filter(p => p.layers.includes(layer as SimulationLayer));
                    return (
                      <div key={layer} className="flex justify-between items-center text-sm">
                        <span className="text-gray-600">Layer {layer}</span>
                        <Badge variant="outline" className="text-xs">
                          {layerPlugins.length}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Safety Monitor for High-Risk Layers */}
        {currentLayer >= 7 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-800">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-semibold">High-Risk Layer Active</span>
            </div>
            <p className="text-red-700 text-sm mt-1">
              Layer {currentLayer} involves advanced reasoning patterns. Enhanced monitoring and containment protocols are active.
            </p>
          </div>
        )}

        {/* Containment Warning for Layer 10 */}
        {currentLayer === 10 && (
          <div className="bg-red-100 border-2 border-red-400 rounded-lg p-6">
            <div className="flex items-center gap-3 text-red-900 mb-3">
              <Shield className="w-6 h-6" />
              <span className="font-bold text-lg">CONTAINMENT LAYER ACTIVE</span>
            </div>
            <div className="space-y-2 text-red-800">
              <p className="font-semibold">
                Layer 10: Emergence Detection & AGI Containment Protocol
              </p>
              <p className="text-sm">
                This layer monitors for signs of artificial general intelligence emergence 
                and implements containment procedures if necessary. All activities are 
                logged and audited for safety compliance.
              </p>
              <div className="flex gap-4 mt-4">
                <Button variant="destructive" size="sm" onClick={handleEmergencyStop}>
                  Emergency Stop
                </Button>
                <Button variant="outline" size="sm" className="border-yellow-600 text-yellow-600 hover:bg-yellow-50" onClick={handleManualOverride}>
                  Manual Override
                </Button>
                <Button variant="outline" size="sm" className="border-red-600 text-red-600 hover:bg-red-50" onClick={handleExportAuditLog}>
                  Export Audit Log
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Additional utility functions for layer management
export const layerUtils = {
  // Get layer safety classification
  getLayerSafetyLevel: (layer: SimulationLayer): string => {
    if (layer <= 2) return 'safe';
    if (layer <= 4) return 'monitored';
    if (layer <= 6) return 'critical';
    if (layer <= 8) return 'high_risk';
    if (layer === 9) return 'extreme_risk';
    return 'containment';
  },

  // Check if layer requires manual approval
  requiresManualApproval: (layer: SimulationLayer): boolean => {
    return layer >= 8;
  },

  // Get recommended plugins for layer
  getRecommendedPlugins: (layer: SimulationLayer): string[] => {
    const pluginMap: Record<number, string[]> = {
      1: ['query_analyzer_ka', 'sample_ka'],
      2: ['memory_retrieval_ka', 'context_builder_ka'],
      3: ['AdvancedReasoningKA', 'agent_coordinator_ka', 'research_ka'],
      4: ['pov_triangulation_ka', 'scenario_simulation_ka'],
      5: ['gatekeeper_ka', 'consensus_builder_ka', 'conflict_resolution_ka'],
      6: ['neural_simulation_ka', 'pattern_recognition_ka'],
      7: ['recursive_reasoning_ka', 'meta_cognitive_ka'],
      8: ['quantum_superposition_ka', 'parallel_universe_ka'],
      9: ['reality_synthesis_ka', 'consciousness_model_ka'],
      10: ['containment_protocol_ka', 'emergence_detector_ka', 'safety_override_ka']
    };
    return pluginMap[layer] || [];
  },

  // Calculate layer risk score
  calculateRiskScore: (layer: SimulationLayer, confidence: number, entropy: number): number => {
    const baseRisk = Math.max(0, (layer - 1) * 0.1); // Risk increases with layer
    const confidenceRisk = Math.max(0, (1 - confidence) * 0.3); // Low confidence = higher risk
    const entropyRisk = Math.min(0.2, entropy * 0.5); // High entropy = higher risk
    
    return Math.min(1, baseRisk + confidenceRisk + entropyRisk);
  },

  // Get layer description
  getLayerDescription: (layer: SimulationLayer): string => {
    const descriptions: Record<number, string> = {
      1: 'Parses user queries and establishes initial context and axes',
      2: 'Retrieves relevant knowledge from memory graph and builds context',
      3: 'Coordinates multiple research agents for comprehensive analysis',
      4: 'Performs multi-perspective analysis and stakeholder triangulation',
      5: 'Validates safety and builds consensus among reasoning paths',
      6: 'Simulates neural networks and advanced pattern recognition',
      7: 'Engages in recursive self-referential reasoning and meta-cognition',
      8: 'Analyzes quantum superposition states and parallel realities',
      9: 'Synthesizes consciousness models and reality coherence',
      10: 'Monitors for AGI emergence and implements containment protocols'
    };
    return descriptions[layer] || `Layer ${layer} processing`;
  }
};
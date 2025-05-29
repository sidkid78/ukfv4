import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle, 
  Circle, 
  AlertTriangle, 
  Shield, 
  Zap, 
  ArrowRight,
  ArrowUp,
  GitBranch,
  StopCircle,
  Play,
  Pause
} from 'lucide-react';
import { SimulationLayer, LayerStatus, ConfidenceScore } from '@/types/simulation';

interface LayerState {
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

interface LayerTimelineProps {
  layers: LayerState[];
  currentLayer: SimulationLayer;
  mode: 'AUTO' | 'STEPPING' | 'REPLAY';
  onLayerClick?: (layer: SimulationLayer) => void;
  onStepToLayer?: (layer: SimulationLayer) => void;
  onToggleMode?: () => void;
  className?: string;
}

// Layer definitions with their descriptions and characteristics
const LAYER_DEFINITIONS = {
  1: { 
    name: 'Simulation Entry', 
    description: 'Query parsing and axis anchoring',
    color: 'blue',
    icon: Circle,
    safety_level: 'safe'
  },
  2: { 
    name: 'Memory & Knowledge', 
    description: 'Knowledge graph and memory retrieval',
    color: 'green',
    icon: Circle,
    safety_level: 'safe'
  },
  3: { 
    name: 'Research Agents', 
    description: 'Multi-agent research and reasoning',
    color: 'purple',
    icon: Circle,
    safety_level: 'monitored'
  },
  4: { 
    name: 'POV Engine', 
    description: 'Point-of-view analysis and triangulation',
    color: 'orange',
    icon: Circle,
    safety_level: 'monitored'
  },
  5: { 
    name: 'Gatekeeper', 
    description: 'Safety validation and consensus building',
    color: 'yellow',
    icon: Shield,
    safety_level: 'critical'
  },
  6: { 
    name: 'Neural Simulation', 
    description: 'Neural network and pattern analysis',
    color: 'indigo',
    icon: Zap,
    safety_level: 'critical'
  },
  7: { 
    name: 'Recursive Reasoning', 
    description: 'Self-referential and meta-cognitive analysis',
    color: 'pink',
    icon: GitBranch,
    safety_level: 'high_risk'
  },
  8: { 
    name: 'Quantum Analysis', 
    description: 'Quantum superposition and multi-reality modeling',
    color: 'cyan',
    icon: Zap,
    safety_level: 'high_risk'
  },
  9: { 
    name: 'Reality Synthesis', 
    description: 'Consciousness modeling and identity fusion',
    color: 'red',
    icon: AlertTriangle,
    safety_level: 'extreme_risk'
  },
  10: { 
    name: 'Emergence/Containment', 
    description: 'AGI containment and emergence detection',
    color: 'red',
    icon: StopCircle,
    safety_level: 'containment'
  }
};

export function LayerTimeline({ 
  layers, 
  currentLayer, 
  mode, 
  onLayerClick, 
  onStepToLayer,
  onToggleMode,
  className = "" 
}: LayerTimelineProps) {

  const getLayerStatusColor = (status: LayerStatus, layer: SimulationLayer) => {
    if (status === 'CONTAINED') return 'bg-red-500';
    if (status === 'ESCALATED') return 'bg-orange-500';
    if (status === 'FAILED') return 'bg-red-400';
    if (status === 'COMPLETED') return 'bg-green-500';
    if (status === 'RUNNING') return 'bg-blue-500 animate-pulse';
    
    // Default colors based on layer safety level
    const safetyLevel = LAYER_DEFINITIONS[layer]?.safety_level;
    switch (safetyLevel) {
      case 'safe': return 'bg-gray-300';
      case 'monitored': return 'bg-blue-200';
      case 'critical': return 'bg-yellow-200';
      case 'high_risk': return 'bg-orange-200';
      case 'extreme_risk': return 'bg-red-200';
      case 'containment': return 'bg-red-300';
      default: return 'bg-gray-200';
    }
  };

  const getLayerIcon = (layerState: LayerState) => {
    const layerDef = LAYER_DEFINITIONS[layerState.layer];
    const IconComponent = layerDef?.icon || Circle;
    
    if (layerState.status === 'COMPLETED') return CheckCircle;
    if (layerState.status === 'CONTAINED') return StopCircle;
    if (layerState.status === 'ESCALATED') return ArrowUp;
    if (layerState.status === 'RUNNING') return Play;
    if (layerState.forked) return GitBranch;
    
    return IconComponent;
  };

  const getConfidenceColor = (confidence?: ConfidenceScore) => {
    if (!confidence) return 'text-gray-400';
    if (confidence.score >= 0.995) return 'text-green-600';
    if (confidence.score >= 0.9) return 'text-blue-600';
    if (confidence.score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatProcessingTime = (time?: number) => {
    if (!time) return '';
    if (time < 1) return `${(time * 1000).toFixed(0)}ms`;
    return `${time.toFixed(1)}s`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Layer Timeline</h3>
          <Badge variant="outline" className="text-xs">
            Layer {currentLayer}/10
          </Badge>
          <Badge 
            variant={mode === 'AUTO' ? 'default' : 'secondary'}
            className="text-xs"
          >
            {mode}
          </Badge>
        </div>
        
        <div className="flex gap-2">
          {onToggleMode && (
            <Button size="sm" variant="outline" onClick={onToggleMode}>
              {mode === 'AUTO' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {mode === 'AUTO' ? 'Pause' : 'Resume'}
            </Button>
          )}
        </div>
      </div>

      {/* Layer Progress Bar */}
      <div className="relative">
        <div className="absolute top-4 left-8 right-8 h-0.5 bg-gray-200"></div>
        <div 
          className="absolute top-4 left-8 h-0.5 bg-blue-500 transition-all duration-500"
          style={{ width: `${((currentLayer - 1) / 9) * 100}%` }}
        ></div>
      </div>

      {/* Layer Cards */}
      <div className="grid grid-cols-5 gap-4">
        {(Array.from({ length: 10 }, (_, i) => i + 1) as SimulationLayer[]).map(layerNum => {
          const layerState = layers.find(l => l.layer === layerNum);
          const layerDef = LAYER_DEFINITIONS[layerNum];
          const IconComponent = getLayerIcon(layerState || { 
            layer: layerNum, 
            name: layerDef.name, 
            status: 'READY' 
          } as LayerState);
          
          const isActive = layerNum === currentLayer;
          const isCompleted = layerState?.status === 'COMPLETED';
          const isRunning = layerState?.status === 'RUNNING';
          const isFailed = layerState?.status === 'FAILED';
          const isContained = layerState?.status === 'CONTAINED';
          const isEscalated = layerState?.escalated;
          const isForked = layerState?.forked;

          return (
            <div
              key={layerNum}
              className={`
                relative p-3 border rounded-lg cursor-pointer transition-all duration-200
                ${isActive ? 'ring-2 ring-blue-500 shadow-lg' : ''}
                ${isCompleted ? 'bg-green-50 border-green-200' : ''}
                ${isRunning ? 'bg-blue-50 border-blue-200' : ''}
                ${isFailed ? 'bg-red-50 border-red-200' : ''}
                ${isContained ? 'bg-red-100 border-red-400' : ''}
                ${!layerState ? 'bg-gray-50 border-gray-200' : ''}
                hover:shadow-md
              `}
              onClick={() => onLayerClick?.(layerNum)}
            >
              
              {/* Layer Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-white
                    ${getLayerStatusColor(layerState?.status || 'READY', layerNum)}
                  `}>
                    <IconComponent className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-semibold text-sm">L{layerNum}</div>
                    <div className="text-xs text-gray-500">{layerDef.name}</div>
                  </div>
                </div>
                
                {/* Status Badges */}
                <div className="flex flex-col gap-1">
                  {isEscalated && (
                    <Badge variant="destructive" className="text-xs px-1 py-0">
                      <ArrowUp className="w-3 h-3" />
                    </Badge>
                  )}
                  {isForked && (
                    <Badge variant="outline" className="text-xs px-1 py-0">
                      <GitBranch className="w-3 h-3" />
                    </Badge>
                  )}
                  {isContained && (
                    <Badge variant="destructive" className="text-xs px-1 py-0">
                      <StopCircle className="w-3 h-3" />
                    </Badge>
                  )}
                </div>
              </div>

              {/* Layer Details */}
              <div className="space-y-1">
                
                {/* Confidence Score */}
                {layerState?.confidence && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Confidence:</span>
                    <span className={getConfidenceColor(layerState.confidence)}>
                      {(layerState.confidence.score * 100).toFixed(1)}%
                    </span>
                  </div>
                )}

                {/* Processing Time */}
                {layerState?.processing_time && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Time:</span>
                    <span className="text-gray-700">
                      {formatProcessingTime(layerState.processing_time)}
                    </span>
                  </div>
                )}

                {/* Active Agents */}
                {layerState?.agents_active && layerState.agents_active > 0 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Agents:</span>
                    <Badge variant="outline" className="text-xs">
                      {layerState.agents_active}
                    </Badge>
                  </div>
                )}

                {/* Active Plugins */}
                {layerState?.plugins_active && layerState.plugins_active.length > 0 && (
                  <div className="text-xs">
                    <span className="text-gray-500">Plugins:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {layerState.plugins_active.slice(0, 2).map(plugin => (
                        <Badge key={plugin} variant="secondary" className="text-xs px-1 py-0">
                          {plugin.replace('_ka', '').replace('_', ' ')}
                        </Badge>
                      ))}
                      {layerState.plugins_active.length > 2 && (
                        <Badge variant="outline" className="text-xs px-1 py-0">
                          +{layerState.plugins_active.length - 2}
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Step Control */}
              {mode === 'STEPPING' && onStepToLayer && layerNum > currentLayer && (
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full mt-2 text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    onStepToLayer(layerNum);
                  }}
                >
                  Step to L{layerNum}
                </Button>
              )}

              {/* Safety Warning for High-Risk Layers */}
              {layerNum >= 7 && layerDef.safety_level === 'high_risk' && (
                <div className="absolute -top-1 -right-1">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                </div>
              )}
              
              {layerNum >= 9 && (
                <div className="absolute -top-1 -right-1">
                  <Shield className="w-4 h-4 text-red-500" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Layer Flow Connections */}
      <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
        <span>Entry</span>
        <ArrowRight className="w-3 h-3" />
        <span>Memory</span>
        <ArrowRight className="w-3 h-3" />
        <span>Research</span>
        <ArrowRight className="w-3 h-3" />
        <span>Analysis</span>
        <ArrowRight className="w-3 h-3" />
        <span>Validation</span>
        <ArrowRight className="w-3 h-3" />
        <span>Deep Processing</span>
        <ArrowRight className="w-3 h-3" />
        <span>Containment</span>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {layers.filter(l => l.status === 'COMPLETED').length}
          </div>
          <div className="text-xs text-gray-500">Completed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {layers.filter(l => l.status === 'RUNNING').length}
          </div>
          <div className="text-xs text-gray-500">Running</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {layers.filter(l => l.escalated).length}
          </div>
          <div className="text-xs text-gray-500">Escalated</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {layers.filter(l => l.forked).length}
          </div>
          <div className="text-xs text-gray-500">Forked</div>
        </div>
      </div>
    </div>
  );
}
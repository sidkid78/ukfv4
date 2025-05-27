import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LayerState } from '@/types/simulation';
import { cn } from '@/lib/utils';

interface LayerTimelineProps {
  layers: LayerState[];
  currentLayer: number;
  onLayerClick?: (layerNumber: number) => void;
}

export function LayerTimeline({ layers, currentLayer, onLayerClick }: LayerTimelineProps) {
  const maxLayers = 10;
  
  const getLayerStatus = (layerNumber: number) => {
    const layer = layers.find(l => l.layer === layerNumber);
    if (!layer) return 'PENDING';
    return layer.status;
  };

  const getLayerConfidence = (layerNumber: number) => {
    const layer = layers.find(l => l.layer === layerNumber);
    return layer?.confidence?.score || 0;
  };

  const getStatusColor = (status: string, isActive: boolean) => {
    if (isActive) return 'bg-blue-500 border-blue-600 text-white';
    
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200';
      case 'ESCALATED':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800 hover:bg-yellow-200';
      case 'CONTAINED':
        return 'bg-red-100 border-red-300 text-red-800 hover:bg-red-200';
      case 'RUNNING':
        return 'bg-blue-100 border-blue-300 text-blue-800 animate-pulse';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Simulation Progress</span>
          <span>{layers.length} / {maxLayers} layers</span>
        </div>
        <Progress value={(layers.length / maxLayers) * 100} className="h-2" />
      </div>

      {/* Layer Grid */}
      <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
        {Array.from({ length: maxLayers }, (_, index) => {
          const layerNumber = index + 1;
          const status = getLayerStatus(layerNumber);
          const confidence = getLayerConfidence(layerNumber);
          const isActive = layerNumber === currentLayer;
          const layer = layers.find(l => l.layer === layerNumber);

          return (
            <div
              key={layerNumber}
              className={cn(
                'relative p-3 rounded-lg border-2 transition-all cursor-pointer min-h-[80px] flex flex-col justify-between',
                getStatusColor(status, isActive),
                onLayerClick && 'hover:scale-105'
              )}
              onClick={() => onLayerClick?.(layerNumber)}
            >
              {/* Layer Number */}
              <div className="text-center">
                <div className="font-bold text-lg">L{layerNumber}</div>
                <div className="text-xs opacity-75">
                  {layer?.name || `Layer ${layerNumber}`}
                </div>
              </div>

              {/* Layer Status Indicators */}
              <div className="space-y-1">
                {/* Confidence Bar */}
                {confidence > 0 && (
                  <div className="w-full bg-white/30 rounded-full h-1">
                    <div
                      className="h-1 rounded-full bg-current transition-all"
                      style={{ width: `${confidence * 100}%` }}
                    />
                  </div>
                )}

                {/* Status Badge */}
                <div className="flex justify-center">
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-[10px] px-1 py-0 border-current',
                      status === 'PENDING' && 'opacity-50'
                    )}
                  >
                    {status}
                  </Badge>
                </div>
              </div>

              {/* Special Indicators */}
              {layer?.escalation && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
              )}
              
              {layer?.forked && (
                <div className="absolute -top-1 -left-1 w-3 h-3 bg-purple-500 rounded-full"></div>
              )}

              {status === 'CONTAINED' && (
                <div className="absolute inset-0 border-2 border-red-500 rounded-lg animate-pulse"></div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
          <span>Escalated</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
          <span>Forked</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span>Contained</span>
        </div>
      </div>
    </div>
  );
}

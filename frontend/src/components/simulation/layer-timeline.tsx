'use client';

import React from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import { cn } from '@/lib/utils';

export function LayerTimeline() {
  const { layers, layerCursor, setLayerCursor } = useSimulationStore();

  return (
    <div className="bg-white p-4 rounded-lg border">
      <h3 className="font-medium mb-4">Layer Timeline</h3>
      
      <div className="flex gap-2 overflow-x-auto pb-2">
        {layers.map((layer, index) => (
          <button
            key={layer.layer}
            onClick={() => setLayerCursor(index)}
            className={cn(
              "flex-shrink-0 px-4 py-3 rounded-lg border transition-all",
              "min-w-[120px] text-center",
              {
                "bg-blue-50 border-blue-200 text-blue-900": index === layerCursor,
                "bg-slate-50 border-slate-200 text-slate-700": index !== layerCursor,
                "ring-2 ring-red-400": layer.escalation,
                "ring-2 ring-yellow-400": layer.status === 'CONTAINED',
                "ring-2 ring-purple-400": layer.forked,
              }
            )}
          >
            <div className="font-medium">Layer {layer.layer}</div>
            <div className="text-xs text-slate-500 mt-1">{layer.name}</div>
            <div className="text-xs mt-1">
              <span className={cn(
                "px-2 py-1 rounded-full text-xs font-medium",
                {
                  "bg-green-100 text-green-800": layer.status === 'COMPLETED',
                  "bg-blue-100 text-blue-800": layer.status === 'RUNNING',
                  "bg-slate-100 text-slate-800": layer.status === 'READY',
                  "bg-red-100 text-red-800": layer.status === 'ESCALATED',
                  "bg-yellow-100 text-yellow-800": layer.status === 'CONTAINED',
                }
              )}>
                {layer.status}
              </span>
            </div>
          </button>
        ))} 
      </div>
    </div>
  );
}
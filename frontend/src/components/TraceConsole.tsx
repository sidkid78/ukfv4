import React, { useRef, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TraceStep } from '@/types/simulation';
import { cn } from '@/lib/utils';
import { Download, Search } from 'lucide-react';

interface TraceLogProps {
  trace: TraceStep[];
  autoScroll?: boolean;
  maxHeight?: string;
  showFilters?: boolean;
}

export function TraceLog({ 
  trace, 
  autoScroll = true, 
  maxHeight = 'h-96',
  showFilters = true 
}: TraceLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = React.useState<string>('');
  const [selectedLayers, setSelectedLayers] = React.useState<number[]>([]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [trace, autoScroll]);

  const filteredTrace = trace.filter(step => {
    const matchesFilter = !filter || 
      step.message.toLowerCase().includes(filter.toLowerCase()) ||
      step.layer_name.toLowerCase().includes(filter.toLowerCase());
    
    const matchesLayer = selectedLayers.length === 0 || 
      selectedLayers.includes(step.layer);
    
    return matchesFilter && matchesLayer;
  });

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'layer_entry':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'memory_patch':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'agent_spawn':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'fork_detected':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'escalation':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'containment':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'ai_interaction':
        return 'bg-cyan-100 text-cyan-800 border-cyan-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp: string | Date) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 3 
    });
  };

  const exportTrace = () => {
    const data = JSON.stringify(filteredTrace, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulation-trace-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const uniqueLayers = Array.from(new Set(trace.map(step => step.layer))).sort();

  return (
    <div className="space-y-4">
      {/* Controls */}
      {showFilters && (
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Filter trace messages..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="flex gap-1">
            {uniqueLayers.map(layer => (
              <Badge
                key={layer}
                variant={selectedLayers.includes(layer) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => {
                  setSelectedLayers(prev =>
                    prev.includes(layer)
                      ? prev.filter(l => l !== layer)
                      : [...prev, layer]
                  );
                }}
              >
                L{layer}
              </Badge>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={exportTrace}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      )}

      {/* Trace Display */}
      <div className={cn('border rounded-lg bg-black text-green-400 font-mono text-sm', maxHeight)}>
        <div className="h-full overflow-auto" ref={scrollRef}>
          <div className="p-4 space-y-2">
            {filteredTrace.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                {trace.length === 0 ? 'No trace events yet...' : 'No events match your filter'}
              </div>
            ) : (
              filteredTrace.map((step, index) => (
                <div
                  key={step.id || index}
                  className="group hover:bg-gray-900/50 p-2 rounded transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {/* Timestamp */}
                    <span className="text-gray-400 text-xs font-mono whitespace-nowrap">
                      {formatTimestamp(step.timestamp)}
                    </span>

                    {/* Layer Badge */}
                    <Badge 
                      variant="outline" 
                      className="text-xs whitespace-nowrap bg-blue-900/50 text-blue-300 border-blue-600"
                    >
                      L{step.layer}
                    </Badge>

                    {/* Event Type Badge */}
                    <Badge 
                      className={cn(
                        'text-xs whitespace-nowrap opacity-80',
                        getEventTypeColor(step.event_type)
                      )}
                    >
                      {step.event_type}
                    </Badge>

                    {/* Message */}
                    <div className="flex-1 min-w-0">
                      <div className="text-green-300">{step.message}</div>
                      
                      {/* Layer Name */}
                      <div className="text-gray-500 text-xs mt-1">
                        {step.layer_name}
                      </div>

                      {/* Confidence Score */}
                      {step.confidence && (
                        <div className="text-yellow-400 text-xs mt-1">
                          Confidence: {(step.confidence.score * 100).toFixed(1)}%
                          {step.confidence.delta !== 0 && (
                            <span className={cn(
                              'ml-2',
                              step.confidence.delta > 0 ? 'text-green-400' : 'text-red-400'
                            )}>
                              ({step.confidence.delta > 0 ? '+' : ''}{(step.confidence.delta * 100).toFixed(1)}%)
                            </span>
                          )}
                        </div>
                      )}

                      {/* Expandable Details */}
                      {(step.input_snapshot || step.output_snapshot) && (
                        <details className="mt-2 group-hover:opacity-100 opacity-60 transition-opacity">
                          <summary className="text-gray-400 text-xs cursor-pointer hover:text-gray-300">
                            View details
                          </summary>
                          <div className="mt-2 pl-4 border-l border-gray-600 space-y-2">
                            {step.input_snapshot && Object.keys(step.input_snapshot).length > 0 && (
                              <div>
                                <div className="text-gray-400 text-xs">Input:</div>
                                <pre className="text-gray-300 text-xs overflow-x-auto">
                                  {JSON.stringify(step.input_snapshot, null, 2)}
                                </pre>
                              </div>
                            )}
                            {step.output_snapshot && Object.keys(step.output_snapshot).length > 0 && (
                              <div>
                                <div className="text-gray-400 text-xs">Output:</div>
                                <pre className="text-gray-300 text-xs overflow-x-auto">
                                  {JSON.stringify(step.output_snapshot, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>
          Showing {filteredTrace.length} of {trace.length} events
        </span>
        <span>
          Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
        </span>
      </div>
    </div>
  );
}

// Also export the existing TraceConsole for backward compatibility
export { TraceConsole } from './TraceConsole';

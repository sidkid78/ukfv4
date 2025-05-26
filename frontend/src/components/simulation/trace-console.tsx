'use client';

import React, { useEffect, useRef } from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Trash2, Search } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';

export function TraceConsole() {
  const { trace } = useSimulationStore();
  const consoleRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new traces arrive
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [trace]);

  const handleDownloadTrace = () => {
    const traceData = JSON.stringify(trace, null, 2);
    const blob = new Blob([traceData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulation-trace-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Trace Console</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadTrace}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={consoleRef}
          className="bg-slate-900 text-slate-200 p-4 rounded-lg h-64 overflow-y-auto font-mono text-sm"
        >
          {trace.length > 0 ? (
            trace.map((step) => (
              <div key={step.id} className="mb-2 leading-relaxed">
                <span className="text-blue-400">[L{step.layer}:{step.layer_name}]</span>{' '}
                <span className="text-slate-400">{formatTimestamp(step.timestamp)}</span>{' '}
                <span className="text-green-400">{step.event_type}</span>{' '}
                - {step.message}
                {step.confidence && (
                  <span className="text-yellow-400 ml-2">
                    (conf: {step.confidence.score.toFixed(3)})
                  </span>
                )}
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-center py-8">
              No trace data available. Start a simulation to see live trace output.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
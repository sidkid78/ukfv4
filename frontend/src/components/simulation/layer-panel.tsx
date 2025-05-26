'use client';

import React from 'react';
import { useSimulationStore } from '@/state/useSimulationStore';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TraceConsole } from './trace-console';
import { ConfidenceMeter } from './confidence-meter';
import { ViewPanel } from '@/types/simulation';


export function LayerPanel() {
  const { layers, layerCursor, viewPanel, setViewPanel } = useSimulationStore();
  const currentLayer = layers[layerCursor];

  if (!currentLayer) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-slate-500">No layer selected</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Layer {currentLayer.layer}: {currentLayer.name}</CardTitle>
        <CardDescription>
          Status: {currentLayer.status} • Confidence: {currentLayer.confidence.score.toFixed(3)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={viewPanel} onValueChange={(value) => setViewPanel(value as ViewPanel)}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="TRACE">Trace</TabsTrigger>
            <TabsTrigger value="AGENTS">Agents</TabsTrigger>
            <TabsTrigger value="PERSONAS">Personas</TabsTrigger>
            <TabsTrigger value="FORKS">Forks</TabsTrigger>
            <TabsTrigger value="CONFIDENCE">Confidence</TabsTrigger>
          </TabsList>
          
          <TabsContent value="TRACE" className="mt-4">
            <TraceConsole />
          </TabsContent>
          <TabsContent value="AGENTS" className="mt-4">
            {/* <AgentList /> */}
          </TabsContent>
          <TabsContent value="PERSONAS" className="mt-4">
            {/* <PersonaList /> */}
          </TabsContent>
          <TabsContent value="FORKS" className="mt-4">
            {/* <ForkList /> */}
          </TabsContent>
          <TabsContent value="CONFIDENCE" className="mt-4">
            <ConfidenceMeter />            
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}


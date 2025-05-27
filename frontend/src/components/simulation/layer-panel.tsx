// 'use client';

// import React from 'react';
// import { useSimulationStore } from '@/state/useSimulationStore';
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

// export function LayerPanel() {
//   const { layers, layerCursor, viewPanel, setViewPanel } = useSimulationStore();
//   const currentLayer = layers[layerCursor];

//   if (!currentLayer) {
//     return (
//       <Card>
//         <CardContent className="p-6">
//           <p className="text-slate-500">No layer selected</p>
//         </CardContent>
//       </Card>
//     );
//   }

//   return (
//     <Card>
//       <CardHeader>
//         <CardTitle>Layer {currentLayer.layer}: {currentLayer.name}</CardTitle>
//         <CardDescription>
//           Status: {currentLayer.status} • Confidence: {currentLayer.confidence.score.toFixed(3)}
//         </CardDescription>
//       </CardHeader>
//       <CardContent>
//         <Tabs value={viewPanel} onValueChange={(value) => setViewPanel(value as any)}>
//           <TabsList className="grid w-full grid-cols-5">
//             <TabsTrigger value="TRACE">Trace</TabsTrigger>
//             <TabsTrigger value="AGENTS">Agents</TabsTrigger>
//             <TabsTrigger value="PERSONAS">Personas</TabsTrigger>
//             <TabsTrigger value="FORKS">Forks</TabsTrigger>
//             <TabsTrigger value="CONFIDENCE">Confidence</TabsTrigger>
//           </TabsList>
          
//           <TabsContent value="TRACE" className="mt-4">
//             <div className="space-y-2">
//               <h4 className="font-medium">Trace Steps for Layer {currentLayer.layer}</h4>
//               <div className="max-h-64 overflow-y-auto space-y-2">
//                 {currentLayer.trace.map((step, index) => (
//                   <div key={step.id} className="p-3 bg-slate-50 rounded border text-sm">
//                     <div className="flex justify-between items-start mb-1">
//                       <span className="font-medium text-slate-900">{step.event_type}</span>
//                       <span className="text-xs text-slate-500">{step.timestamp}</span>
//                     </div>
//                     <p className="text-slate-700">{step.message}</p>
//                     {step.confidence && (
//                       <div className="mt-2 text-xs text-slate-600">
//                         Confidence: {step.confidence.score.toFixed(3)}
//                       </div>
//                     )}
//                   </div>
//                 ))}
//               </div>
//             </div>
//           </TabsContent>
          
//           <TabsContent value="AGENTS" className="mt-4">
//             <div className="space-y-2">
//               <h4 className="font-medium">Active Agents</h4>
//               <div className="grid gap-2">
//                 {currentLayer.agents.length > 0 ? (
//                   currentLayer.agents.map((agentId) => (
//                     <div key={agentId} className="p-3 bg-slate-50 rounded border text-sm">
//                       <span className="font-medium">{agentId}</span>
//                     </div>
//                   ))
//                 ) : (
//                   <p className="text-slate-500 text-sm">No agents active in this layer</p>
//                 )}
//               </div>
//             </div>
//           </TabsContent>
          
//           <TabsContent value="PERSONAS" className="mt-4">
//             <div className="space-y-2">
//               <h4 className="font-medium">Persona Reasoning</h4>
//               <div className="space-y-3">
//                 {Object.entries(currentLayer.persona_reasonings).length > 0 ? (
//                   Object.entries(currentLayer.persona_reasonings).map(([persona, reasoning]) => (
//                     <div key={persona} className="p-3 bg-slate-50 rounded border">
//                       <div className="font-medium text-sm text-slate-900 mb-1">{persona}</div>
//                       <p className="text-sm text-slate-700">{reasoning}</p>
//                     </div>
//                   ))
//                 ) : (
//                   <p className="text-slate-500 text-sm">No persona reasoning available</p>
//                 )}
//               </div>
//             </div>
//           </TabsContent>
          
//           <TabsContent value="FORKS" className="mt-4">
//             <div className="space-y-2">
//               <h4 className="font-medium">Fork & Escalation Events</h4>
//               <div className="space-y-2">
//                 {currentLayer.forked && (
//                   <div className="p-3 bg-purple-50 border border-purple-200 rounded">
//                     <div className="flex items-center gap-2">
//                       <div className="w-2 h-2 rounded-full bg-purple-500"></div>
//                       <span className="font-medium text-purple-900">Fork Detected</span>
//                     </div>
//                     <p className="text-sm text-purple-700 mt-1">
//                       Alternative reasoning path created at this layer
//                     </p>
//                   </div>
//                 )}
                
//                 {currentLayer.escalation && (
//                   <div className="p-3 bg-red-50 border border-red-200 rounded">
//                     <div className="flex items-center gap-2">
//                       <div className="w-2 h-2 rounded-full bg-red-500"></div>
//                       <span className="font-medium text-red-900">Escalation Triggered</span>
//                     </div>
//                     <p className="text-sm text-red-700 mt-1">
//                       Layer escalated due to low confidence or detected issues
//                     </p>
//                   </div>
//                 )}
                
//                 {!currentLayer.forked && !currentLayer.escalation && (
//                   <p className="text-slate-500 text-sm">No fork or escalation events</p>
//                 )}
//               </div>
//             </div>
//           </TabsContent>
          
//           <TabsContent value="CONFIDENCE" className="mt-4">
//             <div className="space-y-4">
//               <h4 className="font-medium">Confidence Analysis</h4>
              
//               <div className="space-y-3">
//                 <div>
//                   <div className="flex justify-between items-center mb-2">
//                     <span className="text-sm font-medium">Current Score</span>
//                     <span className="text-sm font-mono">{currentLayer.confidence.score.toFixed(4)}</span>
//                   </div>
//                   <div className="w-full bg-slate-200 rounded-full h-3">
//                     <div
//                       className="confidence-meter h-3 rounded-full transition-all duration-300"
//                       style={{ width: `${Math.max(5, currentLayer.confidence.score * 100)}%` }}
//                     />
//                   </div>
//                 </div>
                
//                 <div className="flex justify-between text-sm">
//                   <span>Delta: <span className="font-mono">{currentLayer.confidence.delta > 0 ? '+' : ''}{currentLayer.confidence.delta.toFixed(4)}</span></span>
//                   {currentLayer.confidence.entropy && (
//                     <span>Entropy: <span className="font-mono">{currentLayer.confidence.entropy.toFixed(4)}</span></span>
//                   )}
//                 </div>
                
//                 <div className="grid grid-cols-3 gap-2 text-xs">
//                   <div className="text-center p-2 bg-red-50 rounded">
//                     <div className="font-medium text-red-900">Low</div>
//                     <div className="text-red-700">&lt; 0.90</div>
//                   </div>
//                   <div className="text-center p-2 bg-yellow-50 rounded">
//                     <div className="font-medium text-yellow-900">Medium</div>
//                     <div className="text-yellow-700">0.90 - 0.995</div>
//                   </div>
//                   <div className="text-center p-2 bg-green-50 rounded">
//                     <div className="font-medium text-green-900">High</div>
//                     <div className="text-green-700">&gt; 0.995</div>
//                   </div>
//                 </div>
//               </div>
//             </div>
//           </TabsContent>
//         </Tabs>
//       </CardContent>
//     </Card>
//   );
// }
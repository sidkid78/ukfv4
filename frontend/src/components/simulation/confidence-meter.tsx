// 'use client';

// import React from 'react';
// import { useSimulationStore } from '@/state/useSimulationStore';
// import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
// import { getConfidenceColor, getConfidenceTextColor } from '@/lib/utils';

// export function ConfidenceMeter() {
//   const { layers, layerCursor } = useSimulationStore();
//   const currentLayer = layers[layerCursor];

//   if (!currentLayer) {
//     return (
//       <Card>
//         <CardHeader>
//           <CardTitle className="text-lg">Confidence Meter</CardTitle>
//         </CardHeader>
//         <CardContent>
//           <p className="text-slate-500 text-sm">No layer data available</p>
//         </CardContent>
//       </Card>
//     );
//   }

//   const confidence = currentLayer.confidence;
//   const percentage = Math.round(confidence.score * 100);

//   return (
//     <Card>
//       <CardHeader>
//         <CardTitle className="text-lg">Confidence Meter</CardTitle>
//       </CardHeader>
//       <CardContent className="space-y-4">
//         {/* Current Layer Confidence */}
//         <div>
//           <div className="flex justify-between items-center mb-2">
//             <span className="text-sm font-medium">Layer {currentLayer.layer}</span>
//             <span className={`text-lg font-bold ${getConfidenceTextColor(confidence.score)}`}>
//               {percentage}%
//             </span>
//           </div>
          
//           <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden">
//             <div
//               className={`h-4 rounded-full transition-all duration-500 ${getConfidenceColor(confidence.score)}`}
//               style={{ width: `${Math.max(2, percentage)}%` }}
//             />
//           </div>
          
//           <div className="flex justify-between text-xs text-slate-500 mt-1">
//             <span>0%</span>
//             <span>50%</span>
//             <span>99.5%</span>
//             <span>100%</span>
//           </div>
//         </div>

//         {/* Confidence Details */}
//         <div className="space-y-2 text-sm">
//           <div className="flex justify-between">
//             <span>Score:</span>
//             <span className="font-mono">{confidence.score.toFixed(4)}</span>
//           </div>
          
//           <div className="flex justify-between">
//             <span>Delta:</span>
//             <span className={`font-mono ${confidence.delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
//               {confidence.delta >= 0 ? '+' : ''}{confidence.delta.toFixed(4)}
//             </span>
//           </div>
          
//           {confidence.entropy !== undefined && (
//             <div className="flex justify-between">
//               <span>Entropy:</span>
//               <span className="font-mono">{confidence.entropy.toFixed(4)}</span>
//             </div>
//           )}
//         </div>

//         {/* Historical Confidence Chart */}
//         <div>
//           <h4 className="text-sm font-medium mb-2">Confidence History</h4>
//           <div className="flex items-end gap-1 h-16">
//             {layers.slice(0, layerCursor + 1).map((layer, index) => (
//               <div
//                 key={layer.layer}
//                 className="flex-1 min-w-[4px] rounded-t transition-all duration-300"
//                 style={{
//                   height: `${Math.max(4, layer.confidence.score * 64)}px`,
//                   backgroundColor: index === layerCursor ? '#3b82f6' : '#cbd5e1',
//                 }}
//                 title={`Layer ${layer.layer}: ${layer.confidence.score.toFixed(3)}`}
//               />
//             ))}
//           </div>
//           <div className="flex justify-between text-xs text-slate-500 mt-1">
//             <span>L1</span>
//             <span>L{Math.min(layers.length, 10)}</span>
//           </div>
//         </div>

//         {/* Status Indicators */}
//         <div className="space-y-1">
//           {confidence.score < 0.9 && (
//             <div className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded">
//               ⚠️ Low confidence detected
//             </div>
//           )}
          
//           {currentLayer.escalation && (
//             <div className="text-xs bg-orange-50 text-orange-700 px-2 py-1 rounded">
//               🔄 Layer escalation active
//             </div>
//           )}
          
//           {currentLayer.forked && (
//             <div className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
//               🌿 Alternative path forked
//             </div>
//           )}
          
//           {currentLayer.status === 'CONTAINED' && (
//             <div className="text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded">
//               🛡️ Containment active
//             </div>
//           )}
//         </div>
//       </CardContent>
//     </Card>
//   );
// }
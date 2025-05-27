// 'use client';

// import React, { useState } from 'react';
// import { useRouter } from 'next/navigation';
// import { Button } from '@/components/ui/button';
// import { Textarea } from '@/components/ui/textarea';
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
// import { Play, Settings, History } from 'lucide-react';
// import { simulationAPI } from '@/lib/api-client';
// import { useSimulationStore } from '@/state/useSimulationStore';
// import { SimulationQuery } from '@/types/simulation';

// export function SimulationEntry() {
//   const router = useRouter();
//   const { setCurrentSession, setLoading, sessions } = useSimulationStore();
//   const [query, setQuery] = useState('');
//   const [isSubmitting, setIsSubmitting] = useState(false);

//   const handleStartSimulation = async () => {
//     if (!query.trim()) return;
    
//     setIsSubmitting(true);
//     setLoading(true);
    
//     try {
//       const simulationQuery: SimulationQuery = {
//         session_id: '',
//         user_query: query.trim(),
//         context: {
//           timestamp: new Date().toISOString(),
//           source: 'web_ui',
//         },
//         axes: Array(13).fill(0), // Default 13D coordinate
//       };
      
//       const response = await simulationAPI.run(simulationQuery);
      
//       setCurrentSession(response.session);
//       router.push(`/simulation/${response.session.id}`);
//     } catch (error) {
//       console.error('Failed to start simulation:', error);
//       // TODO: Add toast notification
//     } finally {
//       setIsSubmitting(false);
//       setLoading(false);
//     }
//   };

//   const handleContinueSession = (sessionId: string) => {
//     router.push(`/simulation/${sessionId}`);
//   };

//   return (
//     <div className="max-w-4xl mx-auto space-y-6">
//       {/* Main Query Entry */}
//       <Card>
//         <CardHeader>
//           <CardTitle className="flex items-center gap-2">
//             <Play className="h-5 w-5" />
//             Start New Simulation
//           </CardTitle>
//           <CardDescription>
//             Enter your query to begin a multi-layered simulation with AGI-safe reasoning
//           </CardDescription>
//         </CardHeader>
//         <CardContent className="space-y-4">
//           <Textarea
//             placeholder="Enter your simulation query here... (e.g., 'Analyze the implications of quantum computing on cybersecurity')"
//             value={query}
//             onChange={(e) => setQuery(e.target.value)}
//             className="min-h-[120px] resize-none"
//             disabled={isSubmitting}
//           />
          
//           <div className="flex justify-between items-center">
//             <div className="text-sm text-slate-500">
//               {query.length} characters
//             </div>
            
//             <div className="flex gap-2">
//               <Button variant="outline" size="sm">
//                 <Settings className="h-4 w-4 mr-2" />
//                 Advanced Options
//               </Button>
              
//               <Button 
//                 onClick={handleStartSimulation}
//                 disabled={!query.trim() || isSubmitting}
//                 size="lg"
//               >
//                 {isSubmitting ? (
//                   <>
//                     <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
//                     Starting...
//                   </>
//                 ) : (
//                   <>
//                     <Play className="h-4 w-4 mr-2" />
//                     Start Simulation
//                   </>
//                 )}
//               </Button>
//             </div>
//           </div>
//         </CardContent>
//       </Card>

//       {/* Recent Sessions */}
//       {sessions.length > 0 && (
//         <Card>
//           <CardHeader>
//             <CardTitle className="flex items-center gap-2">
//               <History className="h-5 w-5" />
//               Recent Sessions
//             </CardTitle>
//             <CardDescription>
//               Continue from a previous simulation session
//             </CardDescription>
//           </CardHeader>
//           <CardContent>
//             <div className="space-y-2">
//               {sessions.slice(0, 5).map((session) => (
//                 <div
//                   key={session.id}
//                   className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 transition-colors"
//                 >
//                   <div className="flex-1 min-w-0">
//                     <p className="font-medium text-sm truncate">
//                       {session.input_query.user_query}
//                     </p>
//                     <p className="text-xs text-slate-500">
//                       {new Date(session.created_at).toLocaleString()} • 
//                       Status: {session.status} • 
//                       Layer {session.current_layer}
//                     </p>
//                   </div>
                  
//                   <Button
//                     variant="outline"
//                     size="sm"
//                     onClick={() => handleContinueSession(session.id)}
//                   >
//                     Continue
//                   </Button>
//                 </div>
//               ))}
//             </div>
//           </CardContent>
//         </Card>
//       )}

//       {/* Quick Start Examples */}
//       <Card>
//         <CardHeader>
//           <CardTitle>Example Queries</CardTitle>
//           <CardDescription>
//             Try these sample queries to explore the simulation system
//           </CardDescription>
//         </CardHeader>
//         <CardContent>
//           <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
//             {[
//               "What are the potential risks and benefits of AGI development?",
//               "Analyze the ethical implications of autonomous weapon systems",
//               "How might climate change affect global food security in 2050?",
//               "Evaluate the societal impact of universal basic income"
//             ].map((example, index) => (
//               <button
//                 key={index}
//                 className="text-left p-3 border rounded-lg hover:bg-slate-50 transition-colors text-sm"
//                 onClick={() => setQuery(example)}
//                 disabled={isSubmitting}
//               >
//                 {example}
//               </button>
//             ))}
//           </div>
//         </CardContent>
//       </Card>
//     </div>
//   );
// }
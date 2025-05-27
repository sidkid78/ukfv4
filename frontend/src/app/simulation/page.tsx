'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useSimulationStore } from '@/state/useSimulationStore';

export default function SimulationIndexPage() {
  const router = useRouter();
  const { sessions } = useSimulationStore();
  const [query, setQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const createNewSession = async () => {
    if (!query.trim()) return;
    
    setIsCreating(true);
    try {
      // Call backend to create session - let backend generate the ID
      const response = await fetch('/api/simulation/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: query,
          context: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Use the backend-provided session ID
      const sessionId = result.session.id;
      
      console.log('Session created:', sessionId);
      
      // Navigate to the new session page with backend-provided ID
      router.push(`/simulation/${sessionId}`);
      
    } catch (error) {
      console.error('Failed to create session:', error);
      alert(`Failed to create session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-slate-900">
            UKG/USKD Simulation Engine
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Advanced multi-layered AGI-safe reasoning system with dynamic agent orchestration, 
            knowledge algorithms, and comprehensive audit trails.
          </p>
        </div>

        {/* Quick Start */}
        <Card>
          <CardHeader>
            <CardTitle>Start New Simulation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4">
                <Input
                  placeholder="Enter your simulation query..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 text-lg"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isCreating) {
                      createNewSession();
                    }
                  }}
                />
                <Button 
                  onClick={createNewSession}
                  disabled={isCreating || !query.trim()}
                  className="min-w-[140px] text-lg px-6"
                  size="lg"
                >
                  {isCreating ? 'Creating...' : 'Start Simulation'}
                </Button>
              </div>
              
              <div className="text-sm text-gray-600">
                <p>Examples:</p>
                <ul className="mt-2 space-y-1">
                  <li>• &quot;Analyze the implications of artificial general intelligence on society&quot;</li>
                  <li>• &quot;What are the ethical considerations in autonomous vehicle decision-making?&quot;</li>
                  <li>• &quot;Evaluate quantum computing&apos;s impact on cryptographic security&quot;</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Features Overview */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Multi-Layer Processing</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                10 specialized reasoning layers with dynamic escalation, 
                confidence scoring, and safety containment protocols.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Agent Orchestration</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Autonomous agent spawning with multi-agent consensus, 
                fork detection, and recursive reasoning capabilities.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Knowledge Algorithms</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Pluggable KA modules with hot-swapping, per-layer mapping, 
                and specialized algorithm capabilities.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Sessions */}
        {sessions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sessions.slice(0, 5).map(session => (
                  <div 
                    key={session.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => router.push(`/simulation/${session.id}`)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {session.input_query.user_query}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(session.created_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      <Badge variant="outline">
                        L{session.current_layer}
                      </Badge>
                      <Badge 
                        variant={session.status === 'COMPLETED' ? 'default' : 'outline'}
                        className="text-xs"
                      >
                        {session.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">10</div>
                <div className="text-gray-600">Simulation Layers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">24</div>
                <div className="text-gray-600">Knowledge Algorithms</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">∞</div>
                <div className="text-gray-600">Agent Capacity</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">100%</div>
                <div className="text-gray-600">System Health</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

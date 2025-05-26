'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
              UKG/USKD
            </h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Multi-Layered Simulation System for AGI-Safe Reasoning
            </p>
          </div>
          
          <div className="space-y-4 max-w-3xl mx-auto">
            <p className="text-lg text-slate-700">
              Advanced simulation engine with layered reasoning, agent orchestration, 
              and comprehensive audit trails for safe AI development.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="font-semibold text-slate-900 mb-2">Layered Simulation</h3>
                <p className="text-slate-600 text-sm">
                  10-layer reasoning engine with dynamic escalation and containment
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="font-semibold text-slate-900 mb-2">Agent Orchestration</h3>
                <p className="text-slate-600 text-sm">
                  Multi-agent coordination with persona-based reasoning
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="font-semibold text-slate-900 mb-2">Audit & Compliance</h3>
                <p className="text-slate-600 text-sm">
                  Complete trace logging with cryptographic certificates
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-12">
            <Button asChild size="lg">
              <Link href="/simulation">
                Start Simulation
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs">
                Documentation
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

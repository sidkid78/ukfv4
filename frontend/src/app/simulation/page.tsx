import { SimulationEntry } from '@/components/simulation/simulation-entry';

export default function SimulationPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Simulation Center</h1>
          <p className="text-slate-600 mt-2">
            Launch new simulations or continue existing sessions
          </p>
        </div>
        
        <SimulationEntry />
      </div>
    </div>
  );
}

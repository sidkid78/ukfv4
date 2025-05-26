import { SimulationSession } from '@/components/simulation/simulation-session';

interface SimulationSessionPageProps {
  params: Promise<{ sessionId: string }>;
}

export default async function SimulationSessionPage({ 
  params 
}: SimulationSessionPageProps) {
  const { sessionId } = await params;
  
  return (
    <div className="min-h-screen bg-slate-50">
      <SimulationSession sessionId={sessionId} />
    </div>
  );
}